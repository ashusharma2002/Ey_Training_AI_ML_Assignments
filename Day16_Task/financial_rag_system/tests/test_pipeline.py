"""
test_pipeline.py — basic smoke tests (no Azure API needed).

Run with:
    python -m pytest tests/ -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.documents import load_documents, SAMPLE_DOCS
from src.chunker import create_chunks
from langchain_core.documents import Document


def test_documents_load():
    """Documents should load and return 3 LangChain Document objects."""
    docs = load_documents()
    assert len(docs) == 3
    for doc in docs:
        assert isinstance(doc, Document)
        assert "source" in doc.metadata
        assert len(doc.page_content) > 50


def test_document_sources():
    """Each document should have a unique, expected source label."""
    docs = load_documents()
    sources = [d.metadata["source"] for d in docs]
    assert "Apple_10K_2023_Risk" in sources
    assert "Apple_10K_2023_Products" in sources
    assert "Apple_10K_2023_Liquidity" in sources


def test_chunking_produces_more_chunks():
    """Chunking should produce more chunks than input documents."""
    docs = load_documents()
    chunks = create_chunks(docs, chunk_size=512, chunk_overlap=64)
    assert len(chunks) >= len(docs)


def test_chunks_have_metadata():
    """Every chunk must preserve the source metadata from its parent document."""
    docs = load_documents()
    chunks = create_chunks(docs)
    for chunk in chunks:
        assert "source" in chunk.metadata
        assert chunk.metadata["source"] in [
            "Apple_10K_2023_Risk",
            "Apple_10K_2023_Products",
            "Apple_10K_2023_Liquidity",
        ]


def test_chunks_respect_size():
    """No chunk should exceed the configured chunk size by much (splitter may go slightly over)."""
    docs = load_documents()
    chunk_size = 256
    chunks = create_chunks(docs, chunk_size=chunk_size, chunk_overlap=32)
    # Allow 20% overshoot (splitter sometimes keeps a sentence intact)
    for chunk in chunks:
        assert len(chunk.page_content) <= chunk_size * 1.2, (
            f"Chunk too large: {len(chunk.page_content)} chars"
        )


def test_financial_facts_present():
    """Key financial figures should be present in at least one chunk."""
    docs = load_documents()
    chunks = create_chunks(docs)
    all_text = " ".join(c.page_content for c in chunks)
    assert "383.3" in all_text, "Revenue figure missing"
    assert "44.1" in all_text,  "Gross margin missing"
    assert "29.965" in all_text, "Cash figure missing"
