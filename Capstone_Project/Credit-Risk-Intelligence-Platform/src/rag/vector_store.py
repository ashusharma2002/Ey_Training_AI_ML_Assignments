# src/rag/vector_store.py
# ============================================================
# FAISS vector store manager.
# Fix: reset() can now delete persisted files to prevent
# ghost embeddings from previous sessions contaminating new ones.
# ============================================================
from __future__ import annotations
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VectorStoreManager:
    def __init__(self, embeddings: Embeddings) -> None:
        self._embeddings  = embeddings
        self._index: FAISS | None = None
        self._index_path  = Path(settings.FAISS_INDEX_PATH)

    def build(self, documents: list[Document]) -> None:
        if not documents:
            return
        if self._index is None:
            logger.info("Creating FAISS index from %d chunks.", len(documents))
            self._index = FAISS.from_documents(documents, self._embeddings)
        else:
            logger.info("Appending %d chunks to FAISS index.", len(documents))
            self._index.add_documents(documents)
        self._persist()

    def load(self) -> bool:
        index_file = self._index_path.with_suffix(".faiss")
        if not index_file.exists():
            return False
        try:
            self._index = FAISS.load_local(
                str(self._index_path),
                self._embeddings,
                allow_dangerous_deserialization=True,
            )
            logger.info("FAISS index loaded from disk.")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load FAISS index: %s", exc)
            return False

    def similarity_search(self, query: str, k: int = settings.RETRIEVER_TOP_K) -> list[Document]:
        if self._index is None:
            return []
        results = self._index.similarity_search(query, k=k)
        logger.debug("similarity_search → %d results", len(results))
        return results

    def reset(self, delete_files: bool = False) -> None:
        """
        Clear in-memory index.
        If delete_files=True, also removes persisted FAISS files from disk.
        Use delete_files=True when starting a new session to prevent
        answers from previous sessions' documents.
        """
        self._index = None
        if delete_files:
            for suffix in [".faiss", ".pkl"]:
                p = self._index_path.with_suffix(suffix)
                if p.exists():
                    p.unlink()
                    logger.info("Deleted persisted index file: %s", p)
        logger.info("FAISS index cleared (delete_files=%s).", delete_files)

    @property
    def is_ready(self) -> bool:
        return self._index is not None

    def _persist(self) -> None:
        if self._index is None:
            return
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        self._index.save_local(str(self._index_path))
        logger.debug("FAISS index saved to %s.", self._index_path)
