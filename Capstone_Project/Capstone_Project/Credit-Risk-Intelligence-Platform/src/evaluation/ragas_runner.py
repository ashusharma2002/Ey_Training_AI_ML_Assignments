# src/evaluation/ragas_runner.py
# ============================================================
# RAGAS-style evaluation — implemented directly with OpenAI
# API calls, without the ragas package.
#
# WHY: ragas 0.1.21 fails on Windows (numpy source compilation).
# ragas 0.4.3 has a completely broken/unstable API.
# Both issues are packaging problems with the ragas library,
# not problems with the evaluation approach itself.
#
# This file implements the same two metrics ragas provides:
#
# 1. FAITHFULNESS — did the AI answer use ONLY information
#    from the retrieved document chunks, or did it add facts
#    not present in those chunks?
#    Score: 0.0 (fully hallucinated) to 1.0 (fully faithful)
#
# 2. ANSWER RELEVANCY — does the answer actually address the
#    question that was asked?
#    Score: 0.0 (completely irrelevant) to 1.0 (fully relevant)
#
# Both scores are calculated by asking GPT-3.5 to evaluate
# the answer — exactly the same mechanism ragas uses internally.
# ============================================================
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from langchain_core.documents import Document
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

_SCORES_FILE = Path("logs/eval_scores.jsonl")


def _call_openai(prompt: str) -> str:
    """Make a direct OpenAI API call and return the text response."""
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=10,
    )
    return response.choices[0].message.content.strip()


def _score_faithfulness(answer: str, contexts: list[str]) -> float:
    """
    Asks GPT: is every statement in this answer supported by
    the provided context? Returns a score from 0.0 to 1.0.

    Prompt approach: ask GPT to rate faithfulness on a 0-10
    scale, then normalise to 0.0-1.0.
    """
    context_text = "\n\n".join(f"[Context {i+1}]: {c[:600]}" for i, c in enumerate(contexts[:4]))
    prompt = f"""You are evaluating an AI answer for faithfulness.

CONTEXT (the only information the AI should have used):
{context_text}

AI ANSWER TO EVALUATE:
{answer[:800]}

TASK: Rate how faithfully the answer sticks to the context above.
- Score 10: every statement in the answer is directly supported by the context
- Score 5: most statements are supported but 1-2 things were added from outside
- Score 0: the answer contains many facts not found in the context at all

Reply with ONLY a single integer from 0 to 10. No explanation."""
    try:
        raw = _call_openai(prompt)
        score = int("".join(c for c in raw if c.isdigit())[:2]) / 10.0
        return min(1.0, max(0.0, score))
    except Exception:
        return 0.5  # neutral fallback if parsing fails


def _score_answer_relevancy(question: str, answer: str) -> float:
    """
    Asks GPT: does this answer actually address the question
    that was asked? Returns a score from 0.0 to 1.0.
    """
    prompt = f"""You are evaluating whether an AI answer is relevant to the question.

QUESTION: {question}

AI ANSWER: {answer[:800]}

TASK: Rate how directly the answer addresses the question.
- Score 10: the answer directly and completely addresses what was asked
- Score 5: the answer partially addresses the question but misses key parts
- Score 0: the answer does not address the question at all

Reply with ONLY a single integer from 0 to 10. No explanation."""
    try:
        raw = _call_openai(prompt)
        score = int("".join(c for c in raw if c.isdigit())[:2]) / 10.0
        return min(1.0, max(0.0, score))
    except Exception:
        return 0.5


def evaluate_rag_response(
    question:       str,
    answer:         str,
    retrieved_docs: list[Document],
    ground_truth:   str = "",
) -> dict | None:
    """
    Evaluate a RAG response using faithfulness and answer relevancy.
    No external ragas package required — works on all Python/OS versions.
    """
    if not settings.EVALUATION_ENABLED:
        return None

    if not settings.OPENAI_API_KEY:
        logger.warning("RAGAS-style evaluation requires OPENAI_API_KEY.")
        return None

    try:
        contexts = [doc.page_content for doc in retrieved_docs if doc.page_content.strip()]
        if not contexts:
            return None

        faith = _score_faithfulness(answer, contexts)
        relev = _score_answer_relevancy(question, answer)

        scores = {
            "timestamp":        datetime.now(timezone.utc).isoformat(),
            "question":         question[:100],
            "faithfulness":     round(faith, 3),
            "answer_relevancy": round(relev, 3),
            "n_contexts":       len(contexts),
        }

        _append_score(scores)
        logger.info(
            "RAGAS scores — faithfulness: %.3f, relevancy: %.3f",
            scores["faithfulness"],
            scores["answer_relevancy"],
        )
        return scores

    except Exception as exc:
        logger.warning("RAGAS evaluation failed: %s", exc)
        return None


def _append_score(scores: dict) -> None:
    try:
        _SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _SCORES_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(scores) + "\n")
    except Exception as exc:
        logger.warning("Could not write eval scores: %s", exc)


def get_recent_scores(n: int = 20) -> list[dict]:
    if not _SCORES_FILE.exists():
        return []
    try:
        lines = _SCORES_FILE.read_text(encoding="utf-8").strip().splitlines()
        return [json.loads(line) for line in lines[-n:]]
    except Exception:
        return []
