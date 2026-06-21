"""
chunker.py — splits LangChain Documents into smaller chunks.

Why chunking?
  The full document is too large to embed and search efficiently.
  We cut it into overlapping 512-character pieces so each chunk
  is small enough to be semantically focused, but the 64-char
  overlap ensures no fact is lost at a boundary.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

import src.config as cfg


def create_chunks(
    docs: list[Document],
    chunk_size: int = cfg.CHUNK_SIZE,
    chunk_overlap: int = cfg.CHUNK_OVERLAP,
) -> list[Document]:
    """
    Split documents into overlapping chunks.

    Args:
        docs:          List of LangChain Documents to split
        chunk_size:    Max characters per chunk (default 512)
        chunk_overlap: Characters shared between adjacent chunks (default 64)

    Returns:
        List of chunk Documents — same metadata as parent, smaller page_content
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # Priority order: split on blank lines first, then newlines,
        # then sentence endings, then spaces, then characters
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks = splitter.split_documents(docs)

    print(f"✅ Created {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    print(f"   Sample chunk:")
    print(f"   Source : {chunks[0].metadata['source']}")
    print(f"   Content: {chunks[0].page_content[:120]}...")

    return chunks
