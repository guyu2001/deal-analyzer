import math

import pytest

from calculator import (
    build_scenario_deal,
    calculate_break_even_rent,
    calculate_metrics,
    calculate_monthly_mortgage,
    score_deal,
)
from models import DealInput, DealMetrics


def make_deal(**overrides: float) -> DealInput:
    deal = DealInput(
        purchase_price=350000.0,
        monthly_rent=2500.0,
        down_payment_pct=25.0,
        interest_rate=6.5,
        loan_term_years=30,
        property_tax_annual=4200.0,
        insurance_annual=1200.0,
        maintenance_pct=8.0,
        vacancy_pct=5.0,
        property_management_pct=8.0,
        hoa_monthly=0.0,
        closing_costs=7000.0,
        rehab_cost=5000.0,
    )

    for field_name, value in overrides.items():
        setattr(deal, field_name, value)

    return deal


def test_calculate_monthly_mortgage_returns_zero_for_non_positive_loan_amount() -> None:
    assert calculate_monthly_mortgage(0.0, 6.5, 30) == 0.0
    assert calculate_monthly_mortgage(-100.0, 6.5, 30) == 0.0


def test_calculate_monthly_mortgage_handles_zero_interest() -> None:
    payment = calculate_monthly_mortgage(
        loan_amount=120000.0,
        annual_interest_rate=0.0,
        loan_term_years=30,
    )

    assert payment == 120000.0 / 360


def test_calculate_monthly_mortgage_matches_expected_standard_case() -> None:
    payment = calculate_monthly_mortgage(
        loan_amount=262500.0,
        annual_interest_rate=6.5,
        loan_term_years=30,
    )

    assert payment == pytest.approx(1659.18, abs=0.01)


def test_calculate_metrics_returns_expected_values_for_default_deal() -> None:
    metrics = calculate_metrics(make_deal())

    assert metrics.monthly_mortgage == pytest.approx(1659.18, abs=0.01)
    assert metrics.monthly_cash_flow == pytest.approx(-134.18, abs=0.01)
    assert metrics.annual_cash_flow == pytest.approx(-1610.14, abs=0.01)
    assert metrics.noi_annual == pytest.approx(18300.0, abs=0.01)
    assert metrics.cap_rate == pytest.approx(0.05229, abs=0.00001)
    assert metrics.cash_on_cash_return == pytest.approx(-0.01618, abs=0.00001)
    assert metrics.dscr == pytest.approx(0.91913, abs=0.00001)
    assert metrics.total_cash_invested == pytest.approx(99500.0, abs=0.01)


def test_calculate_metrics_handles_zero_purchase_price_for_cap_rate() -> None:
    metrics = calculate_metrics(
        make_deal(
            purchase_price=0.0,
            monthly_rent=0.0,
            property_tax_annual=0.0,
            insurance_annual=0.0,
            hoa_monthly=0.0,
            closing_costs=1000.0,
            rehab_cost=0.0,
        )
    )

    assert metrics.cap_rate == 0.0


def test_calculate_metrics_handles_zero_cash_invested_for_cash_on_cash_return() -> None:
    metrics = calculate_metrics(
        make_deal(
            purchase_price=0.0,
            monthly_rent=0.0,
            property_tax_annual=0.0,
            insurance_annual=0.0,
            hoa_monthly=0.0,
            closing_costs=0.0,
            rehab_cost=0.0,
        )
    )

    assert metrics.cash_on_cash_return == 0.0


def test_calculate_metrics_handles_zero_debt_service_for_dscr() -> None:
    metrics = calculate_metrics(
        make_deal(
            purchase_price=0.0,
            monthly_rent=2500.0,
            property_tax_annual=4200.0,
            insurance_annual=1200.0,
        )
    )

    assert metrics.monthly_mortgage == 0.0
    assert metrics.dscr == 0.0


def test_calculate_break_even_rent_returns_expected_value() -> None:
    break_even_rent = calculate_break_even_rent(make_deal())

    assert break_even_rent == pytest.approx(2669.85, abs=0.01)


def test_calculate_break_even_rent_returns_infinity_when_variable_expenses_hit_100_percent() -> None:
    break_even_rent = calculate_break_even_rent(
        make_deal(vacancy_pct=40.0, property_management_pct=30.0, maintenance_pct=30.0)
    )

    assert math.isinf(break_even_rent)


def test_build_scenario_deal_applies_adjustments_without_mutating_original() -> None:
    original = make_deal()

    scenario = build_scenario_deal(
        original,
        rent_increase=200.0,
        purchase_price_adjustment=-10000.0,
        interest_rate_change=-0.5,
    )

    assert original.monthly_rent == 2500.0
    assert original.purchase_price == 350000.0
    assert original.interest_rate == 6.5
    assert scenario.monthly_rent == 2700.0
    assert scenario.purchase_price == 340000.0
    assert scenario.interest_rate == 6.0


def test_build_scenario_deal_clamps_negative_values_to_zero() -> None:
    scenario = build_scenario_deal(
        make_deal(),
        rent_increase=-5000.0,
        purchase_price_adjustment=-500000.0,
        interest_rate_change=-10.0,
    )

    assert scenario.monthly_rent == 0.0
    assert scenario.purchase_price == 0.0
    assert scenario.interest_rate == 0.0


def test_score_deal_returns_strong_buy_for_strong_metrics() -> None:
    metrics = DealMetrics(
        monthly_mortgage=1500.0,
        monthly_cash_flow=450.0,
        annual_cash_flow=5400.0,
        noi_annual=24000.0,
        cap_rate=0.07,
        cash_on_cash_return=0.12,
        dscr=1.35,
        total_cash_invested=45000.0,
    )

    grade, verdict, strengths, concerns = score_deal(metrics)

    assert grade == "A"
    assert verdict == "Strong Buy"
    assert "Healthy monthly cash flow" in strengths
    assert concerns == []


def test_score_deal_returns_buy_for_mid_tier_metrics() -> None:
    metrics = DealMetrics(
        monthly_mortgage=1500.0,
        monthly_cash_flow=150.0,
        annual_cash_flow=1800.0,
        noi_annual=22000.0,
        cap_rate=0.065,
        cash_on_cash_return=0.07,
        dscr=1.15,
        total_cash_invested=45000.0,
    )

    grade, verdict, strengths, concerns = score_deal(metrics)

    assert grade == "B"
    assert verdict == "Buy"
    assert "Positive monthly cash flow" in strengths
    assert concerns == []


def test_score_deal_returns_maybe_for_borderline_metrics() -> None:
    metrics = DealMetrics(
        monthly_mortgage=1500.0,
        monthly_cash_flow=150.0,
        annual_cash_flow=1800.0,
        noi_annual=18000.0,
        cap_rate=0.05,
        cash_on_cash_return=0.07,
        dscr=1.15,
        total_cash_invested=45000.0,
    )

    grade, verdict, strengths, concerns = score_deal(metrics)

    assert grade == "C"
    assert verdict == "Maybe"
    assert "Cap rate is on the low side" in concerns
    assert "Adequate debt-service coverage" in strengths


def test_score_deal_returns_pass_for_weak_metrics() -> None:
    metrics = DealMetrics(
        monthly_mortgage=1500.0,
        monthly_cash_flow=-50.0,
        annual_cash_flow=-600.0,
        noi_annual=15000.0,
        cap_rate=0.05,
        cash_on_cash_return=0.03,
        dscr=0.95,
        total_cash_invested=45000.0,
    )

    grade, verdict, strengths, concerns = score_deal(metrics)

    assert grade == "D"
    assert verdict == "Pass"
    assert "Weak or negative monthly cash flow" in concerns
    assert "Low cash-on-cash return" in concerns
