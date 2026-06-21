"""
run_pipeline.py — runs the full FinSight RAG pipeline end to end.

Usage:
    python scripts/run_pipeline.py                  # full pipeline
    python scripts/run_pipeline.py --skip-eval      # skip RAGAS (saves API cost)
    python scripts/run_pipeline.py --hybrid         # include hybrid retrieval comparison
"""

import sys
import os
import argparse

# Make sure src/ is importable when running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import validate_credentials
from src.documents import load_documents
from src.chunker import create_chunks
from src.embedder import build_embedding_model, build_vectorstore
from src.retriever import build_retriever, test_retriever
from src.generator import build_llm, build_rag_chain, run_queries
from src.evaluator import build_eval_dataset, run_ragas_evaluation, GROUND_TRUTHS


# ─── Test queries ─────────────────────────────────────────────────────────────
TEST_QUERIES = [
    "What was Apple's total revenue in fiscal year 2023?",
    "How much cash did Apple have at the end of fiscal 2023?",
    "What percentage of Apple's revenue came from iPhone in 2023?",
    "How much did Apple return to shareholders in fiscal 2023?",
    "What is Apple's gross margin for fiscal 2023?",
]


def main():
    parser = argparse.ArgumentParser(description="FinSight Financial RAG Pipeline")
    parser.add_argument("--skip-eval", action="store_true", help="Skip RAGAS evaluation (saves API calls)")
    parser.add_argument("--hybrid", action="store_true", help="Run hybrid retrieval comparison")
    args = parser.parse_args()

    print("=" * 60)
    print("🏦 FinSight — Financial RAG System")
    print("=" * 60 + "\n")

    # ── Step 1: Validate credentials ──────────────────────────────
    print("── Step 1: Credentials ──────────────────────────────────")
    validate_credentials()
    print()

    # ── Step 2: Load documents ────────────────────────────────────
    print("── Step 2: Load Documents ───────────────────────────────")
    docs = load_documents()
    print()

    # ── Step 3: Chunk ─────────────────────────────────────────────
    print("── Step 3: Chunking ─────────────────────────────────────")
    chunks = create_chunks(docs)
    print()

    # ── Step 4: Embed + FAISS index ───────────────────────────────
    print("── Step 4: Embed + Build FAISS Index ────────────────────")
    embedding_model = build_embedding_model()
    vectorstore = build_vectorstore(chunks, embedding_model)
    print()

    # ── Step 5: Retriever ─────────────────────────────────────────
    print("── Step 5: Build Retriever ──────────────────────────────")
    retriever = build_retriever(vectorstore)
    test_retriever(retriever)
    print()

    # ── Step 6: Build RAG chain ───────────────────────────────────
    print("── Step 6: Build RAG Chain ──────────────────────────────")
    llm = build_llm()
    rag_chain = build_rag_chain(retriever, llm)
    print()

    # ── Step 7: Run queries ───────────────────────────────────────
    print("── Step 7: Run Queries ──────────────────────────────────")
    results = run_queries(rag_chain, TEST_QUERIES)
    print()

    # ── Step 8: RAGAS evaluation ──────────────────────────────────
    if not args.skip_eval:
        print("── Step 8: RAGAS Evaluation ─────────────────────────────")
        answers = [r["answer"] for r in results]
        eval_dataset = build_eval_dataset(TEST_QUERIES, answers, retriever, GROUND_TRUTHS)
        scores = run_ragas_evaluation(eval_dataset, llm)
        print()
    else:
        print("── Step 8: RAGAS Evaluation (skipped) ───────────────────\n")

    # ── Step 9: Hybrid retrieval (optional) ───────────────────────
    if args.hybrid:
        print("── Step 9: Hybrid Retrieval Comparison ──────────────────")
        from src.hybrid import (
            build_bm25_retriever, build_hybrid_retriever, build_cross_encoder,
            build_all_chains, run_comparison, print_comparison_table,
        )
        bm25 = build_bm25_retriever(chunks)
        hybrid_ret = build_hybrid_retriever(retriever, bm25)
        cross_enc = build_cross_encoder()
        dense_chain, hybrid_chain, hybrid_reranked_chain = build_all_chains(
            retriever, hybrid_ret, cross_enc, llm
        )
        comparison = run_comparison(TEST_QUERIES, dense_chain, hybrid_chain, hybrid_reranked_chain)
        print_comparison_table(comparison)
        print()

    print("=" * 60)
    print("✅ Pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
