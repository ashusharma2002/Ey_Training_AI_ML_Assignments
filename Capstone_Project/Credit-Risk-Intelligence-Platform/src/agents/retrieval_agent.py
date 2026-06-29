# src/agents/retrieval_agent.py
# ============================================================
# Agent 2 — FAISS vector store management and retrieval.
# Fixes:
#   • Default top_k now reads from settings (was hardcoded 5)
#   • reset_index() can delete persisted files (prevents ghost data)
#   • No auto-load of old index on startup (session isolation)
# ============================================================
from __future__ import annotations
from pathlib import Path
from langchain_core.documents import Document
from src.llm.llm_factory import get_embeddings
from src.rag.vector_store import VectorStoreManager
from src.utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


class RetrievalAgent:
    def __init__(self) -> None:
        self._vs: VectorStoreManager | None = None

    def _get_store(self) -> VectorStoreManager:
        if self._vs is None:
            embeddings = get_embeddings()
            self._vs   = VectorStoreManager(embeddings)
            # NOTE: We intentionally do NOT call self._vs.load() here.
            # Loading an old persisted index in a new session would cause
            # "ghost document" answers from previous sessions.
            # The persisted index is only used for explicit session restore.
        return self._vs

    def index_documents(self, chunks: list[Document]) -> None:
        if not chunks:
            logger.warning("index_documents called with empty chunk list.")
            return
        store = self._get_store()
        logger.info("Indexing %d chunks.", len(chunks))
        store.build(chunks)

    def retrieve(
        self,
        query:  str,
        top_k:  int | None = None,
    ) -> list[Document]:
        """
        Retrieve top-k most relevant chunks.
        top_k defaults to settings.RETRIEVER_TOP_K (12) — not 5.
        """
        if top_k is None:
            top_k = settings.RETRIEVER_TOP_K

        store = self._get_store()
        if not store.is_ready:
            logger.warning("retrieve() called but vector store not ready.")
            return []

        results = store.similarity_search(query, k=top_k)
        logger.info("retrieve('%s...') → %d results", query[:40], len(results))
        return results

    def reset_index(self, delete_persisted: bool = False) -> None:
        """
        Clear in-memory index.
        If delete_persisted=True, also deletes the FAISS files from disk.
        This prevents ghost embeddings from previous sessions.
        """
        if self._vs:
            self._vs.reset(delete_files=delete_persisted)
        self._vs = None
        logger.info("Vector store reset (delete_persisted=%s).", delete_persisted)

    @property
    def is_ready(self) -> bool:
        if self._vs is None:
            return False
        return self._vs.is_ready
