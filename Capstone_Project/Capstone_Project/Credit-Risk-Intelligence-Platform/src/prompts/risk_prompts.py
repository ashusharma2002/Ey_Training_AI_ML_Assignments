# src/prompts/risk_prompts.py
# ============================================================
# Entity-aware + loan-aware + institution-aware risk prompts.
#
# BUG FIX (original): Previously ALL entities (banks, corporates,
# individuals) got the same prompt asking for "debt_to_income_ratio"
# — meaningless for a bank like HDFC, producing a permanent "N/A".
# Branches by entity type for the right metrics (CRAR/NPA for banks,
# D/E for corporates, DTI for individuals).
#
# v3.0 additions:
#   - Phase 9: when a CUSTOMER is applying for a loan, additionally
#     asks for approval probability, interest rate range, safe
#     borrowing amount, affordable EMI, recommended bank types.
#   - Phase 13: when an INSTITUTION reviews a loan application,
#     additionally asks for a lender-focused assessment: risk
#     category, repayment capacity, default risk, fraud indicators,
#     confidence score.
#   - Both additions are OPT-IN — when no loan context is present,
#     behaviour is identical to before these phases existed.
# ============================================================
from __future__ import annotations
from src.models.schemas import EntityType, LoanContext

RISK_SYSTEM_PROMPT = """You are a credit risk officer assessing a financial entity.
Analyse the financial data objectively. ONLY use data provided — never fabricate or estimate numbers.
Explain your findings in plain language that a non-finance person can understand.
Use a traffic-light approach: green = good, yellow = needs attention, red = serious problem.
CRITICAL: Tailor every metric, ratio, and recommendation to the SCALE and TYPE of entity in the data
(a bank with ₹1,000+ crore in assets is fundamentally different from an individual borrower —
never apply individual-borrower thinking or amounts to an institutional entity, or vice versa).
Only provide loan/lending suggestions that are supported by evidence in the data — never guess."""


def _metric_instructions(entity_type: EntityType) -> str:
    if entity_type in (EntityType.COMMERCIAL_BANK, EntityType.NBFC):
        return """This is a BANK / NBFC. Your headline metrics MUST be banking-specific:
  - Capital Adequacy Ratio (CRAR) — regulatory minimum is 11.5% (RBI norm); below this is a red flag
  - Gross NPA ratio — loans not being repaid; below 5% is healthy, above 8% is concerning
  - Net Interest Margin (NIM) — profitability of lending operations
Do NOT calculate or mention "debt-to-income ratio" — this concept does not apply to a bank.
Set debt_to_income_ratio to null. Set monthly_income_estimate and monthly_expense_estimate to null.
Populate key_metrics with the 1-2 most important banking ratios you found in the data."""

    if entity_type in (EntityType.LARGE_CORPORATE, EntityType.SME):
        return """This is a CORPORATE / BUSINESS entity. Your headline metrics MUST be corporate-finance specific:
  - Debt-to-Equity ratio — below 2.0 is generally healthy for most industries
  - Interest Coverage Ratio — ability to pay interest from operating profit (EBIT/Interest)
  - Operating margin or net profit margin
Do NOT calculate "debt-to-income ratio" — this is a personal-finance concept, not corporate.
Set debt_to_income_ratio to null. Set monthly_income_estimate and monthly_expense_estimate to null
UNLESS this is clearly a sole-proprietorship/SME with personal-business overlap.
Populate key_metrics with the 1-2 most important corporate ratios you found in the data."""

    return """This is an INDIVIDUAL / personal borrower. Use personal-finance metrics:
  - Debt-to-income ratio (total monthly debt payments / monthly income)
  - Monthly income and monthly expense estimates
Populate debt_to_income_ratio, monthly_income_estimate, and monthly_expense_estimate
using actual figures found in the documents (null if genuinely not available — never guess).
Also populate key_metrics with debt-to-income ratio as the headline metric for consistency."""


def _eligibility_instructions(entity_type: EntityType) -> str:
    if entity_type in (EntityType.COMMERCIAL_BANK, EntityType.NBFC, EntityType.LARGE_CORPORATE, EntityType.SME):
        return (
            "loan_eligibility here means: this entity's eligibility to raise additional "
            "capital, debt, or credit lines from investors/lenders — NOT a personal loan. "
            "Use values like 'Eligible for Additional Capital', 'Conditionally Eligible', "
            "'Not Recommended for Additional Leverage'."
        )
    return (
        "loan_eligibility means this individual's eligibility for a personal/retail loan. "
        "Use: 'Eligible', 'Conditionally Eligible', or 'Not Eligible'."
    )


def _customer_loan_instructions(loan_context: LoanContext) -> str:
    """Phase 9 — Enhanced Customer Risk Analysis, only active when applying for a loan."""
    amount = loan_context.loan_amount or 0
    ltype  = loan_context.loan_type.value if loan_context.loan_type else "unspecified"
    return f"""
LOAN APPLICATION CONTEXT (Phase 9 — customer is applying for a loan):
  Requested amount: ₹{amount:,.0f}
  Requested loan type: {ltype}

Additionally provide, based ONLY on evidence in the data:
  - approval_probability: a qualitative + rough percentage estimate, e.g. "Moderate (50-65%)"
  - interest_rate_range: realistic range for this loan type given the applicant's profile, e.g. "9.5% - 11.5%"
  - best_loan_type: which loan type (from: Personal/Home/Business/Education/Vehicle/Gold/Other)
    best fits this applicant's profile, even if different from what they requested — explain why
  - affordable_emi: a monthly EMI figure this applicant could comfortably afford given their income
  - safe_borrowing_amount: a maximum SAFE loan amount, which may be LOWER than the ₹{amount:,.0f} requested
    if the data suggests that amount is risky — be honest, do not just approve the requested amount
  - recommended_banks: 2-3 reputable bank TYPES to approach (e.g. "Government banks (SBI, PNB) for lower rates",
    "Private banks (HDFC, ICICI) for faster processing") — never recommend a specific named lender you cannot verify
  - avoid_lenders_warning: a short warning to avoid unregulated/unlicensed lenders, if relevant
  - alternative_suggestions: 1-3 alternatives ONLY if evidence supports them, e.g. "Consider a lower EMI by
    extending tenure", "Increasing down payment by X would improve approval odds", "Waiting 6 months to
    improve credit score could lower the interest rate" — every suggestion must be evidence-based, not generic"""


def _institution_loan_instructions(loan_context: LoanContext) -> str:
    """Phase 13 — Institution Risk Analysis, lender-focused assessment."""
    amount = loan_context.loan_amount or 0
    ltype  = loan_context.loan_type.value if loan_context.loan_type else "unspecified"
    applicant = loan_context.applicant_type.value if loan_context.applicant_type else "unspecified"
    return f"""
LENDER REVIEW CONTEXT (Phase 13 — institution reviewing a loan application):
  Requested amount: ₹{amount:,.0f}
  Requested loan type: {ltype}
  Applicant type: {applicant}

You are now assessing this FROM THE LENDER'S PERSPECTIVE, to help a loan officer decide faster.
Additionally provide, based ONLY on evidence in the data:
  - risk_category: e.g. "Low Risk", "Moderate Risk", "High Risk", "Requires Manual Review"
  - repayment_capacity: assessment of ability to repay this specific loan amount, with reasoning
  - income_stability: assessment of how stable/verifiable the income source appears
  - credit_history_summary: brief summary of credit history quality from available data
  - default_risk: qualitative risk of default, e.g. "Low — strong repayment history evident"
  - fraud_indicators: list any inconsistencies or red flags suggesting possible fraud/misrepresentation
    (e.g. "Stated income doesn't match bank statement deposits") — empty list if none found, NEVER invent one
  - confidence_score: 0-100, how confident you are in this assessment given the completeness of the data
    (lower confidence if key documents are missing — be honest about data limitations)"""


def build_risk_prompt(
    combined_text: str,
    entity_type:   EntityType = EntityType.UNKNOWN,
    loan_context:  LoanContext | None = None,
    account_type:  str = "customer",
) -> str:
    metric_instructions      = _metric_instructions(entity_type)
    eligibility_instructions = _eligibility_instructions(entity_type)
    entity_label = entity_type.value

    loan_section = ""
    extra_json_fields = ""
    if loan_context and loan_context.is_loan_application:
        if account_type == "institution":
            loan_section = _institution_loan_instructions(loan_context)
            extra_json_fields = """,
  "risk_category": "<string or null>",
  "repayment_capacity": "<string or null>",
  "income_stability": "<string or null>",
  "credit_history_summary": "<string or null>",
  "default_risk": "<string or null>",
  "fraud_indicators": ["<string>", "..."],
  "confidence_score": <0-100 or null>"""
        else:
            loan_section = _customer_loan_instructions(loan_context)
            extra_json_fields = """,
  "approval_probability": "<string or null>",
  "interest_rate_range": "<string or null>",
  "best_loan_type": "<string or null>",
  "affordable_emi": "<string or null>",
  "safe_borrowing_amount": "<string or null>",
  "recommended_banks": ["<string>", "..."],
  "avoid_lenders_warning": "<string or null>",
  "alternative_suggestions": ["<string>", "..."]"""

    return f"""Analyse the financial data below and produce a credit risk assessment.
Use ONLY the data provided. Do NOT make up numbers.

DETECTED ENTITY TYPE: {entity_label}

{metric_instructions}

{eligibility_instructions}
{loan_section}

IMPORTANT — scale awareness:
- If figures are in crore/lakh (Indian institutional reporting), strengths/weaknesses/red_flags
  must reference those real figures (e.g. "Net profit grew to ₹45,997 crore") — never invent
  small personal-finance-scale numbers for a large institution.

---FINANCIAL DATA---
{combined_text}
---END---

Respond in valid JSON (no markdown fences, no extra text):
{{
  "risk_score": <0-100; higher = more risk; e.g. 25 = low risk, 65 = high risk>,
  "risk_level": "<Low|Moderate|High|Critical>",
  "credit_health": "<Excellent|Good|Fair|Poor|Critical>",
  "loan_eligibility": "<value matching the eligibility instructions above>",
  "strengths": [
    "Plain language strength using REAL figures from the data, scaled correctly for this entity type",
    "Strength 2",
    "Strength 3"
  ],
  "weaknesses": [
    "Plain language weakness using REAL figures, scaled correctly for this entity type",
    "Weakness 2",
    "Weakness 3"
  ],
  "red_flags": [
    "Specific red flag with real figures if any — otherwise return an empty list",
    "Red flag 2 if any"
  ],
  "missing_information": [
    "What document or data is missing — e.g. 'No cash flow statement found'",
    "Missing item 2 if any"
  ],
  "debt_to_income_ratio": <number or null — see instructions above>,
  "monthly_income_estimate": <number or null — see instructions above>,
  "monthly_expense_estimate": <number or null — see instructions above>,
  "key_metrics": [
    {{"label": "e.g. Capital Adequacy Ratio", "value": "e.g. 17.2%", "is_good": true}},
    {{"label": "e.g. Gross NPA Ratio", "value": "e.g. 1.3%", "is_good": true}}
  ]{extra_json_fields}
}}"""
