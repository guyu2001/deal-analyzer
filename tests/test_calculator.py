import math

import pytest

from calculator import (
    ScoringConfig,
    build_scenario_deal,
    calculate_break_even_rent,
    calculate_metrics,
    calculate_monthly_mortgage,
    score_deal,
    score_deal_detailed,
)


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


def test_calculate_monthly_mortgage_handles_short_term_loans() -> None:
    payment = calculate_monthly_mortgage(
        loan_amount=120000.0,
        annual_interest_rate=12.0,
        loan_term_years=1,
    )

    assert payment == pytest.approx(10661.85, abs=0.01)


def test_calculate_metrics_returns_expected_values_for_default_deal(make_deal) -> None:
    metrics = calculate_metrics(make_deal())

    assert metrics.monthly_mortgage == pytest.approx(1659.18, abs=0.01)
    assert metrics.monthly_cash_flow == pytest.approx(-134.18, abs=0.01)
    assert metrics.annual_cash_flow == pytest.approx(-1610.14, abs=0.01)
    assert metrics.noi_annual == pytest.approx(18300.0, abs=0.01)
    assert metrics.cap_rate == pytest.approx(0.05229, abs=0.00001)
    assert metrics.cash_on_cash_return == pytest.approx(-0.01618, abs=0.00001)
    assert metrics.dscr == pytest.approx(0.91913, abs=0.00001)
    assert metrics.total_cash_invested == pytest.approx(99500.0, abs=0.01)


def test_calculate_metrics_handles_zero_purchase_price_for_cap_rate(make_deal) -> None:
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


def test_calculate_metrics_handles_zero_cash_invested_for_cash_on_cash_return(make_deal) -> None:
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


def test_calculate_metrics_handles_zero_debt_service_for_dscr(make_deal) -> None:
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


def test_calculate_break_even_rent_returns_expected_value(make_deal) -> None:
    break_even_rent = calculate_break_even_rent(make_deal())

    assert break_even_rent == pytest.approx(2669.85, abs=0.01)


def test_calculate_break_even_rent_returns_infinity_when_variable_expenses_hit_100_percent(make_deal) -> None:
    break_even_rent = calculate_break_even_rent(
        make_deal(vacancy_pct=40.0, property_management_pct=30.0, maintenance_pct=30.0)
    )

    assert math.isinf(break_even_rent)


def test_calculate_break_even_rent_handles_zero_mortgage_cash_purchase(make_deal) -> None:
    break_even_rent = calculate_break_even_rent(
        make_deal(
            purchase_price=0.0,
            down_payment_pct=0.0,
            property_tax_annual=2400.0,
            insurance_annual=1200.0,
            maintenance_pct=10.0,
            vacancy_pct=5.0,
            property_management_pct=5.0,
            hoa_monthly=100.0,
        )
    )

    assert break_even_rent == pytest.approx(500.0, abs=0.01)


def test_build_scenario_deal_applies_adjustments_without_mutating_original(make_deal) -> None:
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


def test_build_scenario_deal_clamps_negative_values_to_zero(make_deal) -> None:
    scenario = build_scenario_deal(
        make_deal(),
        rent_increase=-5000.0,
        purchase_price_adjustment=-500000.0,
        interest_rate_change=-10.0,
    )

    assert scenario.monthly_rent == 0.0
    assert scenario.purchase_price == 0.0
    assert scenario.interest_rate == 0.0


def test_build_scenario_deal_with_no_adjustments_returns_same_values(make_deal) -> None:
    original = make_deal()

    scenario = build_scenario_deal(original)

    assert scenario.monthly_rent == pytest.approx(original.monthly_rent)
    assert scenario.purchase_price == pytest.approx(original.purchase_price)
    assert scenario.interest_rate == pytest.approx(original.interest_rate)


def test_scenario_analysis_changes_metrics_consistently(make_deal) -> None:
    original = make_deal()
    scenario = build_scenario_deal(
        original,
        rent_increase=200.0,
        purchase_price_adjustment=-10000.0,
        interest_rate_change=-0.5,
    )

    original_metrics = calculate_metrics(original)
    scenario_metrics = calculate_metrics(scenario)

    assert scenario_metrics.monthly_cash_flow == pytest.approx(154.15, abs=0.01)
    assert scenario_metrics.annual_cash_flow == pytest.approx(1849.75, abs=0.01)
    assert scenario_metrics.cash_on_cash_return == pytest.approx(0.01907, abs=0.00001)
    assert scenario_metrics.dscr == pytest.approx(1.10082, abs=0.00001)
    assert scenario_metrics.monthly_cash_flow > original_metrics.monthly_cash_flow
    assert scenario_metrics.dscr > original_metrics.dscr


def test_score_deal_returns_strong_buy_for_strong_metrics(make_metrics) -> None:
    metrics = make_metrics(
        monthly_cash_flow=450.0,
        annual_cash_flow=5400.0,
        noi_annual=24000.0,
        cap_rate=0.07,
        cash_on_cash_return=0.12,
        dscr=1.35,
    )

    grade, verdict, strengths, concerns = score_deal(metrics)

    assert grade == "A"
    assert verdict == "Strong Buy"
    assert "Healthy monthly cash flow" in strengths
    assert concerns == []


def test_score_deal_returns_buy_for_mid_tier_metrics(make_metrics) -> None:
    metrics = make_metrics()

    grade, verdict, strengths, concerns = score_deal(metrics)

    assert grade == "B"
    assert verdict == "Buy"
    assert "Positive monthly cash flow" in strengths
    assert concerns == []


def test_score_deal_returns_maybe_for_borderline_metrics(make_metrics) -> None:
    metrics = make_metrics(noi_annual=18000.0, cap_rate=0.05)

    grade, verdict, strengths, concerns = score_deal(metrics)

    assert grade == "C"
    assert verdict == "Maybe"
    assert "Cap rate is on the low side" in concerns
    assert "Adequate debt-service coverage" in strengths


def test_score_deal_returns_pass_for_weak_metrics(make_metrics) -> None:
    metrics = make_metrics(
        monthly_cash_flow=-50.0,
        annual_cash_flow=-600.0,
        noi_annual=15000.0,
        cap_rate=0.05,
        cash_on_cash_return=0.03,
        dscr=0.95,
    )

    grade, verdict, strengths, concerns = score_deal(metrics)

    assert grade == "D"
    assert verdict == "Pass"
    assert "Weak or negative monthly cash flow" in concerns
    assert "Low cash-on-cash return" in concerns


@pytest.mark.parametrize(
    ("field_name", "threshold_value", "expected_strength", "expected_concern"),
    [
        ("monthly_cash_flow", 300.0, "Healthy monthly cash flow", None),
        ("monthly_cash_flow", 100.0, "Positive monthly cash flow", None),
        ("cash_on_cash_return", 0.10, "Strong cash-on-cash return", None),
        ("cash_on_cash_return", 0.06, "Acceptable cash-on-cash return", None),
        ("cap_rate", 0.06, "Reasonable cap rate", None),
        ("dscr", 1.25, "Healthy debt-service coverage", None),
        ("dscr", 1.10, "Adequate debt-service coverage", None),
    ],
)
def test_score_deal_includes_expected_signals_at_exact_thresholds(
    make_metrics,
    field_name,
    threshold_value,
    expected_strength,
    expected_concern,
) -> None:
    metrics = make_metrics(**{field_name: threshold_value})

    _, _, strengths, concerns = score_deal(metrics)

    if expected_strength is not None:
        assert expected_strength in strengths
    if expected_concern is not None:
        assert expected_concern in concerns


@pytest.mark.parametrize(
    ("metrics", "expected_grade", "expected_verdict"),
    [
        (
            {
                "monthly_cash_flow": 300.0,
                "cash_on_cash_return": 0.10,
                "cap_rate": 0.06,
                "dscr": 1.25,
            },
            "A",
            "Strong Buy",
        ),
        (
            {
                "monthly_cash_flow": 100.0,
                "cash_on_cash_return": 0.06,
                "cap_rate": 0.06,
                "dscr": 1.10,
            },
            "B",
            "Buy",
        ),
        (
            {
                "monthly_cash_flow": 100.0,
                "cash_on_cash_return": 0.06,
                "cap_rate": 0.05,
                "dscr": 1.10,
            },
            "C",
            "Maybe",
        ),
        (
            {
                "monthly_cash_flow": 99.99,
                "cash_on_cash_return": 0.0599,
                "cap_rate": 0.05,
                "dscr": 1.09,
            },
            "D",
            "Pass",
        ),
    ],
)
def test_score_deal_grade_boundaries(make_metrics, metrics, expected_grade, expected_verdict) -> None:
    grade, verdict, _, _ = score_deal(make_metrics(**metrics))

    assert grade == expected_grade
    assert verdict == expected_verdict


def test_score_deal_detailed_uses_configurable_thresholds(make_metrics) -> None:
    metrics = make_metrics(
        monthly_cash_flow=300.0,
        cash_on_cash_return=0.10,
        cap_rate=0.06,
        dscr=1.25,
    )
    config = ScoringConfig(
        cash_flow_strong=500.0,
        cash_flow_positive=250.0,
        cash_on_cash_strong=0.12,
        cash_on_cash_acceptable=0.09,
        cap_rate_acceptable=0.07,
        dscr_strong=1.40,
        dscr_acceptable=1.20,
    )

    result = score_deal_detailed(metrics, config=config)

    assert result.grade == "C"
    assert result.verdict == "Maybe"
    assert "Healthy monthly cash flow" not in result.strengths
    assert "Positive monthly cash flow" in result.strengths
    assert "Cap rate is on the low side" in result.concerns


def test_score_deal_detailed_penalizes_high_rehab_risk(make_deal, make_metrics) -> None:
    metrics = make_metrics(
        monthly_cash_flow=500.0,
        annual_cash_flow=6000.0,
        noi_annual=26000.0,
        cap_rate=0.07,
        cash_on_cash_return=0.12,
        dscr=1.35,
    )
    low_rehab_deal = make_deal(
        purchase_price=200000.0,
        monthly_rent=3000.0,
        rehab_cost=5000.0,
    )
    high_rehab_deal = make_deal(
        purchase_price=200000.0,
        monthly_rent=3000.0,
        rehab_cost=45000.0,
    )

    low_rehab_result = score_deal_detailed(metrics, low_rehab_deal)
    high_rehab_result = score_deal_detailed(metrics, high_rehab_deal)

    assert high_rehab_result.score == low_rehab_result.score - 2
    assert high_rehab_result.confidence == "Low"
    assert "High rehab cost relative to purchase price" in high_rehab_result.concerns


def test_score_deal_detailed_penalizes_vacancy_stress(make_deal) -> None:
    deal = make_deal(monthly_rent=2800.0)
    metrics = calculate_metrics(deal)

    unstressed_result = score_deal_detailed(metrics)
    stressed_result = score_deal_detailed(metrics, deal)

    assert stressed_result.score == unstressed_result.score - 2
    assert stressed_result.vacancy_stress_cash_flow == pytest.approx(
        -37.18,
        abs=0.01,
    )
    assert "Higher vacancy turns cash flow negative" in stressed_result.concerns


def test_score_deal_detailed_applies_smaller_penalty_when_vacancy_stress_barely_survives(
    make_deal,
) -> None:
    deal = make_deal(monthly_rent=2950.0)
    metrics = calculate_metrics(deal)

    unstressed_result = score_deal_detailed(metrics)
    stressed_result = score_deal_detailed(metrics, deal)

    assert stressed_result.score == unstressed_result.score - 1
    assert stressed_result.vacancy_stress_cash_flow == pytest.approx(
        73.82,
        abs=0.01,
    )
    assert "Vacancy stress leaves a limited cash flow buffer" in stressed_result.concerns


@pytest.mark.parametrize(
    ("metrics_overrides", "expected_confidence"),
    [
        (
            {
                "monthly_cash_flow": 500.0,
                "cash_on_cash_return": 0.12,
                "cap_rate": 0.07,
                "dscr": 1.35,
            },
            "High",
        ),
        (
            {
                "monthly_cash_flow": 150.0,
                "cash_on_cash_return": 0.07,
                "cap_rate": 0.065,
                "dscr": 1.15,
            },
            "Medium",
        ),
        (
            {
                "monthly_cash_flow": -50.0,
                "cash_on_cash_return": 0.07,
                "cap_rate": 0.065,
                "dscr": 1.15,
            },
            "Low",
        ),
    ],
)
def test_score_deal_detailed_classifies_confidence(
    make_metrics,
    metrics_overrides,
    expected_confidence,
) -> None:
    result = score_deal_detailed(make_metrics(**metrics_overrides))

    assert result.confidence == expected_confidence


def test_score_deal_detailed_confidence_does_not_punish_all_cash_deals(make_metrics) -> None:
    metrics = make_metrics(
        monthly_mortgage=0.0,
        monthly_cash_flow=500.0,
        cash_on_cash_return=0.08,
        cap_rate=0.07,
        dscr=0.0,
    )

    result = score_deal_detailed(metrics)

    assert result.confidence == "High"
    assert result.cash_flow_buffer_ratio is None


def test_score_deal_detailed_reports_cash_flow_buffer_ratio(make_metrics) -> None:
    result = score_deal_detailed(
        make_metrics(monthly_cash_flow=300.0, monthly_mortgage=1500.0)
    )

    assert result.cash_flow_buffer_ratio == pytest.approx(0.20)


def test_score_deal_keeps_backward_compatible_return_signature(make_metrics) -> None:
    metrics = make_metrics()

    result = score_deal(metrics)

    assert isinstance(result, tuple)
    assert len(result) == 4
    assert result == ("B", "Buy", [
        "Positive monthly cash flow",
        "Acceptable cash-on-cash return",
        "Reasonable cap rate",
        "Adequate debt-service coverage",
    ], [])
