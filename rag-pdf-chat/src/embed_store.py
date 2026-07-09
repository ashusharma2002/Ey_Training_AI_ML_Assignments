"""
embed_store.py
Handles embedding text via Gemini API, and storing/retrieving vectors in Pinecone.
"""

import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-pdf-chat")

genai.configure(api_key=GEMINI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)

EMBED_DIM = 3072  # dimension of Gemini text-embedding-004


def get_or_create_index():
    existing = [i["name"] for i in pc.list_indexes()]
    if INDEX_NAME not in existing:
        print(f"Creating Pinecone index: {INDEX_NAME}")
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        # wait for index to be ready
        while not pc.describe_index(INDEX_NAME).status["ready"]:
            time.sleep(1)
    return pc.Index(INDEX_NAME)


def embed_text(text: str, task_type: str = "retrieval_document"):
    """
    task_type: "retrieval_document" when embedding chunks to store,
               "retrieval_query" when embedding the user's question.
    """
    result = genai.embed_content(
    model="models/gemini-embedding-001",
    content=text,
    task_type=task_type
    )
    return result["embedding"]


def upsert_chunks(chunks):
    """
    chunks: list of {"id", "source", "page", "text"} from chunk.py
    Embeds each chunk and upserts into Pinecone with metadata.
    """
    index = get_or_create_index()
    vectors = []

    for c in chunks:
        embedding = embed_text(c["text"], task_type="retrieval_document")
        vectors.append({
            "id": c["id"],
            "values": embedding,
            "metadata": {
                "source": c["source"],
                "page": c["page"],
                "text": c["text"]
            }
        })

    # batch upsert (Pinecone recommends batches of ~100)
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)

    print(f"Upserted {len(vectors)} chunks into Pinecone index '{INDEX_NAME}'.")


if __name__ == "__main__":
    # Quick manual test
    from ingest import load_pdfs
    from chunk import chunk_text

    docs = load_pdfs("data/pdfs")
    chunks = chunk_text(docs)
    upsert_chunks(chunks)
