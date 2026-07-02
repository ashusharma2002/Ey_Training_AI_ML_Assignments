# tests/unit/test_loan_workflow.py
# Covers Phase 8/9 (customer loan), Phase 11/13/14 (institution loan),
# and Phase 4 (city-aware retirement calc)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.schemas import (
    LoanContext, LoanType, ApplicantType, PlatformState, RetirementInput,
)
from src.prompts.risk_prompts import build_risk_prompt
from src.prompts.recommendation_prompts import build_recommendation_prompt
from src.models.schemas import EntityType


# ── LoanContext gating (Phase 8/11 "disable Run button until filled") ──

def test_non_loan_application_always_complete():
    lc = LoanContext(is_loan_application=False)
    assert lc.is_complete() is True


def test_loan_application_incomplete_without_amount():
    lc = LoanContext(is_loan_application=True, loan_type=LoanType.HOME)
    assert lc.is_complete() is False


def test_loan_application_incomplete_without_type():
    lc = LoanContext(is_loan_application=True, loan_amount=500000)
    assert lc.is_complete() is False


def test_loan_application_incomplete_with_zero_amount():
    lc = LoanContext(is_loan_application=True, loan_amount=0, loan_type=LoanType.HOME)
    assert lc.is_complete() is False


def test_loan_application_complete_with_amount_and_type():
    lc = LoanContext(is_loan_application=True, loan_amount=500000, loan_type=LoanType.HOME)
    assert lc.is_complete() is True


# ── Risk prompt loan/institution branching ──────────────────────────────

def test_risk_prompt_backward_compatible_without_loan_context():
    prompt = build_risk_prompt("data", EntityType.INDIVIDUAL)
    assert "approval_probability" not in prompt
    assert "risk_category" not in prompt


def test_risk_prompt_customer_loan_adds_phase9_fields():
    lc = LoanContext(is_loan_application=True, loan_amount=500000, loan_type=LoanType.HOME)
    prompt = build_risk_prompt("data", EntityType.INDIVIDUAL, lc, account_type="customer")
    for field in ("approval_probability", "interest_rate_range", "safe_borrowing_amount",
                  "recommended_banks", "avoid_lenders_warning"):
        assert field in prompt


def test_risk_prompt_institution_loan_adds_phase13_fields():
    lc = LoanContext(is_loan_application=True, loan_amount=500000, loan_type=LoanType.HOME,
                      applicant_type=ApplicantType.SALARIED)
    prompt = build_risk_prompt("data", EntityType.INDIVIDUAL, lc, account_type="institution")
    for field in ("risk_category", "repayment_capacity", "default_risk",
                  "fraud_indicators", "confidence_score"):
        assert field in prompt


def test_risk_prompt_no_loan_application_skips_loan_fields_even_with_context_object():
    """LoanContext exists but is_loan_application=False — should behave as if no context."""
    lc = LoanContext(is_loan_application=False)
    prompt = build_risk_prompt("data", EntityType.INDIVIDUAL, lc, account_type="customer")
    assert "approval_probability" not in prompt


# ── Recommendation prompt institution decision branching ───────────────

def test_recommendation_prompt_no_institution_decision_for_customer():
    lc = LoanContext(is_loan_application=True, loan_amount=500000, loan_type=LoanType.HOME)
    prompt = build_recommendation_prompt({}, "summary", EntityType.INDIVIDUAL, lc, account_type="customer")
    assert "institution_decision" not in prompt


def test_recommendation_prompt_institution_decision_present_for_institution():
    lc = LoanContext(is_loan_application=True, loan_amount=500000, loan_type=LoanType.HOME)
    prompt = build_recommendation_prompt({}, "summary", EntityType.INDIVIDUAL, lc, account_type="institution")
    assert "institution_decision" in prompt
    assert "Approve with conditions" in prompt


def test_recommendation_prompt_no_decision_without_loan_application():
    lc = LoanContext(is_loan_application=False)
    prompt = build_recommendation_prompt({}, "summary", EntityType.INDIVIDUAL, lc, account_type="institution")
    assert "institution_decision" not in prompt


# ── PlatformState integration ────────────────────────────────────────────

def test_platform_state_defaults_to_customer():
    state = PlatformState()
    assert state.account_type == "customer"
    assert state.loan_context.is_loan_application is False


def test_platform_state_loan_context_mutable():
    state = PlatformState()
    state.loan_context.is_loan_application = True
    state.loan_context.loan_amount = 750000
    state.loan_context.loan_type = LoanType.VEHICLE
    assert state.loan_context.is_complete() is True


# ── City-aware retirement (Phase 4) backward compatibility ──────────────

def test_retirement_input_city_name_defaults_to_none():
    inp = RetirementInput()
    assert inp.city_name is None


def test_retirement_input_accepts_city_name():
    inp = RetirementInput(city_name="Mumbai")
    assert inp.city_name == "Mumbai"
