# src/retrieval/chunker.py
# ============================================================
# Document chunker with metadata enrichment.
# Improvements:
#   - Contextual chunk headers (document title injected per chunk)
#   - Increased chunk_size to 1000 for financial tables
#   - Overlap reduced to 200 (was 250)
# ============================================================
from __future__ import annotations
import re
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
    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
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
        logger.debug(
            "Chunked '%s' → %d chunks",
            metadata.get("source", "?"),
            len(docs),
        )
        return docs


class DocumentChunker:
    """
    Splits document text into overlapping chunks and enriches each
    chunk's metadata with: source, year, doc_type, chunk_idx.

    Contextual headers: each chunk gets a small header prepended so the
    LLM always knows which document a chunk came from, even without
    looking at metadata.
    """

    def __init__(self, strategy: BaseChunkStrategy | None = None) -> None:
        self._strategy: BaseChunkStrategy = strategy or RecursiveChunkStrategy()

    def chunk(
        self,
        text:          str,
        metadata:      dict | None = None,
        original_name: str | None  = None,
    ) -> list[Document]:
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

        # Enrich each chunk: add sequential index + contextual header
        source = meta.get("source", "unknown")
        year   = meta.get("year", "")
        dtype  = meta.get("doc_type", "")
        header = f"[Source: {source}"
        if year:   header += f" | Year: {year}"
        if dtype:  header += f" | Type: {dtype}"
        header += "]\n"

        for i, doc in enumerate(docs):
            doc.metadata["chunk_idx"] = i
            # Prepend contextual header so LLM always knows the document context
            doc.page_content = header + doc.page_content

        logger.info(
            "Created %d chunks from '%s' (size=%d, overlap=%d)",
            len(docs),
            source_name,
            settings.CHUNK_SIZE,
            settings.CHUNK_OVERLAP,
        )
        return docs
