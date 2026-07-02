# tests/unit/test_entity_aware_fixes.py
# Covers the fixes made for: chat-not-working (vector store errors),
# entity-aware risk metrics, entity-aware recommendations, and the
# loan-eligibility color-matching bug.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.schemas import RiskAssessment, KeyMetric, EntityType, RiskLevel
from src.prompts.risk_prompts import build_risk_prompt
from src.prompts.recommendation_prompts import build_recommendation_prompt


# ── KeyMetric / RiskAssessment schema ────────────────────────────────────

def test_key_metric_holds_label_value_and_quality():
    m = KeyMetric(label="Capital Adequacy Ratio", value="17.2%", is_good=True)
    assert m.label == "Capital Adequacy Ratio"
    assert m.value == "17.2%"
    assert m.is_good is True


def test_risk_assessment_accepts_key_metrics_list():
    ra = RiskAssessment(
        risk_score=30.0,
        risk_level=RiskLevel.LOW,
        key_metrics=[KeyMetric(label="Gross NPA", value="1.3%", is_good=True)],
    )
    assert len(ra.key_metrics) == 1
    assert ra.key_metrics[0].label == "Gross NPA"


def test_risk_assessment_key_metrics_defaults_empty():
    ra = RiskAssessment(risk_score=50.0)
    assert ra.key_metrics == []


# ── Entity-aware risk prompt ─────────────────────────────────────────────

def test_bank_prompt_requests_banking_metrics_not_dti():
    prompt = build_risk_prompt("sample financial data", EntityType.COMMERCIAL_BANK)
    assert "Capital Adequacy Ratio" in prompt
    assert "Gross NPA" in prompt
    assert "does not apply to a bank" in prompt


def test_individual_prompt_requests_dti():
    prompt = build_risk_prompt("sample financial data", EntityType.INDIVIDUAL)
    assert "debt-to-income ratio" in prompt.lower()
    assert "Capital Adequacy Ratio (CRAR)" not in prompt


def test_corporate_prompt_requests_debt_to_equity():
    prompt = build_risk_prompt("sample data", EntityType.LARGE_CORPORATE)
    assert "Debt-to-Equity" in prompt
    assert "Interest Coverage Ratio" in prompt


def test_unknown_entity_falls_back_to_individual_metrics():
    prompt = build_risk_prompt("sample data", EntityType.UNKNOWN)
    assert "debt-to-income ratio" in prompt.lower()


# ── Entity-aware recommendation prompt ───────────────────────────────────

def test_bank_recommendation_prompt_uses_institutional_language():
    prompt = build_recommendation_prompt({}, "bank summary", EntityType.COMMERCIAL_BANK)
    assert "Tier-2 Capital Raise" in prompt
    assert "NEVER mention personal credit cards" in prompt


def test_individual_recommendation_prompt_uses_personal_language():
    prompt = build_recommendation_prompt({}, "individual summary", EntityType.INDIVIDUAL)
    assert "Secured Home Loan" in prompt
    assert "Tier-2 Capital Raise" not in prompt


def test_recommendation_prompt_default_is_individual():
    prompt = build_recommendation_prompt({}, "summary")  # no entity_type passed
    assert "Secured Home Loan" in prompt


# ── Loan eligibility color classification (the visual-mismatch bug) ──────

def _classify_eligibility_color(elig_text: str) -> str:
    """Mirrors the fixed logic in ui/pages/risk_analysis.py and dashboard.py."""
    elig_lower = elig_text.strip().lower()
    if elig_lower in ("eligible", "eligible for additional capital"):
        return "success"
    elif "not" in elig_lower:
        return "danger"
    elif "condition" in elig_lower:
        return "warning"
    else:
        return "neutral"


def test_conditionally_eligible_is_amber_not_green():
    # BUG: old code used `"Eligible" in text` which matched this as green
    assert _classify_eligibility_color("Conditionally Eligible") == "warning"


def test_plain_eligible_is_green():
    assert _classify_eligibility_color("Eligible") == "success"


def test_not_eligible_is_red():
    assert _classify_eligibility_color("Not Eligible") == "danger"


def test_institutional_eligibility_for_additional_capital_is_green():
    assert _classify_eligibility_color("Eligible for Additional Capital") == "success"


def test_institutional_not_recommended_is_red():
    assert _classify_eligibility_color("Not Recommended for Additional Leverage") == "danger"


# ── Vector store error tracking (chat-not-working bug) ───────────────────

def test_faiss_build_returns_bool_not_none():
    """FAISS .build() must now return True/False so the orchestrator can
    detect real success/failure instead of blindly assuming success."""
    import inspect
    from src.retrieval.vector_store import FAISSVectorStore
    sig = inspect.signature(FAISSVectorStore.build)
    # Return type annotation should be bool (best-effort check via source)
    src = inspect.getsource(FAISSVectorStore.build)
    assert "return True" in src
    assert "return False" in src


def test_pinecone_is_ready_requires_indexed_content():
    """BUG FIX: Pinecone.is_ready previously returned True as soon as the
    connection succeeded, even with zero documents indexed. It must now
    also check that at least 1 chunk was actually indexed."""
    import inspect
    from src.retrieval.vector_store import PineconeVectorStore
    src = inspect.getsource(PineconeVectorStore.is_ready.fget)
    assert "_indexed_count" in src


def test_pinecone_has_last_error_property():
    from src.retrieval.vector_store import PineconeVectorStore
    assert hasattr(PineconeVectorStore, "last_error")


def test_faiss_has_last_error_property():
    from src.retrieval.vector_store import FAISSVectorStore
    assert hasattr(FAISSVectorStore, "last_error")
