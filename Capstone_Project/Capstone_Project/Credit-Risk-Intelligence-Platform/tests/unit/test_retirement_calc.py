# tests/unit/test_retirement_calc.py
# Tests the retirement corpus calculation math in the orchestrator.
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.schemas import PlatformState, RetirementInput


def make_orchestrator():
    """Import orchestrator without triggering LLM calls."""
    from src.orchestrator.orchestrator import AgentOrchestrator
    return AgentOrchestrator()


def test_corpus_positive():
    """Corpus needed must always be > 0 for valid inputs."""
    orch   = make_orchestrator()
    inputs = RetirementInput(
        current_age=30, planned_retirement_age=50, life_expectancy=80,
        monthly_income=150000, monthly_expenses=80000,
        current_savings=500000, expected_return=14.0, inflation_rate=6.0,
        lifestyle_multiplier=1.0,
    )
    state  = PlatformState()
    # Bypass AI advice by monkeypatching
    orch._chat_agent.generate_retirement_advice = lambda *a, **k: "Mock advice"
    result = orch.calculate_retirement(inputs, state)
    assert result.corpus_needed > 0
    assert result.years_to_retirement == 20
    assert result.post_retirement_years == 30


def test_no_gap_when_savings_exceed_corpus():
    """If savings > corpus needed, gap should be 0 and SIP 0."""
    orch   = make_orchestrator()
    inputs = RetirementInput(
        current_age=50, planned_retirement_age=55, life_expectancy=70,
        monthly_income=500000, monthly_expenses=30000,
        current_savings=100_000_000,  # 10 crore — definitely enough
        expected_return=10.0, inflation_rate=5.0,
        lifestyle_multiplier=1.0,
    )
    state  = PlatformState()
    orch._chat_agent.generate_retirement_advice = lambda *a, **k: "Mock advice"
    result = orch.calculate_retirement(inputs, state)
    assert result.gap == 0.0
    assert result.required_monthly_sip == 0.0
    assert result.is_achievable is True


def test_feasibility_unfeasible_when_sip_exceeds_surplus():
    """High required SIP should mark plan as not achievable."""
    orch   = make_orchestrator()
    inputs = RetirementInput(
        current_age=45, planned_retirement_age=46, life_expectancy=90,
        monthly_income=30000, monthly_expenses=28000,  # only 2000 surplus
        current_savings=0, expected_return=10.0, inflation_rate=6.0,
        lifestyle_multiplier=1.4,  # luxurious
    )
    state  = PlatformState()
    orch._chat_agent.generate_retirement_advice = lambda *a, **k: "Mock advice"
    result = orch.calculate_retirement(inputs, state)
    # Gap will be huge, SIP will vastly exceed surplus
    assert result.is_achievable is False


def test_result_saved_to_state():
    """Calculation result must be saved to platform state."""
    orch   = make_orchestrator()
    inputs = RetirementInput(
        current_age=30, planned_retirement_age=55, life_expectancy=80,
        monthly_income=100000, monthly_expenses=60000,
        current_savings=1000000, expected_return=12.0, inflation_rate=6.0,
        lifestyle_multiplier=1.0,
    )
    state  = PlatformState()
    orch._chat_agent.generate_retirement_advice = lambda *a, **k: "Mock advice"
    result = orch.calculate_retirement(inputs, state)
    assert state.retirement_result is result
    assert state.retirement_input is inputs
