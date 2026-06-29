# src/agents/orchestrator.py
# ============================================================
# Orchestrator — coordinates the three agents.
# Fixes:
#   • Risk analysis now uses smart financial sampling
#   • FAISS index cleared on new session (no ghost embeddings)
#   • refresh_intelligence() uses richer context
# ============================================================
from __future__ import annotations
from pathlib import Path
from src.agents.document_agent import DocumentIntelligenceAgent, _extract_financial_sample
from src.agents.recommendation_chat_agent import RecommendationChatAgent
from src.agents.retrieval_agent import RetrievalAgent
from src.models.schemas import (
    AIRecommendations, ChatMessage, DocumentMetadata,
    DocumentSummary, PlatformState, RiskAssessment,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    def __init__(self) -> None:
        self._doc_agent       = DocumentIntelligenceAgent()
        self._retrieval_agent = RetrievalAgent()
        self._chat_agent      = RecommendationChatAgent()

    # ── Document Ingestion ────────────────────────────────────

    def ingest_document(
        self,
        file_path: str | Path,
        metadata:  DocumentMetadata,
        state:     PlatformState,
    ) -> DocumentSummary:
        logger.info("Ingesting: %s", metadata.file_name)
        summary, chunks = self._doc_agent.process(file_path, metadata)

        if chunks:
            self._retrieval_agent.index_documents(chunks)
            state.vector_store_ready = True

        state.summaries[metadata.file_name] = summary
        return summary

    def refresh_intelligence(self, state: PlatformState) -> None:
        """
        Generate combined summary + dynamic questions after all documents processed.
        Uses smart financial sampling for better context quality.
        """
        if not state.summaries:
            return

        logger.info("refresh_intelligence for %d documents.", len(state.summaries))

        # Build context from financial samples (not raw text beginning)
        all_text = "\n\n---\n\n".join(
            f"Document: {name}\n{_extract_financial_sample(s.raw_extracted_text, 2000)}"
            for name, s in state.summaries.items()
        )

        # 1 — Combined summary
        try:
            state.combined_summary = self._chat_agent.generate_combined_summary(
                state.summaries, all_text
            )
            logger.info("Combined summary done. Entity: %s",
                        state.combined_summary.entity_type.value)
        except Exception as exc:  # noqa: BLE001
            logger.error("Combined summary failed: %s", exc)

        # 2 — Dynamic questions
        try:
            risk_score = state.risk_assessment.risk_score if state.risk_assessment else None
            state.suggested_questions = self._chat_agent.generate_questions(
                state.combined_summary,
                list(state.summaries.keys()),
                risk_score,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Question generation failed: %s", exc)

    # ── Risk Assessment ───────────────────────────────────────

    def run_risk_analysis(self, state: PlatformState) -> RiskAssessment | None:
        if not state.summaries:
            logger.warning("No summaries for risk analysis.")
            return None

        # Use smart financial sampling — fixes the cover-letter bug
        combined = "\n\n---\n\n".join(
            f"Document: {name}\n{_extract_financial_sample(s.raw_extracted_text, 3000)}"
            for name, s in state.summaries.items()
        )

        risk = self._chat_agent.assess_risk(combined)
        state.risk_assessment = risk
        logger.info("Risk: %.1f (%s)", risk.risk_score, risk.risk_level.value)

        # Refresh questions with risk context
        if state.combined_summary:
            try:
                state.suggested_questions = self._chat_agent.generate_questions(
                    state.combined_summary,
                    list(state.summaries.keys()),
                    risk.risk_score,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Post-risk question refresh failed: %s", exc)

        return risk

    # ── Recommendations ───────────────────────────────────────

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
        recs = self._chat_agent.generate_recommendations(
            state.risk_assessment, summary_text
        )
        state.recommendations = recs
        return recs

    # ── Chat ──────────────────────────────────────────────────

    def chat(self, question: str, state: PlatformState) -> ChatMessage:
        user_msg = ChatMessage(role="user", content=question)
        state.chat_history.append(user_msg)

        from config.settings import settings
        retrieved = self._retrieval_agent.retrieve(
            question, top_k=settings.RETRIEVER_TOP_K
        )
        response = self._chat_agent.answer_question(question, retrieved)
        state.chat_history.append(response)
        return response

    # ── Status / Reset ────────────────────────────────────────

    @property
    def vector_store_ready(self) -> bool:
        return self._retrieval_agent.is_ready

    def reset(self) -> None:
        """Clear in-memory index AND delete persisted FAISS files."""
        self._retrieval_agent.reset_index(delete_persisted=True)
        logger.info("Orchestrator reset complete.")
