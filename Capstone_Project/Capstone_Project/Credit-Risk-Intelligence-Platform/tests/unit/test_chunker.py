# tests/unit/test_chunker.py
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.retrieval.chunker import DocumentChunker


def test_empty_text_returns_no_chunks():
    chunker = DocumentChunker()
    result = chunker.chunk("", original_name="test.pdf")
    assert result == []


def test_short_text_produces_one_chunk():
    chunker = DocumentChunker()
    text = "Net profit was ₹500 crore. Total assets were ₹10,000 crore."
    result = chunker.chunk(text, original_name="annual_report_2023.pdf")
    assert len(result) >= 1
    assert "annual_report_2023.pdf" in result[0].page_content


def test_metadata_source_is_original_name():
    chunker = DocumentChunker()
    text = "A" * 3000
    result = chunker.chunk(text, original_name="HDFC_2023.pdf")
    for doc in result:
        assert doc.metadata.get("source") == "HDFC_2023.pdf"


def test_chunk_index_assigned():
    chunker = DocumentChunker()
    text = "B" * 5000
    result = chunker.chunk(text, original_name="report.pdf")
    indices = [doc.metadata["chunk_idx"] for doc in result]
    assert indices == list(range(len(result)))


def test_year_extracted_from_filename():
    chunker = DocumentChunker()
    text = "C" * 2000
    result = chunker.chunk(text, original_name="ICICI_Annual_2024.pdf")
    assert result[0].metadata.get("year") == "2024"


def test_contextual_header_in_content():
    chunker = DocumentChunker()
    text = "Net profit for the year was ₹1,200 crore."
    result = chunker.chunk(text, original_name="sbi_report.pdf")
    assert "[Source:" in result[0].page_content
