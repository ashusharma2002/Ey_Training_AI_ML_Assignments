# tests/unit/test_schemas.py
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.schemas import (
    PlatformState, RetirementInput, RetirementResult,
    RiskAssessment, RiskLevel, ProcessingStatus, DocumentMetadata
)


def test_platform_state_defaults():
    s = PlatformState()
    assert s.total_documents() == 0
    assert s.processed_count() == 0
    assert s.vector_store_ready is False
    assert s.chat_history == []


def test_processed_count():
    from src.models.schemas import DocumentType
    s = PlatformState()
    m1 = DocumentMetadata(
        file_name="a.pdf", file_size_kb=100,
        processing_status=ProcessingStatus.COMPLETE
    )
    m2 = DocumentMetadata(
        file_name="b.pdf", file_size_kb=200,
        processing_status=ProcessingStatus.FAILED
    )
    s.documents.extend([m1, m2])
    assert s.total_documents() == 2
    assert s.processed_count() == 1


def test_risk_assessment_score_bounds():
    ra = RiskAssessment(risk_score=75.0, risk_level=RiskLevel.HIGH)
    assert 0 <= ra.risk_score <= 100


def test_risk_level_enum():
    for level in ("Low", "Moderate", "High", "Critical"):
        rl = RiskLevel(level)
        assert rl.value == level


def test_retirement_input_defaults():
    ri = RetirementInput()
    assert ri.current_age == 30
    assert ri.planned_retirement_age == 50
    assert ri.expected_return == 14.0


def test_retirement_result_is_achievable():
    r = RetirementResult(
        corpus_needed=10_000_000,
        current_savings_fv=5_000_000,
        gap=5_000_000,
        required_monthly_sip=10_000,
        total_sip_needed=10_000,
        years_to_retirement=20,
        future_monthly_expenses=50_000,
        post_retirement_years=30,
        is_achievable=True,
        feasibility_pct=40.0,
    )
    assert r.is_achievable is True
    assert r.feasibility_pct == 40.0
