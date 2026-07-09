"""
chunk.py
Splits page-level text into smaller overlapping chunks, suitable for embedding.
"""

def chunk_text(documents, chunk_size: int = 1000, overlap: int = 150):
    """
    documents: list of {"source", "page", "text"} from ingest.load_pdfs
    Returns: list of {"id", "source", "page", "text"} chunks

    chunk_size / overlap are measured in characters (simple and dependency-free).
    ~1000 characters is roughly 150-200 tokens for English text.
    """
    chunks = []
    chunk_id = 0

    for doc in documents:
        text = doc["text"]
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            chunk_str = text[start:end]

            chunks.append({
                "id": f"chunk-{chunk_id}",
                "source": doc["source"],
                "page": doc["page"],
                "text": chunk_str
            })
            chunk_id += 1

            # move start forward, keeping some overlap with previous chunk
            start += (chunk_size - overlap)

    print(f"Created {len(chunks)} chunks from {len(documents)} pages.")
    return chunks


if __name__ == "__main__":
    from ingest import load_pdfs

    docs = load_pdfs("data/pdfs")
    chunks = chunk_text(docs)

    for c in chunks[:2]:
        print("\n---")
        print(f"{c['id']} | {c['source']} p{c['page']}")
        print(c["text"][:200])
