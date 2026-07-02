# src/models/schemas.py
# ============================================================
# Pydantic v2 data models — single source of truth for all
# data structures used across agents, API, and UI.
# ============================================================
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


# ── Enumerations ─────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW      = "Low"
    MODERATE = "Moderate"
    HIGH     = "High"
    CRITICAL = "Critical"


class DocumentType(str, Enum):
    BANK_STATEMENT = "Bank Statement"
    ITR            = "Income Tax Return"
    BALANCE_SHEET  = "Balance Sheet"
    PNL            = "Profit & Loss Statement"
    ANNUAL_REPORT  = "Annual Report"
    UNKNOWN        = "Unknown"


class ProcessingStatus(str, Enum):
    PENDING    = "Pending"
    PROCESSING = "Processing"
    COMPLETE   = "Complete"
    FAILED     = "Failed"


class EntityType(str, Enum):
    COMMERCIAL_BANK = "Commercial Bank"
    NBFC            = "NBFC / Financial Institution"
    LARGE_CORPORATE = "Large Corporate"
    SME             = "SME / Small Business"
    INDIVIDUAL      = "Individual / Borrower"
    UNKNOWN         = "Unknown"


# ── Document Models ──────────────────────────────────────────────────────────

class DocumentMetadata(BaseModel):
    file_name:          str
    file_size_kb:       float
    document_type:      DocumentType    = DocumentType.UNKNOWN
    page_count:         int             = 0
    upload_timestamp:   datetime        = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_status:  ProcessingStatus = ProcessingStatus.PENDING
    error_message:      str | None      = None


class DocumentSummary(BaseModel):
    file_name:           str
    executive_summary:   str       = ""
    financial_overview:  str       = ""
    key_insights:        list[str] = Field(default_factory=list)
    income_summary:      str       = ""
    expense_summary:     str       = ""
    assets_summary:      str       = ""
    liabilities_summary: str       = ""
    cash_flow_summary:   str       = ""
    raw_extracted_text:  str       = ""
    generated_at:        datetime  = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Combined Summary ─────────────────────────────────────────────────────────

class CombinedSummary(BaseModel):
    executive_overview:    str = ""
    financial_position:    str = ""
    income_profitability:  str = ""
    key_strengths:         list[str] = Field(default_factory=list)
    areas_of_concern:      list[str] = Field(default_factory=list)
    overall_assessment:    str = ""
    entity_type:           EntityType = EntityType.UNKNOWN
    documents_covered:     list[str]  = Field(default_factory=list)
    generated_at:          datetime   = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Dynamic Questions ────────────────────────────────────────────────────────

class QuestionSet(BaseModel):
    entity_type:       EntityType = EntityType.UNKNOWN
    document_types:    list[str]  = Field(default_factory=list)
    analyst_questions: list[str]  = Field(default_factory=list)
    entity_questions:  list[str]  = Field(default_factory=list)
    generated_at:      datetime   = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_generated:      bool       = False
    is_validated:      bool       = False  # True = questions pre-checked against RAG


# ── Risk Models ──────────────────────────────────────────────────────────────

class KeyMetric(BaseModel):
    """A single entity-appropriate headline metric for the 4th KPI card.
    e.g. {label: 'Capital Adequacy Ratio', value: '17.2%', is_good: true}
    """
    label:   str
    value:   str
    is_good: bool | None = None   # drives green/amber/red coloring in UI


class LoanType(str, Enum):
    PERSONAL  = "Personal Loan"
    HOME      = "Home Loan"
    BUSINESS  = "Business Loan"
    EDUCATION = "Education Loan"
    VEHICLE   = "Vehicle Loan"
    GOLD      = "Gold Loan"
    OTHER     = "Other"


class ApplicantType(str, Enum):
    SALARIED = "Salaried"
    BUSINESS = "Business"


class LoanContext(BaseModel):
    """
    Captures loan-application context (Phase 8 customer / Phase 11
    institution). When is_loan_application is False, every downstream
    module behaves exactly as before this feature existed — this is
    the backward-compatible default path.
    """
    is_loan_application: bool = False
    loan_amount:          float | None = None
    loan_type:             LoanType | None = None
    applicant_type:        ApplicantType | None = None   # institution-side only

    def is_complete(self) -> bool:
        """Used to gate the Run button — disabled until filled, per requirement."""
        if not self.is_loan_application:
            return True
        return self.loan_amount is not None and self.loan_amount > 0 and self.loan_type is not None


class MissingDocumentAlert(BaseModel):
    """One missing-document warning shown in the Phase 15 popup."""
    item:       str
    why_needed: str
    severity:   str = "Medium"


class RiskAssessment(BaseModel):
    risk_score:               float       = Field(ge=0.0, le=100.0, default=0.0)
    risk_level:               RiskLevel   = RiskLevel.MODERATE
    credit_health:            str         = "Unknown"
    loan_eligibility:         str         = "Under Review"
    strengths:                list[str]   = Field(default_factory=list)
    weaknesses:               list[str]   = Field(default_factory=list)
    red_flags:                list[str]   = Field(default_factory=list)
    missing_information:      list[str]   = Field(default_factory=list)
    debt_to_income_ratio:     float | None = None   # individuals only
    monthly_income_estimate:  float | None = None   # individuals only
    monthly_expense_estimate: float | None = None   # individuals only
    # BUG FIX: previously DTI was shown for every entity type, even banks,
    # producing a meaningless "N/A" card. key_metrics now holds the
    # entity-appropriate headline figure (CRAR/NPA for banks, D/E for
    # corporates, DTI for individuals) so the 4th KPI card is always real.
    key_metrics:              list[KeyMetric] = Field(default_factory=list)

    # ── Phase 9 — Enhanced Customer Risk Analysis (loan-aware) ───────
    approval_probability:     str | None = None
    interest_rate_range:      str | None = None
    best_loan_type:            str | None = None
    affordable_emi:            str | None = None
    safe_borrowing_amount:     str | None = None
    recommended_banks:         list[str]  = Field(default_factory=list)
    avoid_lenders_warning:     str | None = None
    alternative_suggestions:   list[str]  = Field(default_factory=list)

    # ── Phase 13 — Institution Risk Analysis (lender-focused) ────────
    risk_category:             str | None = None
    repayment_capacity:        str | None = None
    income_stability:          str | None = None
    credit_history_summary:    str | None = None
    default_risk:              str | None = None
    fraud_indicators:          list[str]  = Field(default_factory=list)
    confidence_score:          float | None = None

    assessed_at:              datetime    = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Recommendation Models ────────────────────────────────────────────────────

class LoanSuggestion(BaseModel):
    loan_type:           str
    amount:              str
    interest_rate_range: str
    rationale:           str
    urgency:             str = "Medium"  # High / Medium / Low


class AIRecommendations(BaseModel):
    credit_improvement_checklist:  list[str]          = Field(default_factory=list)
    alternative_loan_suggestions:  list[LoanSuggestion] = Field(default_factory=list)
    financial_recommendations:     list[str]          = Field(default_factory=list)
    safer_loan_amount:             str                = ""
    next_best_actions:             list[str]          = Field(default_factory=list)
    risk_simulator_data:           list[dict]         = Field(default_factory=list)
    urgency_sorted_actions:        list[dict]         = Field(default_factory=list)

    # ── Phase 14 — Institution AI Recommendations (lender decision) ──
    institution_decision:           str | None = None   # Approve / Approve with conditions / Reject / etc
    institution_decision_reasoning: str | None = None
    institution_conditions:         list[str]  = Field(default_factory=list)  # if "Approve with conditions"
    applicant_improvement_tips:     list[str]  = Field(default_factory=list)  # evidence-based tips for the applicant

    generated_at:                  datetime           = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Chat Models ──────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role:       str       # "user" | "assistant"
    content:    str
    sources:    list[str] = Field(default_factory=list)
    timestamp:  datetime  = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Retirement Planner Models ────────────────────────────────────────────────

class RetirementInput(BaseModel):
    """User inputs for the Early Retirement Planner."""
    current_age:           int   = 30
    planned_retirement_age: int  = 50
    life_expectancy:       int   = 80

    monthly_income:        float = 0.0
    monthly_expenses:      float = 0.0
    current_savings:       float = 0.0
    current_sip:           float = 0.0   # existing monthly SIP/investment

    total_assets:          float = 0.0
    total_liabilities:     float = 0.0

    expected_return:       float = 14.0  # % annual
    inflation_rate:        float = 6.0   # % annual
    emergency_fund_months: int   = 6

    lifestyle_goal: str = "Comfortable"  # Minimal / Comfortable / Luxurious
    lifestyle_multiplier: float = 1.0    # 0.7 Minimal / 1.0 Comfortable / 1.4 Luxurious

    # Phase 4 — City-aware retirement planning
    city_name: str | None = None   # e.g. "Mumbai" — None = use generic national average

    # Extracted from documents?
    auto_extracted: bool = False


class RetirementResult(BaseModel):
    """Calculated retirement planning results."""
    # Core numbers
    corpus_needed:            float = 0.0   # Total corpus required at retirement
    current_savings_fv:       float = 0.0   # Current savings grown to retirement date
    gap:                      float = 0.0   # corpus_needed - current_savings_fv
    required_monthly_sip:     float = 0.0   # Monthly SIP needed to close the gap
    total_sip_needed:         float = 0.0   # required_monthly_sip + current_sip

    # Context
    years_to_retirement:      int   = 0
    future_monthly_expenses:  float = 0.0   # inflation-adjusted monthly expenses at retirement
    post_retirement_years:    int   = 0

    # Assessment
    is_achievable:            bool  = False
    feasibility_pct:          float = 0.0   # % of SIP needed vs available surplus
    ai_summary:               str   = ""    # Plain-language AI-generated advice
    action_steps:             list[str] = Field(default_factory=list)

    # Phase 4 — City-aware breakdown (None if no city was selected)
    city_name:                 str | None = None
    city_cost_of_living_index: float | None = None
    city_adjusted_inflation:   float | None = None
    estimated_housing_expense:  float | None = None
    estimated_healthcare_expense: float | None = None

    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Platform State ───────────────────────────────────────────────────────────

class PlatformState(BaseModel):
    documents:           list[DocumentMetadata]    = Field(default_factory=list)
    summaries:           dict[str, DocumentSummary] = Field(default_factory=dict)
    combined_summary:    CombinedSummary | None    = None
    suggested_questions: QuestionSet               = Field(default_factory=QuestionSet)
    risk_assessment:     RiskAssessment | None     = None
    recommendations:     AIRecommendations | None  = None
    chat_history:        list[ChatMessage]         = Field(default_factory=list)
    vector_store_ready:  bool                      = False
    retirement_input:    RetirementInput | None    = None
    retirement_result:   RetirementResult | None   = None

    # ── Phase 7/8/11 — Auth + Loan workflow context ──────────────────
    account_type:              str               = "customer"   # "customer" | "institution"
    loan_context:              LoanContext       = Field(default_factory=LoanContext)
    missing_document_alerts:   list[MissingDocumentAlert] = Field(default_factory=list)
    institution_summary:       dict | None       = None  # Phase 12 structured executive summary

    last_updated:        datetime                  = Field(default_factory=lambda: datetime.now(timezone.utc))

    def total_documents(self) -> int:
        return len(self.documents)

    def processed_count(self) -> int:
        return sum(
            1 for d in self.documents
            if d.processing_status == ProcessingStatus.COMPLETE
        )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
