# src/retrieval/sampling.py
# ============================================================
# Smart financial content sampling.
#
# Problem: Annual reports start with cover letters, AGM notices,
# and legal boilerplate. Taking text[:6000] gives the LLM
# irrelevant admin content and wastes the context window.
#
# Solution: Score every ~800-char page segment by financial
# keyword density. Select top-scoring segments.
# This ensures the LLM sees actual balance sheet / P&L data.
# ============================================================
from __future__ import annotations
import re


# Financial keywords — pages with more of these are more valuable
_FINANCIAL_KEYWORDS = [
    "net profit", "total assets", "interest earned", "capital adequacy",
    "gross npa", "net interest", "return on", "earnings per share",
    "crore", "lakh", "advances", "deposits", "provisions", "revenue",
    "ebitda", "balance sheet", "profit before tax", "net worth",
    "total income", "operating profit", "cash flow", "dividend",
    "total liabilities", "equity", "net sales", "gross profit",
    "income tax", "depreciation", "amortisation", "working capital",
    "current ratio", "debt to equity", "book value", "roe", "roa",
    "net interest margin", "nim", "tier 1", "tier 2", "crar",
    "monthly income", "monthly expense", "savings", "investment",
]

_CRORE_PATTERN = re.compile(r'\d[\d,.]*\s*crore', re.IGNORECASE)


def extract_financial_sample(text: str, max_chars: int = 8000) -> str:
    """
    Extract the most financially relevant portions of a document.

    Returns up to `max_chars` of text by selecting the highest-scoring
    segments based on financial keyword density and numeric content.

    Parameters
    ----------
    text      : Full document text.
    max_chars : Maximum characters to return.

    Returns
    -------
    str : Concatenated financial excerpts, prefixed with document header.
    """
    if len(text) <= max_chars:
        return text

    seg_size = 800
    segments = [text[i:i + seg_size] for i in range(0, len(text), seg_size)]

    scored = []
    for idx, seg in enumerate(segments):
        lower = seg.lower()
        score = sum(1 for k in _FINANCIAL_KEYWORDS if k in lower)
        # Extra weight for segments with crore values (indicates Indian financial data)
        crore_hits = len(_CRORE_PATTERN.findall(lower))
        score += crore_hits * 2
        # Extra weight for segments with many numbers
        number_count = len(re.findall(r'\b\d{2,}\b', seg))
        score += min(number_count // 5, 3)
        scored.append((score, idx, seg))

    # Sort by score descending
    scored.sort(reverse=True)

    # Always include the document identity header (first 400 chars)
    identity = segments[0][:400].strip() if segments else ""
    result_parts = [f"[Document Header]\n{identity}"]
    chars_used = len(result_parts[0])

    # Select segments by SCORE (highest first), then sort by index for readability.
    # This ensures high-value financial segments at the end of a doc are ALWAYS included.
    # (Old approach: sort by index first → ran out of chars before reaching financial data)
    selected: list[tuple[int, str]] = []
    for score, idx, seg in scored:   # already sorted by score DESC
        seg = seg.strip()
        if not seg:
            continue
        if chars_used + len(seg) + 20 > max_chars:
            continue   # skip — try next (might be shorter)
        if score == 0 and len(selected) > 0:
            break      # no point adding zero-score filler once we have content
        selected.append((idx, seg))
        chars_used += len(seg) + 20   # +20 for section header
        if len(selected) >= 8:
            break

    # Restore natural reading order
    selected.sort(key=lambda x: x[0])
    for idx, seg in selected:
        result_parts.append(f"[Section ~{idx + 1}]\n{seg}")

    return "\n\n---\n\n".join(result_parts)
