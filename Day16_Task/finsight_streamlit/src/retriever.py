"""
retriever.py — builds the retriever that finds relevant chunks for a query.

We use MMR (Maximal Marginal Relevance):
  - Fetches fetch_k=10 candidate chunks by similarity
  - Returns the top k=4 that are both relevant AND diverse
  - Prevents returning 4 near-identical chunks about the same sentence
"""

from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStoreRetriever

import src.config as cfg


def build_retriever(vectorstore: FAISS) -> VectorStoreRetriever:
    """
    Create an MMR retriever from the FAISS vectorstore.

    Args:
        vectorstore: Populated FAISS index from embedder.py

    Returns:
        LangChain retriever — call .invoke("your question") to get chunks
    """
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": cfg.RETRIEVER_K,            # final chunks returned
            "fetch_k": cfg.RETRIEVER_FETCH_K, # candidate pool size
            "lambda_mult": cfg.RETRIEVER_LAMBDA,
        },
    )
    print(f"✅ Retriever ready (MMR, k={cfg.RETRIEVER_K})")
    return retriever


def test_retriever(retriever: VectorStoreRetriever, query: str = "What was Apple revenue in 2023?"):
    """Quick smoke-test — prints what the retriever returns for a sample query."""
    print(f"\n🔍 Test query: \"{query}\"")
    results = retriever.invoke(query)
    print(f"   Retrieved {len(results)} chunks:")
    for i, r in enumerate(results):
        print(f"   [{i+1}] {r.metadata['source']}: {r.page_content[:80]}...")
    return results
