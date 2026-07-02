# src/orchestrator/orchestrator.py
# ============================================================
# Orchestrator — coordinates the three agents.
# Manages the full pipeline: ingest → analyse → chat → plan.
# ============================================================
from __future__ import annotations
import math
from pathlib import Path
from src.agents.document_agent import DocumentIntelligenceAgent
from src.agents.chat_agent import ChatAgent
from src.agents.retrieval_agent import RetrievalAgent
from src.models.schemas import (
    AIRecommendations, ChatMessage, DocumentMetadata,
    DocumentSummary, PlatformState, RiskAssessment,
    RetirementInput, RetirementResult,
)
from src.retrieval.sampling import extract_financial_sample
from src.utils.logger import get_logger

# LangSmith tracing — @traceable creates named spans in LangSmith
# showing inputs, outputs, time, and errors for each step.
# Works as no-op when LANGCHAIN_API_KEY is not set.
try:
    from langsmith import traceable as _traceable
    _TRACING = True
except ImportError:
    _TRACING = False
    def _traceable(**kwargs):
        def decorator(func): return func
        return decorator

logger = get_logger(__name__)


class AgentOrchestrator:
    def __init__(self) -> None:
        self._doc_agent       = DocumentIntelligenceAgent()
        self._retrieval_agent = RetrievalAgent()
        self._chat_agent      = ChatAgent()

    # ── Document Ingestion ───────────────────────────────────

    def ingest_document(
        self,
        file_path: str | Path,
        metadata:  DocumentMetadata,
        state:     PlatformState,
    ) -> DocumentSummary:
        logger.info("Ingesting: %s", metadata.file_name)
        summary, chunks = self._doc_agent.process(file_path, metadata)

        if chunks:
            success = self._retrieval_agent.index_documents(chunks)
            # BUG FIX: previously set state.vector_store_ready = True
            # unconditionally, even if Pinecone/FAISS indexing silently
            # failed. Chat then showed "ready" with zero indexed content.
            # Now reflects the REAL indexing outcome for this document.
            state.vector_store_ready = success
            if not success:
                logger.error(
                    "Indexing failed for %s: %s",
                    metadata.file_name,
                    self._retrieval_agent.last_error,
                )

        state.summaries[metadata.file_name] = summary
        return summary

    def generate_institution_summary(self, state: PlatformState) -> dict | None:
        """Phase 12 — generate structured executive summary for loan officers."""
        if not state.summaries or state.account_type != "institution":
            return None
        combined_text = "\n\n---\n\n".join(
            f"Document: {name}\n{extract_financial_sample(s.raw_extracted_text, 3000)}"
            for name, s in state.summaries.items()
        )
        loan_dict = {
            "is_loan_application": state.loan_context.is_loan_application,
            "loan_amount": state.loan_context.loan_amount,
            "loan_type": state.loan_context.loan_type.value if state.loan_context.loan_type else None,
            "applicant_type": state.loan_context.applicant_type.value if state.loan_context.applicant_type else None,
        }
        summary = self._chat_agent.generate_institution_summary(combined_text, loan_dict)
        state.institution_summary = summary
        return summary

    @_traceable(name="document_processing", run_type="chain",
                metadata={"component": "orchestrator", "step": "document_processing"})
    def refresh_intelligence(self, state: PlatformState) -> None:
        """
        Generate combined summary + validated dynamic questions.
        Called after all documents are processed.
        """
        if not state.summaries:
            return

        logger.info(
            "refresh_intelligence for %d documents.",
            len(state.summaries),
        )

        all_text = "\n\n---\n\n".join(
            f"Document: {name}\n{extract_financial_sample(s.raw_extracted_text, 2000)}"
            for name, s in state.summaries.items()
        )

        # 1 — Combined summary
        try:
            state.combined_summary = self._chat_agent.generate_combined_summary(
                state.summaries, all_text
            )
            logger.info(
                "Combined summary done. Entity: %s",
                state.combined_summary.entity_type.value,
            )
        except Exception as exc:
            logger.error("Combined summary failed: %s", exc)

        # 2 — Dynamic questions with validation
        if state.combined_summary:
            try:
                risk_score = state.risk_assessment.risk_score if state.risk_assessment else None
                # Build a text sample from actual document content so the
                # question-generation prompt is grounded in real document terms,
                # not just the AI-generated summary (which may use invented phrases)
                raw_sample = "\n\n".join(
                    extract_financial_sample(s.raw_extracted_text, 800)
                    for s in list(state.summaries.values())[:3]
                )
                state.suggested_questions = self._chat_agent.generate_questions(
                    state.combined_summary,
                    list(state.summaries.keys()),
                    risk_score,
                    retrieval_agent=self._retrieval_agent,
                    raw_text_sample=raw_sample,
                )
            except Exception as exc:
                logger.error("Question generation failed: %s", exc)

    # ── Risk Assessment ──────────────────────────────────────

    @_traceable(name="run_risk_analysis", run_type="chain",
                metadata={"component": "orchestrator", "step": "risk_analysis"})
    def run_risk_analysis(self, state: PlatformState) -> RiskAssessment | None:
        if not state.summaries:
            logger.warning("No summaries for risk analysis.")
            return None

        combined = "\n\n---\n\n".join(
            f"Document: {name}\n{extract_financial_sample(s.raw_extracted_text, 3000)}"
            for name, s in state.summaries.items()
        )

        # BUG FIX: entity_type is now passed through so the prompt asks for
        # the RIGHT metrics (CRAR/NPA for a bank instead of meaningless DTI).
        entity_type = (
            state.combined_summary.entity_type
            if state.combined_summary else None
        )
        from src.models.schemas import EntityType
        entity_type = entity_type or EntityType.UNKNOWN

        risk = self._chat_agent.assess_risk(
            combined, entity_type,
            loan_context=state.loan_context,
            account_type=state.account_type,
        )
        state.risk_assessment = risk
        logger.info("Risk: %.1f (%s) — entity: %s", risk.risk_score, risk.risk_level.value, entity_type.value)

        # Refresh questions with risk context
        if state.combined_summary:
            try:
                raw_sample = "\n\n".join(
                    extract_financial_sample(s.raw_extracted_text, 800)
                    for s in list(state.summaries.values())[:3]
                )
                state.suggested_questions = self._chat_agent.generate_questions(
                    state.combined_summary,
                    list(state.summaries.keys()),
                    risk.risk_score,
                    retrieval_agent=self._retrieval_agent,
                    raw_text_sample=raw_sample,
                )
            except Exception as exc:
                logger.warning("Post-risk question refresh failed: %s", exc)

        return risk

    # ── Recommendations ──────────────────────────────────────

    @_traceable(name="run_recommendations", run_type="chain",
                metadata={"component": "orchestrator", "step": "recommendations"})
    def run_recommendations(self, state: PlatformState) -> AIRecommendations:
        if state.risk_assessment is None:
            result = self.run_risk_analysis(state)
            if result is None:
                return AIRecommendations(
                    financial_recommendations=["Upload documents first."]
                )

        summary_text = "\n\n".join(
            f"{name}: {s.executive_summary}\n{s.financial_overview}"
            for name, s in state.summaries.items()
        )

        from src.models.schemas import EntityType
        entity_type = (
            state.combined_summary.entity_type
            if state.combined_summary else EntityType.UNKNOWN
        )

        recs = self._chat_agent.generate_recommendations(
            state.risk_assessment, summary_text, entity_type,
            loan_context=state.loan_context,
            account_type=state.account_type,
        )
        state.recommendations = recs
        return recs

    # ── Retirement Planner ───────────────────────────────────

    def calculate_retirement(
        self,
        inputs: RetirementInput,
        state:  PlatformState,
    ) -> RetirementResult:
        """
        Calculate retirement corpus, SIP requirement, and gap analysis.
        Uses compound interest and inflation-adjusted projections.

        Phase 4 — City-aware: if inputs.city_name is set, monthly
        expenses are split into housing/healthcare/other components and
        each is scaled by that city's cost-of-living multipliers, and
        the inflation rate used is blended with the city's local
        inflation estimate. If no city is selected, behaviour is
        IDENTICAL to before this feature existed (backward compatible).
        """
        logger.info("Calculating retirement plan for age %d → %d", inputs.current_age, inputs.planned_retirement_age)

        years = max(inputs.planned_retirement_age - inputs.current_age, 1)
        post  = max(inputs.life_expectancy - inputs.planned_retirement_age, 1)

        r_annual   = inputs.expected_return  / 100.0
        inf_annual = inputs.inflation_rate   / 100.0
        r_monthly  = r_annual / 12.0

        # ── Phase 4: City-aware expense adjustment ──────────────────
        city_data = None
        adjusted_monthly_expenses = inputs.monthly_expenses
        estimated_housing  = None
        estimated_healthcare = None

        if inputs.city_name:
            from src.retirement.city_data import get_city_data
            city_data = get_city_data(inputs.city_name)

        if city_data:
            # Reasonable household split: ~35% housing, ~15% healthcare,
            # ~50% everything else (food, transport, etc.) — applied only
            # to scale those portions by the city's relative cost, not to
            # replace the user's own reported total expenses wholesale.
            base = inputs.monthly_expenses
            housing_portion    = base * 0.35
            healthcare_portion = base * 0.15
            other_portion      = base * 0.50

            estimated_housing    = housing_portion * city_data.housing_multiplier
            estimated_healthcare = healthcare_portion * city_data.healthcare_multiplier
            other_scaled         = other_portion * (city_data.cost_of_living_index / 100.0)

            adjusted_monthly_expenses = estimated_housing + estimated_healthcare + other_scaled

            # Blend the user's stated inflation assumption with the city's
            # local estimate (50/50) rather than fully overriding it —
            # keeps the user's own judgement in the loop.
            inf_annual = (inf_annual + (city_data.local_inflation_pct / 100.0)) / 2.0
            logger.info(
                "City-adjusted expenses for %s: %.0f -> %.0f (inflation blended to %.2f%%)",
                inputs.city_name, base, adjusted_monthly_expenses, inf_annual * 100,
            )

        # Future monthly expenses (inflation adjusted)
        future_monthly_expenses = (
            adjusted_monthly_expenses
            * inputs.lifestyle_multiplier
            * (1 + inf_annual) ** years
        )

        # Retirement corpus needed
        # Using real return = (1 + nominal) / (1 + inflation) - 1
        real_annual  = (1 + r_annual) / (1 + inf_annual) - 1
        real_monthly = real_annual / 12.0

        if real_monthly > 0:
            corpus_needed = (
                future_monthly_expenses * 12
                * (1 - (1 + real_monthly) ** (-post))
                / real_monthly
            )
        else:
            corpus_needed = future_monthly_expenses * 12 * post

        # Current savings grow to retirement date
        current_savings_fv = inputs.current_savings * (1 + r_annual) ** years

        # Existing SIP grows to retirement date
        if r_monthly > 0 and inputs.current_sip > 0:
            months = years * 12
            existing_sip_fv = inputs.current_sip * (
                ((1 + r_monthly) ** months - 1) / r_monthly
            ) * (1 + r_monthly)
        else:
            existing_sip_fv = inputs.current_sip * years * 12

        total_current_fv = current_savings_fv + existing_sip_fv
        gap = max(corpus_needed - total_current_fv, 0.0)

        # Required additional monthly SIP to close gap
        months = years * 12
        if r_monthly > 0 and gap > 0:
            required_sip = gap * r_monthly / ((1 + r_monthly) ** months - 1)
        elif gap > 0:
            required_sip = gap / months
        else:
            required_sip = 0.0

        total_sip = required_sip + inputs.current_sip

        # Feasibility: what % of surplus income is needed
        monthly_surplus = max(inputs.monthly_income - inputs.monthly_expenses, 1.0)
        feasibility_pct = (total_sip / monthly_surplus) * 100
        is_achievable   = feasibility_pct <= 60.0  # safe if SIP ≤ 60% of surplus

        result = RetirementResult(
            corpus_needed           = round(corpus_needed, 0),
            current_savings_fv      = round(current_savings_fv, 0),
            gap                     = round(gap, 0),
            required_monthly_sip    = round(required_sip, 0),
            total_sip_needed        = round(total_sip, 0),
            years_to_retirement     = years,
            future_monthly_expenses = round(future_monthly_expenses, 0),
            post_retirement_years   = post,
            is_achievable           = is_achievable,
            feasibility_pct         = round(feasibility_pct, 1),
            city_name                     = inputs.city_name if city_data else None,
            city_cost_of_living_index     = city_data.cost_of_living_index if city_data else None,
            city_adjusted_inflation       = round(inf_annual * 100, 2) if city_data else None,
            estimated_housing_expense     = round(estimated_housing, 0) if estimated_housing else None,
            estimated_healthcare_expense  = round(estimated_healthcare, 0) if estimated_healthcare else None,
        )

        # Generate AI-powered plain language advice
        try:
            result.ai_summary = self._chat_agent.generate_retirement_advice(inputs, result)
        except Exception as exc:
            logger.warning("Retirement AI advice failed: %s", exc)
            result.ai_summary = self._default_retirement_advice(result, inputs)

        state.retirement_input  = inputs
        state.retirement_result = result
        return result

    @staticmethod
    def _default_retirement_advice(result: RetirementResult, inputs: RetirementInput) -> str:
        if result.is_achievable:
            return (
                f"✅ Your retirement goal appears achievable! "
                f"You need a total monthly investment of ₹{result.total_sip_needed:,.0f} "
                f"to build a retirement corpus of ₹{result.corpus_needed/1e7:.1f} crore by age {inputs.planned_retirement_age}. "
                f"Start your SIP today — time is your biggest advantage."
            )
        else:
            return (
                f"Your retirement goal needs some adjustments. "
                f"The required monthly SIP of ₹{result.total_sip_needed:,.0f} "
                f"is {result.feasibility_pct:.0f}% of your surplus income. "
                f"Consider extending your retirement age by 2-3 years, reducing expenses, "
                f"or increasing your income to make this plan more manageable."
            )

    # ── Chat ─────────────────────────────────────────────────

    @_traceable(name="chat_question", run_type="chain",
                metadata={"component": "orchestrator", "step": "ai_chat"})
    def chat(self, question: str, state: PlatformState) -> ChatMessage:
        user_msg = ChatMessage(role="user", content=question)
        state.chat_history.append(user_msg)

        retrieved = self._retrieval_agent.retrieve(question)
        response  = self._chat_agent.answer_question(question, retrieved)
        state.chat_history.append(response)
        return response

    # ── Status / Reset ───────────────────────────────────────

    @property
    def vector_store_ready(self) -> bool:
        return self._retrieval_agent.is_ready

    @property
    def vector_store_error(self) -> str | None:
        return self._retrieval_agent.last_error

    def reset(self) -> None:
        """Clear in-memory index AND delete persisted FAISS files."""
        self._retrieval_agent.reset_index(delete_persisted=True)
        logger.info("Orchestrator reset complete.")
