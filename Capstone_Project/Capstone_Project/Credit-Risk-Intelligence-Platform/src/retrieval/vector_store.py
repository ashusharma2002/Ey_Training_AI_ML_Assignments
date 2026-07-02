# src/retrieval/vector_store.py
# ============================================================
# Vector store manager supporting FAISS (local) and
# Pinecone (cloud/production).
#
# BUG FIXED: FAISS index load path
#   Old (BROKEN): self._index_path.with_suffix(".faiss")
#                 → looks for "faiss_index.faiss" which never exists
#   New (FIXED):  self._index_path / "index.faiss"
#                 → LangChain saves to faiss_index/index.faiss
# ============================================================
from __future__ import annotations
from pathlib import Path
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FAISSVectorStore:
    """Local FAISS vector store — great for development, not for production."""

    def __init__(self, embeddings: Embeddings) -> None:
        from langchain_community.vectorstores import FAISS as _FAISS
        self._FAISS       = _FAISS
        self._embeddings  = embeddings
        self._index: _FAISS | None = None
        self._index_path  = Path(settings.FAISS_INDEX_PATH)
        self._last_error: str | None = None

    def build(self, documents: list[Document]) -> bool:
        if not documents:
            return False
        try:
            if self._index is None:
                logger.info("Creating FAISS index from %d chunks.", len(documents))
                self._index = self._FAISS.from_documents(documents, self._embeddings)
            else:
                logger.info("Appending %d chunks to FAISS index.", len(documents))
                self._index.add_documents(documents)
            self._persist()
            self._last_error = None
            return True
        except Exception as exc:
            self._last_error = f"FAISS indexing failed: {exc}"
            logger.error(self._last_error)
            return False

    def load(self) -> bool:
        """
        BUG FIX: LangChain's FAISS.save_local(path) creates:
          {path}/index.faiss
          {path}/index.pkl
        The old code checked for {path}.faiss which NEVER exists.
        """
        index_file = self._index_path / "index.faiss"   # ← FIXED
        if not index_file.exists():
            logger.debug("No persisted FAISS index found at %s", index_file)
            return False
        try:
            self._index = self._FAISS.load_local(
                str(self._index_path),
                self._embeddings,
                allow_dangerous_deserialization=True,
            )
            logger.info("FAISS index loaded from disk.")
            return True
        except Exception as exc:
            logger.error("Failed to load FAISS index: %s", exc)
            return False

    def similarity_search(
        self,
        query: str,
        k: int | None = None,
        use_mmr: bool | None = None,
    ) -> list[Document]:
        if self._index is None:
            return []

        _k    = k       if k       is not None else settings.RETRIEVER_TOP_K
        _mmr  = use_mmr if use_mmr is not None else settings.RETRIEVER_USE_MMR

        if _mmr:
            # MMR: fetch 3× candidates, then pick diverse top-k
            try:
                results = self._index.max_marginal_relevance_search(
                    query,
                    k=_k,
                    fetch_k=_k * 3,
                )
                logger.debug("MMR search → %d results", len(results))
                return results
            except Exception:
                # Fallback to standard search if MMR fails
                pass

        results = self._index.similarity_search(query, k=_k)
        logger.debug("Similarity search → %d results", len(results))
        return results

    def reset(self, delete_files: bool = False) -> None:
        self._index = None
        if delete_files:
            for name in ["index.faiss", "index.pkl"]:
                p = self._index_path / name
                if p.exists():
                    p.unlink()
                    logger.info("Deleted persisted index file: %s", p)
        logger.info("FAISS index cleared (delete_files=%s).", delete_files)

    @property
    def is_ready(self) -> bool:
        return self._index is not None

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def _persist(self) -> None:
        if self._index is None:
            return
        self._index_path.mkdir(parents=True, exist_ok=True)
        self._index.save_local(str(self._index_path))
        logger.debug("FAISS index saved to %s.", self._index_path)


class PineconeVectorStore:
    """Pinecone cloud vector store — for production deployment."""

    def __init__(self, embeddings: Embeddings) -> None:
        self._embeddings = embeddings
        self._index      = None
        self._raw_index  = None
        self._ready      = False
        self._last_error: str | None = None
        self._indexed_count = 0
        self._existing_vectors_confirmed = False
        self._init()

    def _init(self) -> None:
        if not settings.pinecone_configured:
            self._last_error = (
                "Pinecone is not configured. Set PINECONE_API_KEY in .env "
                "and ensure VECTOR_STORE_PROVIDER=pinecone."
            )
            logger.warning(self._last_error)
            return
        try:
            from pinecone import Pinecone
            from langchain_pinecone import PineconeVectorStore as _PVC

            pc    = Pinecone(api_key=settings.PINECONE_API_KEY)
            raw_index = pc.Index(settings.PINECONE_INDEX_NAME)
            self._raw_index = raw_index
            self._index = _PVC(index=raw_index, embedding=self._embeddings)
            self._ready = True
            self._last_error = None
            logger.info("Pinecone vector store connected: %s", settings.PINECONE_INDEX_NAME)
        except ImportError:
            self._last_error = (
                "Pinecone packages not installed. "
                "Run: pip install pinecone langchain-pinecone"
            )
            logger.error(self._last_error)
        except Exception as exc:
            self._last_error = (
                f"Pinecone connection failed: {exc}\n"
                f"Check: (1) PINECONE_API_KEY is correct, "
                f"(2) index '{settings.PINECONE_INDEX_NAME}' exists in your Pinecone account, "
                f"(3) index dimension matches your OPENAI_EMBEDDING_DIMENSIONS setting."
            )
            logger.error("Pinecone init failed: %s", exc)

    def build(self, documents: list[Document]) -> bool:
        if not self._ready or self._index is None:
            self._last_error = self._last_error or "Pinecone not ready — cannot index documents."
            logger.error(self._last_error)
            return False
        try:
            self._index.add_documents(documents)
            self._indexed_count += len(documents)
            self._last_error = None
            logger.info("Indexed %d chunks in Pinecone (total: %d).", len(documents), self._indexed_count)
            return True
        except Exception as exc:
            self._last_error = (
                f"Pinecone indexing failed: {exc}\n"
                f"This usually means an embedding dimension mismatch — "
                f"your Pinecone index must be created with dimension=1536 "
                f"to match OpenAI's text-embedding-3-small model."
            )
            logger.error(self._last_error)
            return False

    def load(self) -> bool:
        return self._ready

    def similarity_search(
        self,
        query: str,
        k: int | None = None,
        use_mmr: bool | None = None,
    ) -> list[Document]:
        if not self._ready or self._index is None:
            return []
        _k = k if k is not None else settings.RETRIEVER_TOP_K
        try:
            results = self._index.similarity_search(query, k=_k)
            logger.debug("Pinecone search → %d results", len(results))
            return results
        except Exception as exc:
            logger.error("Pinecone search failed: %s", exc)
            return []

    def reset(self, delete_files: bool = False) -> None:
        # Pinecone: deleting all vectors requires explicit namespace delete
        if delete_files and self._ready and self._index is not None:
            try:
                from pinecone import Pinecone
                pc    = Pinecone(api_key=settings.PINECONE_API_KEY)
                index = pc.Index(settings.PINECONE_INDEX_NAME)
                index.delete(delete_all=True)
                logger.info("Pinecone index cleared.")
            except Exception as exc:
                logger.error("Pinecone clear failed: %s", exc)
        self._indexed_count = 0

    @property
    def is_ready(self) -> bool:
        # BUG FIX (round 2): previously checked self._indexed_count > 0,
        # which is an IN-PROCESS counter that resets to 0 every time a new
        # Python process starts (e.g. the evaluation script, or a second
        # uvicorn worker). This meant a fully populated Pinecone index was
        # reported "not ready" simply because THIS process hadn't indexed
        # anything itself yet — even though the cloud index already had
        # real vectors from a previous Streamlit session.
        #
        # Fix: if this process indexed something, trust that immediately
        # (fast path, no network call). Otherwise, ask Pinecone directly
        # how many vectors actually exist in the index — this correctly
        # detects "already populated by another process" scenarios.
        if not self._ready:
            return False
        if self._indexed_count > 0:
            return True
        if self._existing_vectors_confirmed:
            return True
        if self._check_existing_vectors():
            self._existing_vectors_confirmed = True
            return True
        return False

    def _check_existing_vectors(self) -> bool:
        """Ask Pinecone directly whether the index already has vectors,
        instead of relying on an in-process counter that doesn't survive
        across separate script runs (Streamlit vs evaluation script)."""
        if self._raw_index is None:
            return False
        try:
            stats = self._raw_index.describe_index_stats()
            total = getattr(stats, "total_vector_count", None)
            if total is None and isinstance(stats, dict):
                total = stats.get("total_vector_count", 0)
            total = total or 0
            logger.info("Pinecone index '%s' has %d existing vectors.", settings.PINECONE_INDEX_NAME, total)
            return total > 0
        except Exception as exc:
            logger.debug("Could not check existing Pinecone vector count: %s", exc)
            return False

    @property
    def last_error(self) -> str | None:
        return self._last_error


def create_vector_store(embeddings: Embeddings) -> FAISSVectorStore | PineconeVectorStore:
    """Factory: returns the configured vector store implementation."""
    if settings.VECTOR_STORE_PROVIDER == "pinecone":
        logger.info("Using Pinecone vector store.")
        return PineconeVectorStore(embeddings)
    logger.info("Using FAISS local vector store.")
    return FAISSVectorStore(embeddings)
