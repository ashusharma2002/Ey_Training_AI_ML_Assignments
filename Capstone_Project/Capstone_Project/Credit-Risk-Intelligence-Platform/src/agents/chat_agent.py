# src/agents/chat_agent.py
# ============================================================
# Agent 3 — handles all LLM-based tasks:
#   • Chat Q&A (RAG-grounded, plain language)
#   • Risk assessment
#   • Recommendations
#   • Combined multi-document summary
#   • Dynamic question generation with validation
# ============================================================
from __future__ import annotations
import json
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from src.llm.llm_factory import invoke_with_fallback
from src.models.schemas import (
    AIRecommendations, ChatMessage, CombinedSummary,
    EntityType, KeyMetric, LoanSuggestion, QuestionSet,
    RiskAssessment, RiskLevel, RetirementInput, RetirementResult,
)
from src.prompts.rag_prompts import CHAT_SYSTEM_PROMPT, build_rag_prompt
from src.prompts.summary_prompts import COMBINED_SUMMARY_SYSTEM, build_combined_summary_prompt
from src.prompts.risk_prompts import RISK_SYSTEM_PROMPT, build_risk_prompt
from src.prompts.recommendation_prompts import (
    RECOMMENDATION_SYSTEM_PROMPT, RETIREMENT_SYSTEM_PROMPT,
    build_recommendation_prompt, build_retirement_prompt,
)
from src.prompts.question_prompts import QUESTION_GENERATION_SYSTEM, build_question_generation_prompt
from src.prompts.institution_prompts import INSTITUTION_SUMMARY_SYSTEM, build_institution_summary_prompt
from src.retrieval.sampling import extract_financial_sample
from src.utils.logger import get_logger

try:
    from langsmith import traceable as _traceable
except ImportError:
    def _traceable(**kwargs):
        def decorator(func): return func
        return decorator

logger = get_logger(__name__)


# Default questions used when generation or validation fails completely
_DEFAULT_ANALYST_QUESTIONS = [
    "What is the total income or interest income reported?",
    "What are the total assets and total liabilities?",
    "Is there evidence of consistent positive cash flow?",
    "What is the total debt or outstanding loan amount?",
    "Are there any financial red flags or overdue payments mentioned?",
]
_DEFAULT_ENTITY_QUESTIONS = [
    "What is my overall financial health based on these documents?",
    "What are my biggest financial strengths?",
    "What is the net profit or income reported?",
    "What should I improve to get better credit terms?",
    "What does the balance sheet show about assets and liabilities?",
]


class ChatAgent:

    # ── Chat ─────────────────────────────────────────────────

    @_traceable(name="chat_agent.answer_question", run_type="chain",
                metadata={"component": "chat_agent", "step": "answer_question"})
    def answer_question(
        self,
        question:       str,
        retrieved_docs: list[Document],
    ) -> ChatMessage:
        logger.info("Chat: '%s...'", question[:60])
        prompt  = build_rag_prompt(question, retrieved_docs)
        sources = list({
            d.metadata.get("source", "")
            for d in retrieved_docs
            if d.metadata.get("source")
        })
        try:
            answer = invoke_with_fallback([
                SystemMessage(content=CHAT_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])
        except Exception as exc:
            logger.error("Chat error: %s", exc)
            answer = (
                f"⚠️ I encountered an error: {exc}\n\n"
                "Please check your API keys in `.env` and ensure documents are processed."
            )
        return ChatMessage(role="assistant", content=answer, sources=sources)

    # ── Combined Summary ─────────────────────────────────────

    def generate_combined_summary(
        self,
        summaries: dict,
        all_text:  str,
    ) -> CombinedSummary:
        logger.info("Combined summary for %d documents.", len(summaries))

        summary_texts = {}
        for name, s in summaries.items():
            financial_sample = extract_financial_sample(s.raw_extracted_text, max_chars=3000)
            summary_texts[name] = (
                f"Executive Summary: {s.executive_summary}\n"
                f"Financial Overview: {s.financial_overview}\n"
                f"Income: {s.income_summary}\n"
                f"Assets: {s.assets_summary}\n"
                f"Liabilities: {s.liabilities_summary}\n\n"
                f"Financial Data:\n{financial_sample}"
            )

        prompt = build_combined_summary_prompt(summary_texts, all_text)
        try:
            raw  = invoke_with_fallback([
                SystemMessage(content=COMBINED_SUMMARY_SYSTEM),
                HumanMessage(content=prompt),
            ])
            data = json.loads(self._strip_fences(raw))
            try:
                entity_type = EntityType(data.get("entity_type", "Unknown"))
            except ValueError:
                entity_type = EntityType.UNKNOWN
            return CombinedSummary(
                executive_overview   = data.get("executive_overview", ""),
                financial_position   = data.get("financial_position", ""),
                income_profitability = data.get("income_profitability", ""),
                key_strengths        = data.get("key_strengths", []),
                areas_of_concern     = data.get("areas_of_concern", []),
                overall_assessment   = data.get("overall_assessment", ""),
                entity_type          = entity_type,
                documents_covered    = data.get("documents_covered", list(summaries.keys())),
            )
        except Exception as exc:
            logger.error("Combined summary error: %s", exc)
            return CombinedSummary(
                executive_overview = "Combined analysis generation failed. Re-upload documents.",
                documents_covered  = list(summaries.keys()),
            )

    # ── Dynamic Questions with Validation ────────────────────

    def generate_questions(
        self,
        combined_summary:  CombinedSummary,
        document_names:    list[str],
        risk_score:        float | None       = None,
        retrieval_agent    = None,
        raw_text_sample:   str               = "",   # NEW: actual doc text for grounding
    ) -> QuestionSet:
        """
        Generate context-aware questions grounded in the actual document
        text, then validate every one against the vector store.

        HARD RULE: a question is NEVER returned to the UI unless:
          1. It was retrieved from the vector store (not empty)
          2. The retrieved chunks contain real financial keywords
          3. If a year is mentioned, that year's chunks exist
          4. The fallbacks themselves pass the same checks

        If retrieval_agent is not ready (documents not indexed yet),
        NO questions are returned — the UI shows a "chat not ready" message
        instead of showing unvalidated questions that might not work.
        """
        logger.info("Generating questions for %s", combined_summary.entity_type.value)

        # If the vector store is not ready, return nothing rather than
        # showing unvalidated questions that may not have answers
        if not retrieval_agent or not retrieval_agent.is_ready:
            return QuestionSet(
                entity_type   = combined_summary.entity_type,
                is_generated  = False,
                is_validated  = False,
            )

        summary_dict = {
            "entity_type":        combined_summary.entity_type.value,
            "executive_overview": combined_summary.executive_overview,
            "financial_position": combined_summary.financial_position,
        }
        prompt = build_question_generation_prompt(
            summary_dict, document_names, risk_score, raw_text_sample
        )

        try:
            raw  = invoke_with_fallback([
                SystemMessage(content=QUESTION_GENERATION_SYSTEM),
                HumanMessage(content=prompt),
            ])
            data = json.loads(self._strip_fences(raw))
            try:
                entity_type = EntityType(data.get("entity_type", combined_summary.entity_type.value))
            except ValueError:
                entity_type = combined_summary.entity_type

            analyst_qs = data.get("analyst_questions", [])[:5]
            entity_qs  = data.get("entity_questions",  [])[:5]

        except Exception as exc:
            logger.warning("Question generation failed: %s — trying validated fallbacks", exc)
            # Even the fallback list gets validated so we never show
            # hardcoded questions that don't match the uploaded documents
            analyst_qs = self._validate_questions(
                _DEFAULT_ANALYST_QUESTIONS, [], retrieval_agent
            )
            entity_qs = self._validate_questions(
                _DEFAULT_ENTITY_QUESTIONS, [], retrieval_agent
            )
            return QuestionSet(
                entity_type       = combined_summary.entity_type,
                analyst_questions = analyst_qs,
                entity_questions  = entity_qs,
                is_generated      = True,
                is_validated      = True,
            )

        # ── Validate every AI-generated question against the vector store ──
        # Fallback list is ALSO validated here — a hardcoded fallback like
        # "What is the total interest income?" is useless if the user uploaded
        # a personal salary slip (no interest income field). By validating
        # fallbacks too, only truly answerable questions reach the UI.
        analyst_qs = self._validate_questions(
            analyst_qs, _DEFAULT_ANALYST_QUESTIONS, retrieval_agent
        )
        entity_qs = self._validate_questions(
            entity_qs, _DEFAULT_ENTITY_QUESTIONS, retrieval_agent
        )

        return QuestionSet(
            entity_type       = entity_type if "entity_type" in locals() else combined_summary.entity_type,
            document_types    = data.get("document_types", []) if "data" in locals() else [],
            analyst_questions = analyst_qs,
            entity_questions  = entity_qs,
            is_generated      = True,
            is_validated      = True,   # always True — we only reach here if retrieval_agent was ready
        )

    def _validate_questions(
        self,
        questions:  list[str],
        fallbacks:  list[str],
        retrieval_agent,
    ) -> list[str]:
        """Replace questions that have no retrievable answer with fallbacks."""
        validated = []
        fallback_pool = list(fallbacks)

        for q in questions:
            if retrieval_agent.validate_question(q):
                validated.append(q)
                logger.debug("Question validated: '%s'", q[:60])
            else:
                # Try to find a fallback that works
                replacement = None
                for fb in fallback_pool:
                    if retrieval_agent.validate_question(fb):
                        replacement = fb
                        fallback_pool.remove(fb)
                        break
                if replacement:
                    validated.append(replacement)
                    logger.info(
                        "Question replaced: '%s' -> '%s'",
                        q[:50],
                        replacement[:50],
                    )
                else:
                    # HARD RULE (per product requirement): a recommended
                    # question must NEVER be shown unless the RAG system can
                    # guarantee an answer. Previously this branch fell back
                    # to showing the original unvalidated question anyway —
                    # that directly violated the rule. Now the slot is
                    # simply dropped, so the user only ever sees questions
                    # proven to be answerable, even if that means fewer
                    # than 5 questions are shown.
                    logger.warning(
                        "Dropping unanswerable question (no valid fallback): '%s'",
                        q[:60],
                    )

        return validated[:5]

    # ── Risk Assessment ──────────────────────────────────────

    @_traceable(name="chat_agent.assess_risk", run_type="chain",
                metadata={"component": "chat_agent", "step": "risk_assessment"})
    def assess_risk(
        self,
        combined_text: str,
        entity_type:   EntityType = EntityType.UNKNOWN,
        loan_context  = None,
        account_type: str = "customer",
    ) -> RiskAssessment:
        logger.info("Risk assessment for entity: %s (loan_app=%s, account=%s)",
                    entity_type.value,
                    getattr(loan_context, "is_loan_application", False),
                    account_type)
        prompt = build_risk_prompt(combined_text, entity_type, loan_context, account_type)
        try:
            raw  = invoke_with_fallback([
                SystemMessage(content=RISK_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])
            data = json.loads(self._strip_fences(raw))
            try:
                data["risk_level"] = RiskLevel(data.get("risk_level", "Moderate"))
            except ValueError:
                data["risk_level"] = RiskLevel.MODERATE
            # key_metrics may come back malformed from the LLM — never let
            # a bad metric crash the whole risk assessment.
            raw_metrics = data.pop("key_metrics", []) or []
            metrics = []
            for m in raw_metrics:
                if isinstance(m, dict) and m.get("label") and m.get("value"):
                    metrics.append(KeyMetric(
                        label=str(m["label"]),
                        value=str(m["value"]),
                        is_good=m.get("is_good"),
                    ))
            # Defensive: list-type fields must never be explicit null —
            # drop the key entirely so the schema's default_factory=list
            # applies instead of crashing on a type-mismatch.
            for list_field in ("recommended_banks", "alternative_suggestions", "fraud_indicators"):
                if data.get(list_field) is None:
                    data.pop(list_field, None)
            return RiskAssessment(**data, key_metrics=metrics)
        except Exception as exc:
            logger.error("Risk assessment error: %s", exc)
            return RiskAssessment(
                risk_score=50.0,
                risk_level=RiskLevel.MODERATE,
                credit_health="Assessment failed — re-run analysis.",
            )

    # ── Recommendations ──────────────────────────────────────

    @_traceable(name="chat_agent.generate_recommendations", run_type="chain",
                metadata={"component": "chat_agent", "step": "recommendations"})
    def generate_recommendations(
        self,
        risk_assessment: RiskAssessment,
        summary_texts:   str,
        entity_type:     EntityType = EntityType.UNKNOWN,
        loan_context     = None,
        account_type:    str = "customer",
    ) -> AIRecommendations:
        logger.info("Generating recommendations for entity: %s (account=%s)", entity_type.value, account_type)
        prompt = build_recommendation_prompt(
            risk_assessment.model_dump(mode="json"), summary_texts, entity_type,
            loan_context, account_type,
        )
        try:
            raw       = invoke_with_fallback([
                SystemMessage(content=RECOMMENDATION_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])
            data      = json.loads(self._strip_fences(raw))
            raw_loans = data.pop("alternative_loan_suggestions", [])
            loans     = [LoanSuggestion(**l) for l in raw_loans if isinstance(l, dict)]
            # Defensive: never let an explicit null on a list-type field crash parsing.
            for list_field in ("institution_conditions", "applicant_improvement_tips"):
                if data.get(list_field) is None:
                    data.pop(list_field, None)
            return AIRecommendations(**data, alternative_loan_suggestions=loans)
        except Exception as exc:
            logger.error("Recommendations error: %s", exc)
            return AIRecommendations(
                financial_recommendations=[f"Recommendation generation failed: {exc}"],
            )

    # ── Retirement Planner ───────────────────────────────────

    def generate_institution_summary(
        self,
        combined_text: str,
        loan_context:  dict,
    ) -> dict:
        """Phase 12 — structured executive summary for a loan officer."""
        logger.info("Generating institution executive summary.")
        prompt = build_institution_summary_prompt(combined_text, loan_context)
        try:
            raw  = invoke_with_fallback([
                SystemMessage(content=INSTITUTION_SUMMARY_SYSTEM),
                HumanMessage(content=prompt),
            ])
            return json.loads(self._strip_fences(raw))
        except Exception as exc:
            logger.error("Institution summary generation failed: %s", exc)
            return {
                "customer_age": "Not stated in documents",
                "occupation": "Not stated in documents",
                "monthly_income": "Not stated in documents",
                "annual_income": "Not stated in documents",
                "credit_score": "Not stated in documents",
                "existing_loans": "Not stated in documents",
                "assets": "Not stated in documents",
                "liabilities": "Not stated in documents",
                "investments": "Not stated in documents",
                "requested_loan": loan_context.get("loan_amount", "Not stated"),
                "loan_type": loan_context.get("loan_type", "Not stated"),
                "key_financial_indicators": [f"Summary generation failed: {exc}"],
            }

    def generate_retirement_advice(
        self,
        inputs:      RetirementInput,
        calculation: RetirementResult,
    ) -> str:
        """Generate plain-language retirement planning advice."""
        logger.info("Generating retirement advice.")
        prompt = build_retirement_prompt(
            inputs.model_dump(mode="json"),
            calculation.model_dump(mode="json"),
        )
        try:
            raw  = invoke_with_fallback([
                SystemMessage(content=RETIREMENT_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])
            data = json.loads(self._strip_fences(raw))
            # Return structured result
            summary      = data.get("summary", "")
            action_steps = data.get("action_steps", [])
            encouragement = data.get("encouragement", "")
            full_text = summary
            if action_steps:
                full_text += "\n\n**Your Action Plan:**\n"
                for i, step in enumerate(action_steps, 1):
                    full_text += f"\n{i}. {step}"
            if encouragement:
                full_text += f"\n\n💪 {encouragement}"
            return full_text
        except Exception as exc:
            logger.error("Retirement advice error: %s", exc)
            return "Retirement analysis complete. Please review the numbers above and consult a financial advisor for personalised guidance."

    # ── Helpers ──────────────────────────────────────────────

    @staticmethod
    def _strip_fences(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            parts = text.split("```")
            text  = parts[1] if len(parts) > 1 else text
            if text.startswith("json"):
                text = text[4:]
        return text.strip()

    def _fallback_questions(self, entity_type: EntityType) -> QuestionSet:
        """Safe fallback questions — always generic enough to be answerable."""
        if entity_type == EntityType.COMMERCIAL_BANK:
            aq = [
                "What is the Capital Adequacy Ratio reported?",
                "What is the Gross NPA ratio mentioned?",
                "What is the Net Interest Income for the period?",
                "What are total deposits and advances?",
                "What provisions were made for non-performing assets?",
            ]
            eq = [
                "What was the net profit for the reporting period?",
                "How has the loan book changed compared to last year?",
                "What dividend was declared for shareholders?",
                "What are the key risks identified by management?",
                "What is the Return on Assets reported?",
            ]
        elif entity_type in (EntityType.LARGE_CORPORATE, EntityType.SME):
            aq = [
                "What is the debt-to-equity ratio mentioned?",
                "What is the total revenue or net sales reported?",
                "What is the EBITDA or operating profit?",
                "Are there any overdue loans or defaults mentioned?",
                "What is the working capital position?",
            ]
            eq = [
                "What is the net profit margin reported?",
                "What are the biggest expense categories?",
                "How has revenue changed over the reporting period?",
                "What are the total assets reported?",
                "What improvements would strengthen the financial profile?",
            ]
        else:
            aq = _DEFAULT_ANALYST_QUESTIONS
            eq = _DEFAULT_ENTITY_QUESTIONS
        return QuestionSet(
            entity_type=entity_type,
            analyst_questions=aq,
            entity_questions=eq,
            is_generated=False,
            is_validated=False,
        )
