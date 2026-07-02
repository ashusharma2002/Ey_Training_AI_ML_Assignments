# tests/unit/test_city_and_validator.py
# Covers Phase 4 — Retirement city feature, Phase 15 — Missing document detection
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.retirement.city_data import search_cities, get_city_data, all_city_names
from src.orchestrator.document_validator import detect_missing_documents
from src.models.schemas import LoanContext, LoanType


# ── City data ──────────────────────────────────────────────────────────

def test_city_dataset_loads():
    assert len(all_city_names()) > 0


def test_search_cities_partial_match():
    results = search_cities("mum")
    assert "Mumbai" in results


def test_search_cities_no_match_returns_empty():
    assert search_cities("zzznotacity") == []


def test_search_cities_empty_query_returns_some_results():
    results = search_cities("", limit=5)
    assert len(results) == 5


def test_get_city_data_returns_valid_fields():
    city = get_city_data("Mumbai")
    assert city is not None
    assert city.cost_of_living_index > 0
    assert city.housing_multiplier > 0
    assert 0 < city.local_inflation_pct < 20


def test_get_city_data_unknown_city_returns_none():
    assert get_city_data("Definitely Not A Real City") is None


def test_expensive_city_has_higher_cost_index_than_cheap_city():
    mumbai = get_city_data("Mumbai")
    patna  = get_city_data("Patna")
    assert mumbai.cost_of_living_index > patna.cost_of_living_index


# ── Missing document detection ────────────────────────────────────────

def test_detects_all_missing_when_text_is_empty():
    alerts = detect_missing_documents("", LoanContext())
    assert len(alerts) >= 5  # most/all checks should fire on truly empty text


def test_no_alerts_for_item_present_in_text():
    text = "Monthly salary is 50000 as per bank statement."
    alerts = detect_missing_documents(text, LoanContext())
    items = [a.item for a in alerts]
    assert "Income Proof" not in items
    assert "Bank Statement" not in items


def test_loan_application_without_amount_flags_it():
    lc = LoanContext(is_loan_application=True)
    alerts = detect_missing_documents("some text", lc)
    items = [a.item for a in alerts]
    assert "Loan Amount" in items
    assert "Loan Type" in items


def test_loan_application_with_complete_details_does_not_flag_loan_fields():
    lc = LoanContext(is_loan_application=True, loan_amount=500000, loan_type=LoanType.HOME)
    alerts = detect_missing_documents("some text", lc)
    items = [a.item for a in alerts]
    assert "Loan Amount" not in items
    assert "Loan Type" not in items


def test_non_loan_application_never_flags_loan_fields():
    lc = LoanContext(is_loan_application=False)
    alerts = detect_missing_documents("", lc)
    items = [a.item for a in alerts]
    assert "Loan Amount" not in items
    assert "Loan Type" not in items


def test_alerts_have_severity_and_explanation():
    alerts = detect_missing_documents("", LoanContext())
    for a in alerts:
        assert a.severity in ("High", "Medium", "Low")
        assert len(a.why_needed) > 10  # must have a real explanation, not blank
