# tests/unit/test_reranker.py
# Covers the hallucination-reduction fixes built directly from the
# real eval_run_20260630_085258.json report:
#   - TC07: AI swapped 2024/2025 figures (hallucination=1.0)
#   - TC05: AI invented an unsupported cross-year comparison (1.0)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_core.documents import Document
from src.retrieval.reranker import (
    extract_years, year_aware_rerank, BM25Index, reciprocal_rank_fusion,
)


def _doc(text: str, year: str) -> Document:
    return Document(page_content=text, metadata={"year": year})


# ── extract_years ─────────────────────────────────────────────────────

def test_extract_years_single():
    assert extract_years("What was the NPA in 2025?") == ["2025"]


def test_extract_years_comparison():
    assert extract_years("Increase from 2023 to 2025") == ["2023", "2025"]


def test_extract_years_none():
    assert extract_years("What is the current stock price?") == []


def test_extract_years_deduplicates():
    assert extract_years("2025 figures compared to 2025 estimates") == ["2025"]


# ── year_aware_rerank — single-year questions ────────────────────────

def test_rerank_promotes_matching_year_to_top():
    """Reproduces TC07: a 2025 question must rank the 2025 chunk first,
    even if vector search originally ranked 2024 higher."""
    docs = [_doc("ESOP 2024: 14,13,74,510", "2024"), _doc("ESOP 2025: 17,56,59,424", "2025")]
    result = year_aware_rerank("What was the increase in ESOP in 2025?", docs, top_k=2)
    assert result[0].metadata["year"] == "2025"


def test_rerank_demotes_wrong_year():
    docs = [_doc("2023 data", "2023"), _doc("2025 data", "2025"), _doc("2024 data", "2024")]
    result = year_aware_rerank("question about 2025", docs, top_k=1)
    assert result[0].metadata["year"] == "2025"


def test_rerank_no_year_mentioned_preserves_order():
    """If the question doesn't mention a year, original similarity order is untouched."""
    docs = [_doc("a", "2024"), _doc("b", "2025")]
    result = year_aware_rerank("What is the gross NPA?", docs, top_k=2)
    assert result == docs


def test_rerank_unknown_year_metadata_not_overly_penalised():
    """A chunk with no year metadata should rank above a WRONG-year chunk,
    since we genuinely don't know if it's relevant (neutral, not negative)."""
    docs = [_doc("wrong year", "2020"), _doc("unknown year", "")]
    result = year_aware_rerank("question about 2025", docs, top_k=2)
    assert result[0].metadata.get("year", "") == ""


# ── year_aware_rerank — comparison questions (2 years) ────────────────

def test_rerank_comparison_guarantees_both_years():
    """Reproduces TC05: a comparison question must have BOTH years
    represented in the final result, not just whichever was more
    vector-similar."""
    docs = [_doc("2024 filler", "2024"), _doc("2024 filler 2", "2024"), _doc("2023 data", "2023"), _doc("2025 data", "2025")]
    result = year_aware_rerank("increase from 2023 to 2025", docs, top_k=2)
    years_present = {d.metadata["year"] for d in result}
    assert years_present == {"2023", "2025"}


def test_rerank_comparison_with_missing_year_does_not_crash():
    """If one of the two requested years has no matching chunk at all,
    the function must not crash — it should just return what's available."""
    docs = [_doc("2024 data", "2024")]
    result = year_aware_rerank("increase from 2023 to 2025", docs, top_k=5)
    assert len(result) == 1  # no crash, just returns what exists


# ── BM25Index ──────────────────────────────────────────────────────────

def test_bm25_finds_exact_figure_match():
    docs = [
        _doc("Net profit for the year was 45997.11 crore", "2025"),
        _doc("Total assets grew significantly this period", "2025"),
    ]
    bm25 = BM25Index()
    bm25.add_documents(docs)
    results = bm25.search("45997.11 crore net profit", top_k=2)
    assert results[0][0].page_content.startswith("Net profit")


def test_bm25_not_ready_before_documents_added():
    bm25 = BM25Index()
    assert bm25.is_ready is False


def test_bm25_reset_clears_index():
    bm25 = BM25Index()
    bm25.add_documents([_doc("some text", "2025")])
    assert bm25.is_ready is True
    bm25.reset()
    assert bm25.is_ready is False


# ── Reciprocal Rank Fusion ─────────────────────────────────────────────

def test_rrf_merges_two_ranked_lists():
    d1, d2, d3 = _doc("a", "2025"), _doc("b", "2025"), _doc("c", "2025")
    vector_results = [d1, d2, d3]
    bm25_results    = [(d3, 5.0), (d1, 2.0), (d2, 1.0)]
    fused = reciprocal_rank_fusion(vector_results, bm25_results)
    assert len(fused) == 3
    # d1 and d3 both rank highly in at least one list, so they should
    # outrank d2 (which is consistently ranked last in both lists)
    fused_contents = [d.page_content for d in fused]
    assert fused_contents.index("b") == 2  # d2 should be last
