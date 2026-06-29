# src/rag/chunker.py — updated with filename + year + doc_type metadata
from __future__ import annotations
from abc import ABC, abstractmethod
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseChunkStrategy(ABC):
    @abstractmethod
    def split(self, text: str, metadata: dict) -> list[Document]: ...


class RecursiveChunkStrategy(BaseChunkStrategy):
    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        _size    = chunk_size    if chunk_size    is not None else settings.CHUNK_SIZE
        _overlap = chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=_size,
            chunk_overlap=_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split(self, text: str, metadata: dict) -> list[Document]:
        docs = self._splitter.create_documents(texts=[text], metadatas=[metadata])
        logger.debug("Chunked '%s' → %d chunks", metadata.get("source", "?"), len(docs))
        return docs


class DocumentChunker:
    """
    Chunks document text and enriches each chunk's metadata with:
      - source:    original filename (not the tmp path)
      - year:      detected year from filename (e.g. 2023 from HDFC_2023.pdf)
      - doc_type:  detected document category
      - chunk_idx: sequential chunk index within the document
    """
    def __init__(self, strategy: BaseChunkStrategy | None = None) -> None:
        self._strategy: BaseChunkStrategy = strategy or RecursiveChunkStrategy()

    def chunk(
        self,
        text:          str,
        metadata:      dict | None = None,
        original_name: str | None  = None,
    ) -> list[Document]:
        """
        Split document text into overlapping chunks.

        Parameters
        ----------
        text          : The full document text.
        metadata      : Base metadata dict (will be enriched).
        original_name : The real filename (e.g. 'HDFC_2023.pdf').
                        Overrides metadata['source'] if provided.
        """
        if not text.strip():
            logger.warning("Attempted to chunk empty document text.")
            return []

        meta = dict(metadata or {})

        # Always store original filename — never a tmp path
        if original_name:
            meta["source"] = original_name

        # Auto-detect year from filename (e.g. HDFC_2023.pdf → 2023)
        source_name = meta.get("source", "")
        if "year" not in meta or not meta["year"]:
            import re
            year_match = re.search(r"(20\d{2})", source_name)
            meta["year"] = year_match.group(1) if year_match else ""

        # Auto-detect document type from filename keywords
        if "doc_type" not in meta or not meta["doc_type"]:
            lower = source_name.lower()
            if any(k in lower for k in ["annual", "ar", "report"]):
                meta["doc_type"] = "Annual Report"
            elif any(k in lower for k in ["balance", "bs"]):
                meta["doc_type"] = "Balance Sheet"
            elif any(k in lower for k in ["pnl", "p&l", "profit", "income"]):
                meta["doc_type"] = "P&L Statement"
            elif any(k in lower for k in ["bank", "statement", "account"]):
                meta["doc_type"] = "Bank Statement"
            elif any(k in lower for k in ["itr", "tax", "return"]):
                meta["doc_type"] = "Tax Return"
            else:
                meta["doc_type"] = "Financial Document"

        docs = self._strategy.split(text, meta)

        # Add sequential chunk index for debugging
        for i, doc in enumerate(docs):
            doc.metadata["chunk_idx"] = i

        return docs
