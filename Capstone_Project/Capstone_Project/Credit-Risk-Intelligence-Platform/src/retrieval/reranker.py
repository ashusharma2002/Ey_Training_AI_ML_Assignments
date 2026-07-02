# src/retrieval/reranker.py
# ============================================================
# Hybrid Search + Year-Aware Re-ranking
#
# ROOT CAUSE THIS FIXES (confirmed from real eval_run report):
#   - TC07: AI swapped 2024/2025 ESOP figures (hallucination=1.0)
#   - TC05: AI invented a borrowings increase not in any chunk (1.0)
#   - TC02/04/06/08: chunks for one year also contain OTHER years'
#     numbers (HDFC reports show 3-year comparative tables), so a
#     single retrieved chunk often "contradicts itself" when DeepEval
#     checks it — average hallucination 0.58 across factual questions.
#
# FIX:
#   1. BM25 keyword search runs ALONGSIDE vector search (hybrid).
#      Vector search finds "similar meaning"; BM25 finds "exact year/
#      number match" — the combination catches what either one alone
#      misses.
#   2. Every result is re-scored based on whether its year metadata
#      matches a year explicitly mentioned in the question. A chunk
#      tagged year=2023 is demoted when the question asks about 2025,
#      even if it's vector-similar (this is exactly what caused the
#      2024/2025 swap in TC07).
#   3. For comparison questions mentioning TWO years (e.g. "from 2023
#      to 2025"), the re-ranker guarantees both years are represented
#      in the final result set, rather than letting one year crowd out
#      the other via plain similarity ranking.
# ============================================================
from __future__ import annotations
import re
from langchain_core.documents import Document
from src.utils.logger import get_logger

logger = get_logger(__name__)

_YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")


def extract_years(text: str) -> list[str]:
    """Extract all 4-digit years (2000-2099) mentioned in a string, in order, deduplicated."""
    seen: list[str] = []
    for y in _YEAR_PATTERN.findall(text):
        if y not in seen:
            seen.append(y)
    return seen


class BM25Index:
    """
    Lightweight in-memory BM25 keyword index, kept alongside whichever
    vector store is active (FAISS or Pinecone). This makes hybrid search
    backend-agnostic — it works identically regardless of which vector
    database is configured, since BM25 only needs the raw chunk text.
    """

    def __init__(self) -> None:
        self._docs: list[Document] = []
        self._bm25 = None
        self._tokenized: list[list[str]] = []

    def add_documents(self, docs: list[Document]) -> None:
        self._docs.extend(docs)
        self._rebuild()

    def _rebuild(self) -> None:
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            logger.warning(
                "rank_bm25 not installed — hybrid search disabled, falling back "
                "to vector-only search. Run: pip install rank-bm25"
            )
            self._bm25 = None
            return
        self._tokenized = [self._tokenize(d.page_content) for d in self._docs]
        if self._tokenized:
            self._bm25 = BM25Okapi(self._tokenized)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9₹%.]+", text.lower())

    def search(self, query: str, top_k: int = 10) -> list[tuple[Document, float]]:
        """Returns [(document, bm25_score), ...] sorted by score descending."""
        if self._bm25 is None or not self._docs:
            return []
        scores = self._bm25.get_scores(self._tokenize(query))
        ranked = sorted(zip(self._docs, scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    @property
    def is_ready(self) -> bool:
        return self._bm25 is not None and len(self._docs) > 0

    def reset(self) -> None:
        self._docs = []
        self._bm25 = None
        self._tokenized = []


def year_aware_rerank(
    query: str,
    candidates: list[Document],
    top_k: int,
) -> list[Document]:
    """
    Re-scores and reorders candidate chunks so that chunks whose year
    metadata matches a year mentioned in the question are prioritised,
    and (for 2-year comparison questions) both years are guaranteed
    representation in the final list instead of one year crowding out
    the other.
    """
    question_years = extract_years(query)

    if not question_years:
        # No specific year mentioned — original similarity order is fine.
        return candidates[:top_k]

    def year_match_score(doc: Document) -> int:
        doc_year = str(doc.metadata.get("year", ""))
        if doc_year in question_years:
            return 2   # exact match — strongly preferred
        if not doc_year:
            return 1   # unknown year — neutral, don't penalise too harshly
        return 0       # wrong year — actively demoted

    # Stable sort: preserves original similarity order within each score tier.
    scored = sorted(
        enumerate(candidates),
        key=lambda pair: (-year_match_score(pair[1]), pair[0]),
    )
    reranked = [doc for _, doc in scored]

    if len(question_years) >= 2:
        # Comparison question (e.g. "increase from 2023 to 2025") — make sure
        # BOTH years actually appear in the final set, not just whichever
        # year happened to be more vector-similar.
        guaranteed: list[Document] = []
        for yr in question_years:
            match = next(
                (d for d in reranked if str(d.metadata.get("year", "")) == yr),
                None,
            )
            if match and match not in guaranteed:
                guaranteed.append(match)
        remaining = [d for d in reranked if d not in guaranteed]
        reranked = guaranteed + remaining
        if len(guaranteed) < len(question_years):
            missing = [y for y in question_years if not any(
                str(d.metadata.get("year", "")) == y for d in guaranteed
            )]
            logger.warning(
                "Comparison question mentions years %s but no chunk found for: %s. "
                "Answer should be flagged as potentially incomplete.",
                question_years, missing,
            )

    return reranked[:top_k]


def reciprocal_rank_fusion(
    vector_results: list[Document],
    bm25_results:   list[tuple[Document, float]],
    k: int = 60,
) -> list[Document]:
    """
    Merges vector search results and BM25 results into one ranked list
    using Reciprocal Rank Fusion (RRF) — a standard, parameter-light way
    to combine two different ranking signals without needing to manually
    tune relative score weights between cosine similarity and BM25 score
    (which are on completely different numeric scales).
    """
    scores: dict[int, float] = {}
    doc_lookup: dict[int, Document] = {}

    def _key(doc: Document) -> int:
        return id(doc) if doc in vector_results else hash(doc.page_content[:200])

    for rank, doc in enumerate(vector_results):
        key = hash(doc.page_content[:200])
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
        doc_lookup[key] = doc

    for rank, (doc, _bm25_score) in enumerate(bm25_results):
        key = hash(doc.page_content[:200])
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
        doc_lookup.setdefault(key, doc)

    ranked_keys = sorted(scores.keys(), key=lambda k_: scores[k_], reverse=True)
    return [doc_lookup[k_] for k_ in ranked_keys]
