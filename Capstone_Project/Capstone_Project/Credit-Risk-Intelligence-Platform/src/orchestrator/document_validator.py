# src/orchestrator/document_validator.py
# ============================================================
# Phase 15 — Missing Document Detection.
#
# Lightweight, fast, keyword-based heuristic check (no extra LLM
# call needed) that scans the combined extracted text for evidence
# of key data points BEFORE running expensive AI analysis. Shown as
# an "intelligent popup" (st.warning block) so users understand
# what's missing and why it matters, rather than getting a vague or
# low-quality AI result silently.
# ============================================================
from __future__ import annotations
from src.models.schemas import MissingDocumentAlert, LoanContext, PlatformState

# (keyword markers, item label, why it matters, severity)
_CHECKS: list[tuple[list[str], str, str, str]] = [
    (["age", "date of birth", "dob"], "Age / Date of Birth",
     "Age affects loan tenure eligibility and retirement planning calculations.", "Medium"),
    (["salary", "income", "net pay", "gross pay"], "Income Proof",
     "Income is the primary factor in determining loan eligibility and repayment capacity.", "High"),
    (["bank statement", "account statement", "balance"], "Bank Statement",
     "Bank statements verify cash flow, spending patterns, and existing balances.", "High"),
    (["credit score", "cibil", "credit report"], "Credit Score Report",
     "Credit score is a major factor in approval probability and interest rate offered.", "High"),
    (["employer", "employment", "designation", "company name"], "Employment Proof",
     "Confirms job stability, which affects repayment capacity assessment.", "Medium"),
    (["income tax return", "itr", "form 16"], "Income Tax Return (ITR)",
     "ITR provides an independently verifiable record of declared income.", "Medium"),
    (["existing loan", "outstanding loan", "emi", "current liability"], "Existing Loan Details",
     "Needed to calculate accurate Debt-to-Income ratio and total repayment burden.", "Medium"),
]


def detect_missing_documents(
    combined_text: str,
    loan_context: LoanContext,
) -> list[MissingDocumentAlert]:
    """
    Scans combined extracted document text for evidence of each key
    data point. Returns a list of MissingDocumentAlert for anything
    not found. Loan-specific checks (amount/type) are validated
    separately since those come from form inputs, not documents.
    """
    alerts: list[MissingDocumentAlert] = []
    lower_text = combined_text.lower()

    for keywords, item, why, severity in _CHECKS:
        if not any(kw in lower_text for kw in keywords):
            alerts.append(MissingDocumentAlert(item=item, why_needed=why, severity=severity))

    if loan_context.is_loan_application:
        if not loan_context.loan_amount or loan_context.loan_amount <= 0:
            alerts.append(MissingDocumentAlert(
                item="Loan Amount",
                why_needed="Required to calculate EMI affordability and safe borrowing limits.",
                severity="High",
            ))
        if not loan_context.loan_type:
            alerts.append(MissingDocumentAlert(
                item="Loan Type",
                why_needed="Different loan types have different interest rates and eligibility criteria.",
                severity="High",
            ))

    return alerts


def run_validation(state: PlatformState) -> list[MissingDocumentAlert]:
    """Convenience wrapper: validates using whatever documents are currently summarised."""
    if not state.summaries:
        return []
    combined_text = "\n".join(
        s.raw_extracted_text for s in state.summaries.values()
    )
    alerts = detect_missing_documents(combined_text, state.loan_context)
    state.missing_document_alerts = alerts
    return alerts
