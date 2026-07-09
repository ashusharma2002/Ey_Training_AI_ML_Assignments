"""
pipeline.py
Orchestrates the full RAG flow: build index (once) and answer questions (many times).
"""

from ingest import load_pdfs
from text_chunker import chunk_text
from embed_store import upsert_chunks
from retriever import retrieve_chunks
from generator import generate_answer


def build_index(pdf_folder: str = "data/pdfs"):
    """
    Run this once (or whenever your PDFs change) to populate Pinecone.
    """
    docs = load_pdfs(pdf_folder)
    if not docs:
        print("No documents found — nothing to index.")
        return
    chunks = chunk_text(docs)
    upsert_chunks(chunks)


def get_answer(question: str, top_k: int = 3):
    """
    Run this for every user question.
    Returns: (answer_text, list_of_source_strings)
    """
    chunks = retrieve_chunks(question, top_k=top_k)

    if not chunks:
        return "No relevant documents found. Have you run build_index() yet?", []

    answer = generate_answer(question, chunks)
    sources = [f"{c['source']} (page {c['page']}, score {c['score']:.2f})" for c in chunks]

    return answer, sources


if __name__ == "__main__":
    # Step 1: build the index (only needs to run once per set of PDFs)
    build_index()

    # Step 2: ask a test question
    answer, sources = get_answer("What is this document about?")
    print("\nAnswer:", answer)
    print("\nSources:")
    for s in sources:
        print(" -", s)
