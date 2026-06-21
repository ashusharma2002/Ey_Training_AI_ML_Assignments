"""
evaluator.py — evaluates RAG quality using RAGAS metrics.

RAGAS scores (all 0.0 → 1.0, higher is better):
  - Faithfulness      : Are all answer claims grounded in the retrieved context?
  - Answer Relevancy  : Does the answer actually address the question?
  - Context Recall    : Did the retriever fetch everything needed to answer?
  - Context Precision : Is the retrieved context focused (low noise)?

Target for FinSight: faithfulness >= 0.85
"""

import sys
from unittest.mock import MagicMock

# Patch broken vertexai import in ragas 0.2.10
sys.modules["langchain_community.chat_models.vertexai"] = MagicMock()
sys.modules["langchain_community.chat_models"] = MagicMock()

from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_core.vectorstores import VectorStoreRetriever

import src.config as cfg


# ─── Ground truth answers (for evaluation) ────────────────────────────────────
GROUND_TRUTHS = [
    "Apple's total revenue in fiscal 2023 was $383.3 billion.",
    "Apple had $29.965 billion in cash and cash equivalents at end of fiscal 2023.",
    "iPhone represented approximately 52% of Apple's total revenue in fiscal 2023.",
    "Apple returned over $77 billion to shareholders in fiscal 2023.",
    "Apple's gross margin was 44.1% in fiscal 2023.",
]


def build_eval_dataset(
    queries: list[str],
    answers: list[str],
    retriever: VectorStoreRetriever,
    ground_truths: list[str] = GROUND_TRUTHS,
) -> EvaluationDataset:
    """Build a RAGAS EvaluationDataset from queries, answers, and ground truths."""
    contexts = [
        [d.page_content for d in retriever.invoke(q)]
        for q in queries
    ]
    samples = [
        SingleTurnSample(
            user_input=q,
            response=a,
            retrieved_contexts=ctx,
            reference=gt,
        )
        for q, a, ctx, gt in zip(queries, answers, contexts, ground_truths)
    ]
    return EvaluationDataset(samples=samples)


def safe_score(val):
    """Handle both single float and list of floats from RAGAS."""
    if isinstance(val, list):
        valid = [v for v in val if v is not None]
        if not valid:
            return 0.0
        val = sum(valid) / len(valid)
    if val is None:
        return 0.0
    return round(float(val), 4)


def run_ragas_evaluation(
    eval_dataset: EvaluationDataset,
    llm: AzureChatOpenAI,
) -> dict:
    """
    Run RAGAS evaluation and return scores.

    Args:
        eval_dataset: Built with build_eval_dataset()
        llm:          Azure OpenAI LLM (same one used for generation)

    Returns:
        Dict with faithfulness, answer_relevancy, context_recall, context_precision scores
    """
    # Azure embeddings for RAGAS semantic scoring
    az_embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=cfg.AZURE_ENDPOINT,
        azure_deployment="text-embedding-ada-002",
        api_key=cfg.AZURE_API_KEY,
        api_version=cfg.AZURE_API_VERSION,
    )

    ragas_llm = LangchainLLMWrapper(llm)
    ragas_emb = LangchainEmbeddingsWrapper(az_embeddings)

    print("⏳ Running RAGAS evaluation...")
    results = evaluate(
        dataset=eval_dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=ragas_llm,
        embeddings=ragas_emb,
    )

    scores = {
        "faithfulness":      safe_score(results["faithfulness"]),
        "answer_relevancy":  safe_score(results["answer_relevancy"]),
        "context_recall":    safe_score(results["context_recall"]),
        "context_precision": safe_score(results["context_precision"]),
    }

    print("\n📊 RAGAS Evaluation Results:")
    for metric, score in scores.items():
        target_met = "✅" if metric == "faithfulness" and score >= 0.85 else "  "
        print(f"   {target_met} {metric:<22}: {score}")

    if scores["faithfulness"] >= 0.85:
        print("\n✅ FinSight target met: faithfulness >= 0.85")
    else:
        print(f"\n⚠️  Below target: faithfulness={scores['faithfulness']} (need >= 0.85)")

    return scores