# src/prompts/recommendation_prompts.py
# ============================================================
# Entity-aware recommendation prompts.
#
# BUG FIX: Previously this prompt ALWAYS generated personal-borrower
# advice ("reduce credit card debt below ₹50,000", "secured home loan
# ₹25 lakh") regardless of what entity was actually uploaded. A bank
# like HDFC (assets in lakh-crore) got individual retail-loan tips —
# nonsensical and unusable.
#
# Now the prompt branches by entity type so a bank/NBFC/corporate gets
# institutional-scale advice (capital strategy, NPA management, balance
# sheet optimisation) instead of personal credit-card tips.
# ============================================================
from __future__ import annotations
from src.models.schemas import EntityType

RECOMMENDATION_SYSTEM_PROMPT = (
    "You are a friendly financial advisor giving personalised, practical advice. "
    "Use simple, encouraging language. Focus on what the entity CAN do, not just problems. "
    "Every recommendation should be specific and actionable — no vague advice. "
    "CRITICAL: Match every number, amount, and suggestion to the ACTUAL SCALE of the entity in "
    "the data. A bank with ₹10 lakh crore in assets must NEVER receive personal-loan-scale advice "
    "(e.g. 'reduce credit card debt to ₹50,000') — that is meaningless and wrong for an institution. "
    "Likewise an individual must never receive institutional advice about capital adequacy ratios."
)

RETIREMENT_SYSTEM_PROMPT = (
    "You are a retirement planning expert helping someone plan their early retirement. "
    "Use encouraging, simple language. Show them realistic steps they can take right now. "
    "Be honest about challenges but focus on solutions."
)

_INSTITUTIONAL_TYPES = (
    EntityType.COMMERCIAL_BANK,
    EntityType.NBFC,
    EntityType.LARGE_CORPORATE,
    EntityType.SME,
)


def _is_institutional(entity_type: EntityType) -> bool:
    return entity_type in _INSTITUTIONAL_TYPES


def _entity_guidance(entity_type: EntityType) -> str:
    if entity_type in (EntityType.COMMERCIAL_BANK, EntityType.NBFC):
        return """This is a BANK / NBFC. ALL recommendations must be institutional-scale:
  - credit_improvement_checklist → capital & risk-management actions
    (e.g. "Reduce gross NPA from 1.3% toward 1.0% by tightening underwriting on retail loans",
     "Maintain Capital Adequacy Ratio above 11.5% RBI minimum with a buffer of 2-3%")
  - alternative_loan_suggestions → reinterpret as CAPITAL / FUNDING STRATEGIES the bank could
    pursue (e.g. loan_type="Tier-2 Capital Raise via Bonds", amount="₹5,000 crore",
    interest_rate_range="Target coupon 7.5-8.5%", rationale="...")
  - safer_loan_amount → reinterpret as a RECOMMENDED CAPITAL BUFFER or safe additional
    leverage figure in crore (e.g. "₹2,000 crore additional Tier-1 capital recommended")
  - financial_recommendations → balance sheet optimisation, NPA management, deposit growth,
    regulatory compliance — all in crore-scale figures matching the data provided
  - NEVER mention personal credit cards, personal loans, individual EMIs, or lakh-scale
    amounts unless the underlying data is genuinely that small."""

    if entity_type in (EntityType.LARGE_CORPORATE, EntityType.SME):
        return """This is a CORPORATE / BUSINESS entity. ALL recommendations must be business-scale:
  - credit_improvement_checklist → corporate financial health actions
    (e.g. "Reduce debt-to-equity from 1.8 to below 1.5 by retaining more earnings")
  - alternative_loan_suggestions → reinterpret as BUSINESS FINANCING OPTIONS
    (e.g. loan_type="Working Capital Facility", amount matching the entity's actual revenue scale)
  - safer_loan_amount → a safe additional borrowing capacity matching the entity's real scale
  - NEVER suggest personal credit cards, personal loans, or individual-scale amounts."""

    # Individual / Unknown — keep original personal-finance advice
    return """This is an INDIVIDUAL / personal borrower. Use personal-finance-scale advice:
  - credit_improvement_checklist → personal credit actions (credit cards, on-time payments)
  - alternative_loan_suggestions → personal/retail loan options (home loan, personal loan, etc.)
  - safer_loan_amount → a safe personal loan amount based on their income"""


def _institution_decision_instructions(risk_assessment: dict) -> str:
    """Phase 14 — Institution AI Recommendations: lender decision framework."""
    return """
INSTITUTION LOAN DECISION (Phase 14 — you are advising a loan officer):
Based on the risk assessment above, provide a concrete lending decision.
Additionally provide:
  - institution_decision: EXACTLY one of: "Approve", "Approve with conditions",
    "Request additional documents", "Reduce loan amount", "Require collateral",
    "Recommend guarantor", "Reject with explanation"
  - institution_decision_reasoning: 1-2 sentences explaining WHY, citing specific evidence
  - institution_conditions: if decision is "Approve with conditions", list the specific
    conditions (e.g. "Provide 6 months of additional bank statements"); empty list otherwise
  - applicant_improvement_tips: 2-4 evidence-based, actionable tips for the APPLICANT to
    improve their profile (e.g. "Clear ₹45,000 outstanding credit card balance",
    "Reduce active loan count from 3 to 2 before reapplying") — must be evidence-based,
    never generic advice not supported by the data"""


def build_recommendation_prompt(
    risk_assessment: dict,
    summary_texts:   str,
    entity_type:     EntityType = EntityType.UNKNOWN,
    loan_context     = None,    # LoanContext | None — Phase 8/11
    account_type:    str = "customer",
) -> str:
    guidance = _entity_guidance(entity_type)
    label_loan_type   = "Strategy / Instrument" if _is_institutional(entity_type) else "Loan Type"
    label_safer_field = "Recommended Capital Buffer" if _is_institutional(entity_type) else "Safer Loan Amount"

    institution_section = ""
    institution_json_fields = ""
    if account_type == "institution" and loan_context and loan_context.is_loan_application:
        institution_section = _institution_decision_instructions(risk_assessment)
        institution_json_fields = """,
  "institution_decision": "<one of the 7 allowed values above>",
  "institution_decision_reasoning": "<string>",
  "institution_conditions": ["<string>", "..."],
  "applicant_improvement_tips": ["<string>", "..."]"""

    return f"""Generate personalised financial recommendations based on this assessment.

DETECTED ENTITY TYPE: {entity_type.value}

{guidance}
{institution_section}

RISK ASSESSMENT:
{risk_assessment}

FINANCIAL SUMMARY:
{summary_texts[:4000]}

RULES:
- Use simple, friendly language
- Make every recommendation specific and actionable (not vague like "improve credit")
- Include realistic timelines where possible
- Sort actions by urgency: what to do THIS WEEK vs this month vs this year
- Every number/amount MUST match the scale of the entity above — re-read the financial
  summary and use figures consistent with what's actually there (crore for a large bank,
  lakh/thousands for an individual)

Respond in valid JSON (no markdown fences):
{{
  "credit_improvement_checklist": [
    "Specific action 1 matching entity scale and type",
    "Specific action 2",
    "Specific action 3",
    "Specific action 4",
    "Specific action 5"
  ],
  "alternative_loan_suggestions": [
    {{
      "loan_type": "e.g. {('Tier-2 Capital Raise' if _is_institutional(entity_type) else 'Secured Home Loan')}",
      "amount": "amount matching entity scale (crore for institutions, lakh for individuals)",
      "interest_rate_range": "realistic range for this type of instrument",
      "rationale": "Why this fits their profile in 1 sentence",
      "urgency": "High|Medium|Low"
    }}
  ],
  "financial_recommendations": [
    "Plain language recommendation 1 matching entity scale",
    "Recommendation 2",
    "Recommendation 3"
  ],
  "safer_loan_amount": "{label_safer_field} matching entity scale, e.g. value + 1-sentence reason",
  "next_best_actions": [
    "THIS WEEK: One urgent action",
    "THIS MONTH: One medium-term action",
    "THIS YEAR: One longer-term action"
  ],
  "risk_simulator_data": [
    {{"year": 1, "risk_score": 55, "action": "After first improvement action"}},
    {{"year": 2, "risk_score": 45, "action": "After second improvement action"}},
    {{"year": 3, "risk_score": 35, "action": "After consistent improvement"}}
  ],
  "urgency_sorted_actions": [
    {{"action": "Action description", "urgency": "High", "timeline": "This week", "impact": "Expected effect"}},
    {{"action": "Action 2", "urgency": "Medium", "timeline": "This month", "impact": "Expected effect"}},
    {{"action": "Action 3", "urgency": "Low", "timeline": "3-6 months", "impact": "Expected effect"}}
  ]{institution_json_fields}
}}"""


def build_retirement_prompt(inputs: dict, calculation: dict) -> str:
    return f"""Help this person plan for early retirement. Be encouraging and specific.

THEIR FINANCIAL SITUATION:
{inputs}

CALCULATION RESULTS:
{calculation}

Write a personalised retirement plan analysis. Be honest but encouraging.
Focus on: Is this achievable? What are the 3 most important actions they should take?

Respond in valid JSON (no markdown fences):
{{
  "summary": "3-4 sentences: Is early retirement at [age] achievable? What is the key challenge? What is the biggest opportunity? Use plain language, no jargon.",
  "key_message": "One sentence: the single most important thing they need to know about their retirement plan",
  "action_steps": [
    "Step 1: Most important action with specific number — e.g. 'Start a monthly SIP of ₹25,000 in a diversified equity mutual fund today'",
    "Step 2: Second most important action",
    "Step 3: Third action"
  ],
  "encouragement": "One sentence of genuine, realistic encouragement based on their actual situation"
}}"""
