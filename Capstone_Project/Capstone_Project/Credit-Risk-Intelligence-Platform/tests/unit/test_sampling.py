# tests/unit/test_sampling.py
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.retrieval.sampling import extract_financial_sample


def test_short_text_returned_unchanged():
    text = "Net profit was ₹500 crore."
    result = extract_financial_sample(text, max_chars=8000)
    assert result == text


def test_financial_keywords_prioritised():
    filler  = "This is a notice to shareholders regarding the AGM held last year. " * 50
    finance = "Net profit was ₹44,108 crore. Total assets were ₹2,34,000 crore. " * 20
    text    = filler + finance
    result  = extract_financial_sample(text, max_chars=2000)
    # Financial content should be present
    assert "crore" in result.lower() or "net profit" in result.lower()


def test_max_chars_respected():
    text   = "A" * 50_000
    result = extract_financial_sample(text, max_chars=4000)
    assert len(result) <= 4500   # small headroom for section headers


def test_document_header_always_included():
    text   = "Net profit was ₹100 crore. " * 200
    result = extract_financial_sample(text, max_chars=3000)
    assert "[Document Header]" in result


def test_returns_string():
    result = extract_financial_sample("any text here")
    assert isinstance(result, str)
