# src/agents/document_agent.py
# ============================================================
# Agent 1 — Document Intelligence Agent
# Extracts text from PDFs and generates structured summaries.
#
# KEY FIX: Uses smart financial sampling instead of text[:6000].
# For a 600-page annual report, first 6000 chars is the cover
# letter. We now sample from multiple positions to find the
# actual financial content.
# ============================================================
from __future__ import annotations
import json, re
from pathlib import Path
from langchain_core.messages import HumanMessage, SystemMessage
from src.llm.llm_factory import invoke_with_fallback
from src.models.schemas import DocumentMetadata, DocumentSummary, DocumentType, ProcessingStatus
from src.rag.chunker import DocumentChunker
from src.rag.loader import DocumentLoader
from src.rag.prompt_builder import build_summary_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are a senior financial analyst. Read the provided document excerpts and "
    "produce a structured JSON summary. Be specific — include actual figures, "
    "percentages, and dates from the text. Never invent numbers."
)


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


def _extract_financial_sample(text: str, max_chars: int = 8000) -> str:
    """
    Smart financial content sampling.

    Problem: Annual reports start with cover letters and AGM notices.
    Simply taking text[:6000] gives the LLM irrelevant admin content.

    Solution: Score every ~600-char page segment by financial keyword
    density. Select the top-scoring segments to build the context.
    This ensures the LLM sees actual balance sheet / P&L data.
    """
    if len(text) <= max_chars:
        return text

    # Financial keywords — pages with more of these are more valuable
    keywords = [
        "net profit", "total assets", "interest earned", "capital adequacy",
        "gross npa", "net interest", "return on", "earnings per share",
        "crore", "lakh", "advances", "deposits", "provisions", "revenue",
        "ebitda", "balance sheet", "profit before tax", "net worth",
        "total income", "operating profit", "cash flow", "dividend",
    ]

    # Split text into ~600-char segments and score each
    seg_size = 600
    segments = [text[i:i+seg_size] for i in range(0, len(text), seg_size)]

    scored = []
    for idx, seg in enumerate(segments):
        lower = seg.lower()
        score = sum(1 for k in keywords if k in lower)
        # Extra weight for segments with actual numbers (crore values)
        crore_hits = len(re.findall(r'\d[\d,.]*\s*crore', lower))
        score += crore_hits * 2
        scored.append((score, idx, seg))

    # Sort by score descending
    scored.sort(reverse=True)

    # Build result: document identity header + top financial segments
    # Always include the first segment for document identity
    identity = segments[0][:400].strip()
    result_parts = [f"[DOCUMENT HEADER]\n{identity}"]
    chars_used = len(result_parts[0])

    # Add high-scoring financial segments (keeping order for readability)
    top_indices = sorted([idx for _, idx, _ in scored[:20]])
    for idx in top_indices:
        seg = segments[idx].strip()
        if not seg:
            continue
        if chars_used + len(seg) > max_chars:
            break
        result_parts.append(f"[Excerpt from ~page {idx+1}]\n{seg}")
        chars_used += len(seg)

    return "\n\n---\n\n".join(result_parts)


class DocumentIntelligenceAgent:
    def __init__(self) -> None:
        self._loader  = DocumentLoader()
        self._chunker = DocumentChunker()

    def process(
        self,
        file_path:  str | Path,
        metadata:   DocumentMetadata,
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
            logger.info("Extracted %d chars from %d pages.", len(raw_text), page_count)

            # 2 — Generate summary using SMART sampling (fixes the cover-letter bug)
            financial_sample = _extract_financial_sample(raw_text)
            logger.info(
                "Financial sample: %d chars from %d total (%.1f%%)",
                len(financial_sample), len(raw_text),
                len(financial_sample)/max(len(raw_text), 1)*100
            )
            summary = self._generate_summary(
                financial_sample, original_name, metadata.document_type
            )
            summary.raw_extracted_text = raw_text  # store full text for RAG

            # 3 — Chunk FULL text for RAG (not just the sample)
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

        except Exception as exc:  # noqa: BLE001
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
            from langchain_core.messages import SystemMessage, HumanMessage
            raw = invoke_with_fallback([
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])
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
        except Exception as exc:  # noqa: BLE001
            logger.error("Summary generation error for %s: %s", file_name, exc)
            return DocumentSummary(
                file_name=file_name,
                executive_summary=f"Summary unavailable: {exc}",
            )
