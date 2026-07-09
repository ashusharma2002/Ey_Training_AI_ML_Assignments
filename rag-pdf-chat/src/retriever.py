"""
retriever.py
Given a user question, embeds it and retrieves the top-k most relevant chunks from Pinecone.
"""

from embed_store import embed_text, get_or_create_index


def retrieve_chunks(question: str, top_k: int = 3):
    """
    Returns a list of dicts: [{"text", "source", "page", "score"}, ...]
    """
    index = get_or_create_index()
    query_embedding = embed_text(question, task_type="retrieval_query")

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    matches = []
    for match in results["matches"]:
        meta = match["metadata"]
        matches.append({
            "text": meta["text"],
            "source": meta["source"],
            "page": meta["page"],
            "score": match["score"]
        })

    return matches


if __name__ == "__main__":
    q = "What is this document about?"
    results = retrieve_chunks(q)
    for r in results:
        print(f"\n[{r['source']} p{r['page']}] score={r['score']:.3f}")
        print(r["text"][:200])
