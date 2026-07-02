# src/prompts/summary_prompts.py
from __future__ import annotations

DOCUMENT_SUMMARY_SYSTEM = (
    "You are a senior financial analyst. Read the provided document excerpts and "
    "produce a structured JSON summary. Be specific — include actual figures, "
    "percentages, and dates from the text. Never invent numbers."
)

COMBINED_SUMMARY_SYSTEM = (
    "You are a senior credit analyst writing a clear, simple financial briefing. "
    "Your audience may not be financial experts. Use plain language. "
    "Explain technical terms when first used."
)


def build_summary_prompt(document_text: str, doc_type: str = "") -> str:
    type_hint = f"Document type: {doc_type}\n" if doc_type else ""
    return f"""Analyse these financial document excerpts and extract key information.

{type_hint}Focus on actual financial figures, ratios, and data — ignore administrative boilerplate.

---DOCUMENT EXCERPTS---
{document_text}
---END---

Respond in valid JSON (no markdown fences, no extra text before or after):
{{
  "executive_summary": "2-3 sentences: entity name, document period, headline financial result with specific figures",
  "financial_overview": "Overall financial position with actual numbers (assets, liabilities, equity if available)",
  "key_insights": ["Insight with specific figure 1", "Insight 2", "Insight 3", "Insight 4", "Insight 5"],
  "income_summary": "Revenue/income with actual figures and year-on-year change if available",
  "expense_summary": "Expense description with actual figures if available",
  "assets_summary": "Assets description with actual figures if available",
  "liabilities_summary": "Liabilities description with actual figures if available",
  "cash_flow_summary": "Cash flow description with actual figures if available"
}}"""


def build_combined_summary_prompt(all_summaries: dict[str, str], all_text: str) -> str:
    summaries_block = "\n\n".join(
        f"=== {name} ===\n{text[:3000]}" for name, text in all_summaries.items()
    )
    n = len(all_summaries)
    return f"""You are writing a clear, simple financial summary for {n} document(s).
Write ONE combined analysis — not document by document.

FORMATTING RULES:
- Wrap every financial figure in **bold**: Net profit was **₹44,108 crore**, up **19.8%**
- Write 3-5 sentences per section
- Use simple language — explain terms that non-finance people might not know
- Example of good plain language: "The company made a profit of ₹500 crore, which is 15% more than last year"

---DOCUMENT DATA---
{summaries_block}
---END---

Detect the entity type and respond in valid JSON (no markdown fences):
{{
  "executive_overview": "3-4 sentences: entity name, reporting period, headline results with **bold figures**",
  "financial_position": "4-5 sentences on balance sheet: total assets, loans, deposits, capital with **bold figures**",
  "income_profitability": "4-5 sentences on income, net profit, margins, YoY growth with **bold figures**",
  "key_strengths": ["Strength with **specific figure**", "Strength 2", "Strength 3", "Strength 4"],
  "areas_of_concern": ["Concern with **specific figure** if available", "Concern 2", "Concern 3"],
  "overall_assessment": "2-3 sentences on overall financial health and outlook in plain language",
  "entity_type": "Commercial Bank | NBFC / Financial Institution | Large Corporate | SME / Small Business | Individual / Borrower | Unknown",
  "documents_covered": ["doc name 1", "doc name 2"]
}}"""
