# src/agents/recommendation_chat_agent.py
# ============================================================
# Agent 3 — handles all LLM-based tasks:
#   • Chat Q&A (RAG-grounded)
#   • Risk assessment
#   • Recommendations
#   • Combined multi-document summary
#   • Dynamic question generation
#
# Uses invoke_with_fallback() for Gemini → OpenAI resilience.
# ============================================================
from __future__ import annotations
import json
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from src.llm.llm_factory import invoke_with_fallback
from src.models.schemas import (
    AIRecommendations, ChatMessage, CombinedSummary,
    EntityType, LoanSuggestion, QuestionSet,
    RiskAssessment, RiskLevel,
)
from src.rag.prompt_builder import (
    build_combined_summary_prompt, build_question_generation_prompt,
    build_rag_prompt, build_recommendation_prompt, build_risk_prompt,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

_CHAT_SYS = (
    "You are a Credit Risk Intelligence assistant. "
    "Answer ONLY from the document context provided. "
    "Use markdown: **bold** key figures, bullet points, tables for comparisons. "
    "If information is absent from context, say so — never guess."
)
_RISK_SYS = (
    "You are a senior credit risk officer. "
    "Assess financial health objectively using only the provided data. "
    "Never fabricate or estimate numbers not present in the text."
)
_REC_SYS  = "You are an expert financial counsellor. Give realistic, actionable advice."
_SUM_SYS  = "You are a senior financial analyst writing executive briefings. Be specific with figures."
_QGEN_SYS = "You design targeted financial analysis questions. Never use generic templates."


class RecommendationChatAgent:

    # ── Chat ──────────────────────────────────────────────────

    def answer_question(
        self,
        question:      str,
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
                SystemMessage(content=_CHAT_SYS),
                HumanMessage(content=prompt),
            ])
        except Exception as exc:  # noqa: BLE001
            logger.error("Chat error: %s", exc)
            answer = f"I encountered an error: {exc}. Please check your API keys."
        return ChatMessage(role="assistant", content=answer, sources=sources)

    # ── Combined Summary ──────────────────────────────────────

    def generate_combined_summary(
        self,
        summaries: dict,
        all_text:  str,
    ) -> CombinedSummary:
        logger.info("Combined summary for %d documents.", len(summaries))

        # Build richer context using financial samples from each document's raw text
        from src.agents.document_agent import _extract_financial_sample
        summary_texts = {}
        for name, s in summaries.items():
            # Use financial sample of raw text for better context
            financial_sample = _extract_financial_sample(s.raw_extracted_text, max_chars=3000)
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
                SystemMessage(content=_SUM_SYS),
                HumanMessage(content=prompt),
            ])
            data = json.loads(self._strip_fences(raw))
            et_str = data.get("entity_type", "Unknown")
            try:
                entity_type = EntityType(et_str)
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
        except Exception as exc:  # noqa: BLE001
            logger.error("Combined summary error: %s", exc)
            return CombinedSummary(
                executive_overview = "Combined analysis generation failed. Re-upload documents.",
                documents_covered  = list(summaries.keys()),
            )

    # ── Dynamic Questions ─────────────────────────────────────

    def generate_questions(
        self,
        combined_summary: CombinedSummary,
        document_names:   list[str],
        risk_score:       float | None = None,
    ) -> QuestionSet:
        logger.info("Generating questions for %s", combined_summary.entity_type.value)
        summary_dict = {
            "entity_type":        combined_summary.entity_type.value,
            "executive_overview": combined_summary.executive_overview,
            "financial_position": combined_summary.financial_position,
        }
        prompt = build_question_generation_prompt(summary_dict, document_names, risk_score)
        try:
            raw  = invoke_with_fallback([
                SystemMessage(content=_QGEN_SYS),
                HumanMessage(content=prompt),
            ])
            data = json.loads(self._strip_fences(raw))
            try:
                entity_type = EntityType(data.get("entity_type", combined_summary.entity_type.value))
            except ValueError:
                entity_type = combined_summary.entity_type
            return QuestionSet(
                entity_type       = entity_type,
                document_types    = data.get("document_types", []),
                analyst_questions = data.get("analyst_questions", [])[:5],
                entity_questions  = data.get("entity_questions", [])[:5],
                is_generated      = True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Question generation failed: %s", exc)
            return self._fallback_questions(combined_summary.entity_type)

    # ── Risk Assessment ───────────────────────────────────────

    def assess_risk(self, combined_text: str) -> RiskAssessment:
        logger.info("Risk assessment.")
        prompt = build_risk_prompt(combined_text)
        try:
            raw  = invoke_with_fallback([
                SystemMessage(content=_RISK_SYS),
                HumanMessage(content=prompt),
            ])
            data = json.loads(self._strip_fences(raw))
            try:
                data["risk_level"] = RiskLevel(data.get("risk_level", "Moderate"))
            except ValueError:
                data["risk_level"] = RiskLevel.MODERATE
            return RiskAssessment(**data)
        except Exception as exc:  # noqa: BLE001
            logger.error("Risk assessment error: %s", exc)
            return RiskAssessment(
                risk_score=50.0, risk_level=RiskLevel.MODERATE,
                credit_health="Assessment failed — re-run analysis.",
            )

    # ── Recommendations ───────────────────────────────────────

    def generate_recommendations(
        self,
        risk_assessment: RiskAssessment,
        summary_texts:   str,
    ) -> AIRecommendations:
        logger.info("Generating recommendations.")
        prompt = build_recommendation_prompt(
            risk_assessment.model_dump(mode="json"), summary_texts
        )
        try:
            raw       = invoke_with_fallback([
                SystemMessage(content=_REC_SYS),
                HumanMessage(content=prompt),
            ])
            data      = json.loads(self._strip_fences(raw))
            raw_loans = data.pop("alternative_loan_suggestions", [])
            loans     = [LoanSuggestion(**l) for l in raw_loans if isinstance(l, dict)]
            return AIRecommendations(**data, alternative_loan_suggestions=loans)
        except Exception as exc:  # noqa: BLE001
            logger.error("Recommendations error: %s", exc)
            return AIRecommendations(
                financial_recommendations=[f"Recommendation generation failed: {exc}"],
            )

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _strip_fences(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            parts = text.split("```")
            text  = parts[1] if len(parts) > 1 else text
            if text.startswith("json"):
                text = text[4:]
        return text.strip()

    @staticmethod
    def _fallback_questions(entity_type: EntityType) -> QuestionSet:
        if entity_type == EntityType.COMMERCIAL_BANK:
            aq = [
                "What is the Capital Adequacy Ratio reported?",
                "What is the Gross NPA ratio and how has it changed?",
                "How has Net Interest Income changed year on year?",
                "What are total deposits and advances?",
                "What provisions were made for non-performing assets?",
            ]
            eq = [
                "What was the net profit for the reporting period?",
                "How has the loan book grown compared to last year?",
                "What dividend was declared for shareholders?",
                "What are the key risks identified by management?",
                "How has Return on Assets changed?",
            ]
        elif entity_type in (EntityType.LARGE_CORPORATE, EntityType.SME):
            aq = [
                "What is the debt-to-equity ratio?",
                "Is there sufficient cash flow for debt servicing?",
                "What is the EBITDA margin?",
                "Are there any overdue loans or defaults?",
                "What is the working capital position?",
            ]
            eq = [
                "What is the net profit margin?",
                "How much loan can this entity safely afford?",
                "What are the biggest expense categories?",
                "How has revenue trended over the period?",
                "What improvements would strengthen the credit profile?",
            ]
        else:
            aq = [
                "What is the total income reported in these documents?",
                "What are the main assets and liabilities?",
                "Is there evidence of regular income and stable cash flow?",
                "What is the debt position of this entity?",
                "Are there any financial red flags in the documents?",
            ]
            eq = [
                "What is my current financial health based on these documents?",
                "How much loan am I eligible for?",
                "What are my financial strengths?",
                "What should I improve to get better loan terms?",
                "What does the cash flow analysis show?",
            ]
        return QuestionSet(
            entity_type=entity_type,
            analyst_questions=aq,
            entity_questions=eq,
            is_generated=False,
        )
