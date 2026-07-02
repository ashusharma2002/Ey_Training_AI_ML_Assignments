# src/agents/retrieval_agent.py
# ============================================================
# Agent 2 — Vector store management and retrieval.
#
# v2.1 update (hallucination-reduction pass, based on real eval data):
#   - Hybrid search: BM25 keyword index runs alongside the vector
#     store (FAISS/Pinecone), merged via Reciprocal Rank Fusion.
#   - Year-aware re-ranking: chunks whose year metadata conflicts
#     with a year mentioned in the question are demoted; comparison
#     questions (mentioning 2 years) guarantee both years appear in
#     the final result set.
#   - validate_question() tightened: now also checks that a question
#     mentioning a specific year actually has a matching-year chunk
#     available, not just "any non-empty result".
# ============================================================
from __future__ import annotations
from langchain_core.documents import Document
from src.llm.llm_factory import get_embeddings
from src.retrieval.vector_store import create_vector_store
from src.retrieval.reranker import BM25Index, extract_years, year_aware_rerank, reciprocal_rank_fusion
from src.utils.logger import get_logger
from config.settings import settings

try:
    from langsmith import traceable as _traceable
except ImportError:
    def _traceable(**kwargs):
        def decorator(func): return func
        return decorator

logger = get_logger(__name__)


class RetrievalAgent:
    def __init__(self) -> None:
        self._vs = None
        self._init_error: str | None = None
        self._bm25 = BM25Index()

    def _get_store(self):
        if self._vs is None:
            embeddings = get_embeddings()
            self._vs   = create_vector_store(embeddings)
            # NOTE: We do NOT auto-load persisted index on startup.
            # This prevents ghost-document answers from previous sessions.
        return self._vs

    def index_documents(self, chunks: list[Document]) -> bool:
        if not chunks:
            logger.warning("index_documents called with empty chunk list.")
            return False
        try:
            store = self._get_store()
        except Exception as exc:
            self._init_error = f"Could not initialise vector store: {exc}"
            logger.error(self._init_error)
            return False
        logger.info("Indexing %d chunks.", len(chunks))
        success = store.build(chunks)
        if success:
            # Keep the BM25 keyword index in sync with the vector store,
            # regardless of which vector backend (FAISS/Pinecone) is active.
            self._bm25.add_documents(chunks)
        if not success:
            logger.error("Indexing failed: %s", self.last_error)
        return success

    @_traceable(name="retrieval_agent.retrieve", run_type="retriever",
                metadata={"component": "retrieval_agent"})
    def retrieve(
        self,
        query:        str,
        top_k:        int | None  = None,
        use_mmr:      bool | None = None,
        use_hybrid:   bool | None = None,
        use_rerank:   bool | None = None,
    ) -> list[Document]:
        """
        Retrieve top-k most relevant chunks.

        Pipeline (all configurable, all default to settings):
          1. Vector similarity search (MMR for diversity)
          2. BM25 keyword search (catches exact figures/years vector
             search sometimes misses due to semantic-similarity bias)
          3. Reciprocal Rank Fusion merges both result lists
          4. Year-aware re-ranking demotes chunks whose year conflicts
             with a year explicitly mentioned in the question
        """
        _k       = top_k      if top_k      is not None else settings.RETRIEVER_TOP_K
        _mmr     = use_mmr    if use_mmr    is not None else settings.RETRIEVER_USE_MMR
        _hybrid  = use_hybrid if use_hybrid is not None else settings.HYBRID_SEARCH_ENABLED
        _rerank  = use_rerank if use_rerank is not None else settings.RERANK_ENABLED

        store = self._get_store()
        if not store.is_ready:
            logger.warning("retrieve() called but vector store not ready.")
            return []

        # Fetch a larger candidate pool than _k so re-ranking has room to work
        fetch_k = max(_k * 3, 12)
        vector_results = store.similarity_search(query, k=fetch_k, use_mmr=_mmr)

        if _hybrid and self._bm25.is_ready:
            bm25_results = self._bm25.search(query, top_k=fetch_k)
            merged = reciprocal_rank_fusion(vector_results, bm25_results)
            logger.debug(
                "Hybrid search: %d vector + %d BM25 -> %d merged candidates",
                len(vector_results), len(bm25_results), len(merged),
            )
        else:
            merged = vector_results

        if _rerank:
            final = year_aware_rerank(query, merged, top_k=_k)
        else:
            final = merged[:_k]

        logger.info(
            "retrieve('%s...') -> %d results (hybrid=%s, rerank=%s)",
            query[:40], len(final), _hybrid, _rerank,
        )
        return final

    def validate_question(self, question: str) -> bool:
        """
        Check whether a question has at least one retrievable answer that
        contains REAL financial content — not just any non-empty chunk.

        Used to pre-validate suggested questions so system-generated
        questions NEVER appear in the UI unless the RAG pipeline can
        guarantee a meaningful answer exists in the uploaded documents.

        This is enforced in two layers:
          Layer 1 (this method): retrieval check — does the vector store
            return a chunk that (a) has enough text AND (b) contains at
            least one financial keyword? This filters out questions where
            the only matching chunks are boilerplate headers or disclaimers.
          Layer 2 (chat_agent.py): fallback validation — even the
            hardcoded fallback questions are put through this same check,
            so a fallback that doesn't match the uploaded document type
            is also dropped rather than shown.

        The MANUAL QUESTION EXCEPTION: this check is intentionally only
        applied to SYSTEM-GENERATED suggested questions, never to questions
        the user types manually — if a user asks something not in the docs,
        the answer_question() method replies "not found in your documents",
        which is the correct and acceptable behaviour per the requirement.
        """
        if not self.is_ready:
            return False
        try:
            results = self.retrieve(question, top_k=3, use_mmr=False)

            # Require at least one chunk with real content (not just a
            # disclaimer or page header, which can be 50+ chars but useless)
            has_content = len(results) > 0 and any(
                len(doc.page_content.strip()) > 80 for doc in results
            )
            if not has_content:
                return False

            # Require at least one chunk to contain a financial keyword.
            # A question like "what is the net profit?" that only retrieves
            # chunks saying "this is a fictional test document" passes the
            # length check but fails here — correctly rejected.
            _FINANCIAL_KEYWORDS = {
                "income", "salary", "profit", "loss", "revenue", "asset",
                "liabilit", "loan", "emi", "credit", "debit", "balance",
                "interest", "rate", "score", "cibil", "net", "gross",
                "tax", "payment", "outstanding", "deposit", "saving",
                "investment", "expense", "cash", "debt", "equity",
                "capital", "npa", "bank", "account", "amount", "rs.",
                "lakh", "crore", "default", "overdue", "repay",
            }
            has_financial_content = any(
                any(kw in doc.page_content.lower() for kw in _FINANCIAL_KEYWORDS)
                for doc in results
            )
            if not has_financial_content:
                logger.info(
                    "Question '%s...' — retrieved chunks contain no financial "
                    "keywords (likely boilerplate). Rejecting as unanswerable.",
                    question[:50],
                )
                return False

            # Year-specificity check: if the question mentions a year,
            # at least one retrieved chunk must carry that year as metadata
            question_years = extract_years(question)
            if question_years:
                available_years = {str(d.metadata.get("year", "")) for d in results}
                if not any(y in available_years for y in question_years):
                    logger.info(
                        "Question '%s...' mentions year(s) %s but no matching "
                        "chunk retrieved — rejecting as unanswerable.",
                        question[:50], question_years,
                    )
                    return False

            return True

        except Exception as exc:
            logger.warning(
                "Question validation failed for '%s': %s", question[:50], exc
            )
            return False

    def reset_index(self, delete_persisted: bool = False) -> None:
        if self._vs:
            self._vs.reset(delete_files=delete_persisted)
        self._vs = None
        self._bm25.reset()
        logger.info("Vector store reset (delete_persisted=%s).", delete_persisted)

    @property
    def is_ready(self) -> bool:
        if self._vs is None:
            return False
        return self._vs.is_ready

    @property
    def last_error(self) -> str | None:
        if self._vs is None:
            return self._init_error
        return getattr(self._vs, "last_error", None) or self._init_error
