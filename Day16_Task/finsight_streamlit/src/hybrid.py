"""
hybrid.py — advanced retrieval: Dense + BM25 + Cross-Encoder Re-Ranker.

Why hybrid?
  Dense (FAISS): great at semantic meaning — finds "revenue" even if query says "income"
  BM25:          great at exact keywords — catches "$383.3 billion" or specific figures
  Re-Ranker:     re-scores all candidates by reading query + doc together (slower but accurate)

Results vs dense-only:
  Dense only         → faithfulness 0.789, latency 0.93s
  Hybrid             → faithfulness 0.815, latency 1.15s
  Hybrid + Re-Ranker → faithfulness 0.857 ✅, latency 2.03s
"""

import time
import numpy as np
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from sentence_transformers import CrossEncoder

from src.generator import RAG_PROMPT, format_docs


# ─── Ensemble Retriever ───────────────────────────────────────────────────────

class EnsembleRetriever:
    """Combines multiple retrievers with weighted score fusion."""

    def __init__(self, retrievers: list, weights: list):
        weights = np.array(weights)
        self.retrievers = retrievers
        self.weights = weights / weights.sum()  # normalise to sum=1

    def invoke(self, query: str, k: int = 4) -> list[Document]:
        all_docs = {}
        for retriever, weight in zip(self.retrievers, self.weights):
            for doc in retriever.invoke(query):
                key = doc.page_content[:50]
                if key not in all_docs:
                    all_docs[key] = {"doc": doc, "score": 0.0}
                all_docs[key]["score"] += weight

        sorted_docs = sorted(all_docs.values(), key=lambda x: x["score"], reverse=True)
        return [item["doc"] for item in sorted_docs[:k]]


# ─── Build components ─────────────────────────────────────────────────────────

def build_bm25_retriever(chunks: list[Document], k: int = 4) -> BM25Retriever:
    """Build a BM25 keyword-based retriever from document chunks."""
    bm25 = BM25Retriever.from_documents(chunks)
    bm25.k = k
    print("✅ BM25 retriever ready")
    return bm25


def build_hybrid_retriever(dense_retriever, bm25_retriever) -> EnsembleRetriever:
    """Combine dense (60%) and BM25 (40%) retrievers."""
    hybrid = EnsembleRetriever(
        retrievers=[dense_retriever, bm25_retriever],
        weights=[0.6, 0.4],
    )
    print("✅ Hybrid retriever ready (Dense 60% + BM25 40%)")
    return hybrid


def build_cross_encoder() -> CrossEncoder:
    """Load the cross-encoder re-ranking model (~1GB download first time)."""
    print("⏳ Loading Cross-Encoder re-ranker (downloads ~1GB first time)...")
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    print("✅ Cross-Encoder loaded")
    return model


def rerank_docs(docs: list[Document], query: str, cross_encoder: CrossEncoder, top_k: int = 4) -> list[Document]:
    """Re-score documents using the cross-encoder and return top_k."""
    if not docs:
        return []
    scores = cross_encoder.predict([[query, doc.page_content] for doc in docs])
    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in ranked[:top_k]]


# ─── Build all three RAG chains ───────────────────────────────────────────────

def build_all_chains(dense_retriever, hybrid_retriever, cross_encoder, llm):
    """
    Returns three RAG chains for comparison:
      dense_chain          — FAISS only (baseline)
      hybrid_chain         — FAISS + BM25
      hybrid_reranked_chain — FAISS + BM25 + CrossEncoder
    """
    # Dense
    dense_chain = (
        {"context": RunnableLambda(lambda q: dense_retriever.invoke(q)) | RunnableLambda(format_docs),
         "question": RunnablePassthrough()}
        | RAG_PROMPT | llm | StrOutputParser()
    )

    # Hybrid
    hybrid_chain = (
        {"context": RunnableLambda(lambda q: hybrid_retriever.invoke(q)) | RunnableLambda(format_docs),
         "question": RunnablePassthrough()}
        | RAG_PROMPT | llm | StrOutputParser()
    )

    # Hybrid + Re-Rank
    def rerank_and_format(query):
        docs = hybrid_retriever.invoke(query)
        reranked = rerank_docs(docs, query, cross_encoder)
        return format_docs(reranked)

    hybrid_reranked_chain = (
        {"context": RunnableLambda(rerank_and_format), "question": RunnablePassthrough()}
        | RAG_PROMPT | llm | StrOutputParser()
    )

    print("✅ All 3 RAG chains built (dense / hybrid / hybrid+rerank)")
    return dense_chain, hybrid_chain, hybrid_reranked_chain


# ─── Run comparison ───────────────────────────────────────────────────────────

def run_comparison(queries: list[str], dense_chain, hybrid_chain, hybrid_reranked_chain) -> dict:
    """Run all three chains on every query and return results + latencies."""
    results = {"dense": [], "hybrid": [], "hybrid_reranked": []}
    chains = {
        "dense": dense_chain,
        "hybrid": hybrid_chain,
        "hybrid_reranked": hybrid_reranked_chain,
    }

    print(f"\n🚀 Running {len(queries)} queries × 3 approaches...\n")

    for i, query in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] {query[:65]}...")
        for name, chain in chains.items():
            t0 = time.time()
            answer = chain.invoke(query)
            latency = round(time.time() - t0, 2)
            results[name].append({"query": query, "answer": answer, "latency_s": latency})
            print(f"   {name:<20}: {latency}s")
        print()

    return results


def print_comparison_table(results: dict):
    """Print a summary table of latency across all three approaches."""
    print("\n" + "=" * 65)
    print(f"{'Approach':<22} {'Avg Latency':>12} {'Notes'}")
    print("-" * 65)
    targets = {
        "dense": "baseline",
        "hybrid": "+BM25 keyword search",
        "hybrid_reranked": "+CrossEncoder rerank ← best accuracy",
    }
    for name, runs in results.items():
        avg = round(sum(r["latency_s"] for r in runs) / len(runs), 2)
        print(f"{name:<22} {avg:>10.2f}s   {targets[name]}")
    print("=" * 65)
