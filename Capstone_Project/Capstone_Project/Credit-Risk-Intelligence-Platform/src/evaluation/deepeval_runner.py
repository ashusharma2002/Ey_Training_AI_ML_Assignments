# src/evaluation/deepeval_runner.py
# ============================================================
# DeepEval Evaluation — backend only, not visible in UI.
# Adds hallucination detection and answer correctness scoring.
#
# SETUP (optional, free tier):
#   pip install deepeval
#   Get free API key at: https://app.confident-ai.com
#   Set DEEPEVAL_API_KEY in .env
#
# Why DeepEval over TruLens:
#   - No server/database setup needed
#   - Hallucination metric specifically designed for RAG
#   - Easy LangChain integration
#   - Free tier covers this project's usage
# ============================================================
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from langchain_core.documents import Document
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

_DEEPEVAL_SCORES_FILE = Path("logs/deepeval_scores.jsonl")


def evaluate_hallucination(
    question:       str,
    answer:         str,
    retrieved_docs: list[Document],
) -> dict | None:
    """
    Run DeepEval hallucination check on a RAG response.

    Returns hallucination score (0-1, higher = more hallucinated)
    and a flag indicating if the answer is grounded in context.
    """
    if not settings.EVALUATION_ENABLED:
        return None

    try:
        from deepeval import evaluate as dv_evaluate
        from deepeval.test_case import LLMTestCase
        from deepeval.metrics import HallucinationMetric

        if settings.DEEPEVAL_API_KEY:
            import os
            os.environ["DEEPEVAL_API_KEY"] = settings.DEEPEVAL_API_KEY

        context = [doc.page_content for doc in retrieved_docs if doc.page_content.strip()]
        if not context:
            return None

        test_case = LLMTestCase(
            input=question,
            actual_output=answer,
            context=context,
        )

        metric = HallucinationMetric(threshold=0.5)
        metric.measure(test_case)

        scores = {
            "timestamp":          datetime.now(timezone.utc).isoformat(),
            "question":           question[:100],
            "hallucination_score": round(metric.score, 3),
            "is_grounded":        metric.score < 0.5,
            "reason":             metric.reason or "",
        }

        _append_deepeval_score(scores)
        logger.info(
            "DeepEval hallucination: %.3f (%s)",
            metric.score,
            "GROUNDED" if scores["is_grounded"] else "HALLUCINATED",
        )
        return scores

    except ImportError:
        logger.warning(
            "DeepEval not installed. Run: pip install deepeval\n"
            "Get free API key at: https://app.confident-ai.com\n"
            "Set DEEPEVAL_API_KEY and EVALUATION_ENABLED=true in .env"
        )
        return None
    except Exception as exc:
        logger.warning("DeepEval evaluation failed: %s", exc)
        return None


def _append_deepeval_score(scores: dict) -> None:
    try:
        _DEEPEVAL_SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _DEEPEVAL_SCORES_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(scores) + "\n")
    except Exception as exc:
        logger.warning("Could not write DeepEval scores: %s", exc)
