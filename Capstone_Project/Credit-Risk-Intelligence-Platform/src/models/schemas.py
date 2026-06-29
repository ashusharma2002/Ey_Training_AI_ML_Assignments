# src/models/schemas.py
# ============================================================
# Pydantic v2 data models — single source of truth.
# Updated: added combined_summary + suggested_questions
# ============================================================
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


# ── Enumerations ──────────────────────────────────────────────────────────────

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
    """Detected type of the entity that filed the documents."""
    COMMERCIAL_BANK = "Commercial Bank"
    NBFC            = "NBFC / Financial Institution"
    LARGE_CORPORATE = "Large Corporate"
    SME             = "SME / Small Business"
    INDIVIDUAL      = "Individual / Borrower"
    UNKNOWN         = "Unknown"


# ── Document Models ───────────────────────────────────────────────────────────

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
    executive_summary:   str        = ""
    financial_overview:  str        = ""
    key_insights:        list[str]  = Field(default_factory=list)
    income_summary:      str        = ""
    expense_summary:     str        = ""
    assets_summary:      str        = ""
    liabilities_summary: str        = ""
    cash_flow_summary:   str        = ""
    raw_extracted_text:  str        = ""
    generated_at:        datetime   = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Combined Summary ──────────────────────────────────────────────────────────

class CombinedSummary(BaseModel):
    """
    AI-generated narrative summary across ALL uploaded documents.
    Generated once after all documents are processed.
    """
    executive_overview:    str = ""
    financial_position:    str = ""
    income_profitability:  str = ""
    key_strengths:         list[str] = Field(default_factory=list)
    areas_of_concern:      list[str] = Field(default_factory=list)
    overall_assessment:    str = ""
    entity_type:           EntityType = EntityType.UNKNOWN
    documents_covered:     list[str] = Field(default_factory=list)
    generated_at:          datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Dynamic Questions ─────────────────────────────────────────────────────────

class QuestionSet(BaseModel):
    """
    Dynamically generated questions based on uploaded documents.
    Replaces hardcoded BANK_PROMPTS / BORROWER_PROMPTS.
    """
    entity_type:        EntityType       = EntityType.UNKNOWN
    document_types:     list[str]        = Field(default_factory=list)
    analyst_questions:  list[str]        = Field(default_factory=list)
    entity_questions:   list[str]        = Field(default_factory=list)
    generated_at:       datetime         = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_generated:       bool             = False


# ── Risk Models ───────────────────────────────────────────────────────────────

class RiskAssessment(BaseModel):
    risk_score:               float       = Field(ge=0.0, le=100.0, default=0.0)
    risk_level:               RiskLevel   = RiskLevel.MODERATE
    credit_health:            str         = "Unknown"
    loan_eligibility:         str         = "Under Review"
    strengths:                list[str]   = Field(default_factory=list)
    weaknesses:               list[str]   = Field(default_factory=list)
    red_flags:                list[str]   = Field(default_factory=list)
    missing_information:      list[str]   = Field(default_factory=list)
    debt_to_income_ratio:     float | None = None
    monthly_income_estimate:  float | None = None
    monthly_expense_estimate: float | None = None
    assessed_at:              datetime    = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Recommendation Models ─────────────────────────────────────────────────────

class LoanSuggestion(BaseModel):
    loan_type:           str
    amount:              str
    interest_rate_range: str
    rationale:           str


class AIRecommendations(BaseModel):
    credit_improvement_checklist:  list[str]          = Field(default_factory=list)
    alternative_loan_suggestions:  list[LoanSuggestion] = Field(default_factory=list)
    financial_recommendations:     list[str]          = Field(default_factory=list)
    safer_loan_amount:             str                = ""
    next_best_actions:             list[str]          = Field(default_factory=list)
    generated_at:                  datetime           = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Chat Models ───────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role:      str           # "user" | "assistant"
    content:   str
    sources:   list[str]     = Field(default_factory=list)
    timestamp: datetime      = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Platform State ────────────────────────────────────────────────────────────

class PlatformState(BaseModel):
    documents:           list[DocumentMetadata]      = Field(default_factory=list)
    summaries:           dict[str, DocumentSummary]  = Field(default_factory=dict)
    combined_summary:    CombinedSummary | None      = None
    suggested_questions: QuestionSet                 = Field(default_factory=QuestionSet)
    risk_assessment:     RiskAssessment | None       = None
    recommendations:     AIRecommendations | None    = None
    chat_history:        list[ChatMessage]           = Field(default_factory=list)
    vector_store_ready:  bool                        = False
    last_updated:        datetime                    = Field(default_factory=lambda: datetime.now(timezone.utc))

    def total_documents(self) -> int:
        return len(self.documents)

    def processed_count(self) -> int:
        return sum(
            1 for d in self.documents
            if d.processing_status == ProcessingStatus.COMPLETE
        )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
