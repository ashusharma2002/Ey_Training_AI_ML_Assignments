"""
test_pipeline.py
Basic smoke tests — do not require live API keys.
These check that chunking logic works correctly in isolation.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from text_chunker import chunk_text


def test_chunk_text_basic():
    docs = [{"source": "test.pdf", "page": 1, "text": "a" * 2500}]
    chunks = chunk_text(docs, chunk_size=1000, overlap=150)

    assert len(chunks) > 1
    assert all("id" in c for c in chunks)
    assert all(c["source"] == "test.pdf" for c in chunks)


def test_chunk_text_empty():
    docs = []
    chunks = chunk_text(docs)
    assert chunks == []


def test_chunk_text_short_text():
    docs = [{"source": "short.pdf", "page": 1, "text": "hello world"}]
    chunks = chunk_text(docs, chunk_size=1000, overlap=150)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "hello world"
