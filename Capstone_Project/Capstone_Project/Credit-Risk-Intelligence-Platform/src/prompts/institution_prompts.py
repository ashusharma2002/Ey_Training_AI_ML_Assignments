# src/prompts/institution_prompts.py
# ============================================================
# Phase 12 — Institution Document Summary.
# A structured, lender-focused executive summary distinct from
# the customer-facing combined summary (which stays plain-language
# and narrative). This one is a scannable data sheet for a loan
# officer who needs facts fast.
# ============================================================
from __future__ import annotations

INSTITUTION_SUMMARY_SYSTEM = (
    "You are preparing a structured executive summary of a loan applicant's financial "
    "documents for a bank loan officer. Be concise, factual, and use ONLY information "
    "found in the documents. Use 'Not stated in documents' for any field you cannot find "
    "— never guess or estimate a value for a missing field."
)


def build_institution_summary_prompt(combined_text: str, loan_context: dict) -> str:
    return f"""Extract a structured executive summary from the financial documents below,
for a bank loan officer reviewing this application.

LOAN CONTEXT: {loan_context}

---DOCUMENT DATA---
{combined_text[:6000]}
---END---

Respond in valid JSON (no markdown fences, no extra text). Use "Not stated in documents"
for any field with no supporting evidence — never fabricate a value:
{{
  "customer_age": "<age or 'Not stated in documents'>",
  "occupation": "<occupation/job title or 'Not stated in documents'>",
  "monthly_income": "<figure with currency or 'Not stated in documents'>",
  "annual_income": "<figure with currency or 'Not stated in documents'>",
  "credit_score": "<score or 'Not stated in documents'>",
  "existing_loans": "<summary of existing loans/EMIs or 'None found in documents'>",
  "assets": "<summary of assets or 'Not stated in documents'>",
  "liabilities": "<summary of liabilities or 'Not stated in documents'>",
  "investments": "<summary of investments or 'Not stated in documents'>",
  "requested_loan": "<amount requested, from loan context above>",
  "loan_type": "<type, from loan context above>",
  "key_financial_indicators": [
    "Indicator 1 with real figure, e.g. 'Debt-to-Income ratio: 32%'",
    "Indicator 2",
    "Indicator 3"
  ]
}}"""
