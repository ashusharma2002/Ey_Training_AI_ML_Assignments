# src/agents/document_agent.py
# ============================================================
# Agent 1 — Document Intelligence Agent
# Extracts text from PDFs and generates structured summaries.
# ============================================================
from __future__ import annotations
import json
from pathlib import Path
from langchain_core.messages import HumanMessage, SystemMessage
from src.llm.llm_factory import invoke_with_fallback
from src.models.schemas import DocumentMetadata, DocumentSummary, DocumentType, ProcessingStatus
from src.retrieval.chunker import DocumentChunker
from src.retrieval.loader import DocumentLoader
from src.retrieval.sampling import extract_financial_sample
from src.prompts.summary_prompts import DOCUMENT_SUMMARY_SYSTEM, build_summary_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _infer_doc_type(file_name: str) -> DocumentType:
    name = file_name.lower()
    if any(k in name for k in ("bank", "statement", "account")):
        return DocumentType.BANK_STATEMENT
    if any(k in name for k in ("itr", "tax", "income_tax", "return")):
        return DocumentType.ITR
    if any(k in name for k in ("balance", "bs")):
        return DocumentType.BALANCE_SHEET
    if any(k in name for k in ("pnl", "profit", "loss", "p&l")):
        return DocumentType.PNL
    if any(k in name for k in ("annual", "ar", "report", "integrated")):
        return DocumentType.ANNUAL_REPORT
    return DocumentType.UNKNOWN


class DocumentIntelligenceAgent:
    def __init__(self) -> None:
        self._loader  = DocumentLoader()
        self._chunker = DocumentChunker()

    def process(
        self,
        file_path: str | Path,
        metadata:  DocumentMetadata,
    ) -> tuple[DocumentSummary, list]:
        path          = Path(file_path)
        original_name = metadata.file_name
        logger.info("DocumentAgent processing: %s", original_name)

        metadata.processing_status = ProcessingStatus.PROCESSING
        metadata.document_type     = _infer_doc_type(original_name)

        try:
            # 1 — Extract text
            raw_text, page_count = self._loader.load(path)
            metadata.page_count  = page_count
            logger.info(
                "Extracted %d chars from %d pages.",
                len(raw_text),
                page_count,
            )

            # 2 — Generate summary using smart financial sampling
            financial_sample = extract_financial_sample(raw_text)
            logger.info(
                "Financial sample: %d chars from %d total (%.1f%%)",
                len(financial_sample),
                len(raw_text),
                len(financial_sample) / max(len(raw_text), 1) * 100,
            )
            summary = self._generate_summary(
                financial_sample, original_name, metadata.document_type
            )
            summary.raw_extracted_text = raw_text  # store full text for RAG

            # 3 — Chunk FULL text for RAG
            chunks = self._chunker.chunk(
                raw_text,
                metadata={
                    "source":        original_name,
                    "document_type": metadata.document_type.value,
                    "file_path":     str(path),
                },
                original_name=original_name,
            )
            logger.info("Created %d chunks from %s.", len(chunks), original_name)

            metadata.processing_status = ProcessingStatus.COMPLETE
            return summary, chunks

        except Exception as exc:
            logger.error("Processing failed for %s: %s", original_name, exc)
            metadata.processing_status = ProcessingStatus.FAILED
            metadata.error_message     = str(exc)
            return DocumentSummary(file_name=original_name), []

    def _generate_summary(
        self,
        text:      str,
        file_name: str,
        doc_type:  DocumentType,
    ) -> DocumentSummary:
        prompt = build_summary_prompt(text, doc_type.value)
        try:
            raw = invoke_with_fallback([
                SystemMessage(content=DOCUMENT_SUMMARY_SYSTEM),
                HumanMessage(content=prompt),
            ])
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            data = json.loads(raw)
            return DocumentSummary(file_name=file_name, **data)
        except json.JSONDecodeError as exc:
            logger.warning("Summary JSON parse failed for %s: %s", file_name, exc)
            return DocumentSummary(
                file_name=file_name,
                executive_summary="Summary parse error — re-process this document.",
            )
        except Exception as exc:
            logger.error("Summary generation error for %s: %s", file_name, exc)
            return DocumentSummary(
                file_name=file_name,
                executive_summary=f"Summary unavailable: {exc}",
            )
