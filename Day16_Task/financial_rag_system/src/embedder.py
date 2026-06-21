"""
embedder.py — converts text chunks into vectors and stores them in FAISS.

How it works:
  1. all-MiniLM-L6-v2 reads each chunk and produces a 384-number vector
     that captures the semantic meaning of the text.
  2. FAISS stores all these vectors in an index optimised for fast
     nearest-neighbour search (cosine similarity).
  3. At query time, the question is also embedded and we find the
     chunks whose vectors are closest to the question vector.
"""

import time
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

import src.config as cfg


def build_embedding_model() -> HuggingFaceEmbeddings:
    """
    Load the HuggingFace sentence embedding model.
    Downloads ~90 MB on first run, cached afterwards.
    """
    print("⏳ Loading HuggingFace embedding model (downloads ~90MB first time)...")
    model = HuggingFaceEmbeddings(
        model_name=cfg.EMBEDDING_MODEL,
        model_kwargs={"device": cfg.EMBEDDING_DEVICE},
        encode_kwargs={
            "normalize_embeddings": True,  # needed for cosine similarity
            "batch_size": 32,
        },
    )
    print(f"✅ Embedding model loaded: {cfg.EMBEDDING_MODEL}")
    return model


def build_vectorstore(
    chunks: list[Document],
    embedding_model: HuggingFaceEmbeddings,
) -> FAISS:
    """
    Embed all chunks and store them in a FAISS index.

    Args:
        chunks:          List of Document chunks from chunker.py
        embedding_model: The loaded HuggingFace embedding model

    Returns:
        FAISS vectorstore ready for similarity search
    """
    print("⏳ Building FAISS index...")
    t0 = time.time()
    vectorstore = FAISS.from_documents(chunks, embedding_model)
    elapsed = time.time() - t0

    print(f"✅ FAISS index built in {elapsed:.2f}s")
    print(f"   Vectors stored : {vectorstore.index.ntotal}")
    print(f"   Vector dimension: {vectorstore.index.d}")
    return vectorstore
