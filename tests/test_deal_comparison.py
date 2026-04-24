import pytest

from deal_comparison import build_deal_comparison, compare_grades, compare_values, deal_input_from_dict


def test_deal_input_from_dict_creates_deal_input(make_deal) -> None:
    deal = make_deal()

    converted = deal_input_from_dict(deal.__dict__)

    assert converted.purchase_price == pytest.approx(deal.purchase_price)
    assert converted.monthly_rent == pytest.approx(deal.monthly_rent)
    assert converted.loan_term_years == deal.loan_term_years


def test_compare_values_marks_higher_value_as_better() -> None:
    assert compare_values(10.0, 5.0, higher_is_better=True) == ("Better", "")
    assert compare_values(5.0, 10.0, higher_is_better=True) == ("", "Better")


def test_compare_values_marks_lower_value_as_better() -> None:
    assert compare_values(5.0, 10.0, higher_is_better=False) == ("Better", "")
    assert compare_values(10.0, 5.0, higher_is_better=False) == ("", "Better")


def test_compare_values_handles_ties() -> None:
    assert compare_values(5.0, 5.0, higher_is_better=True) == ("Tie", "Tie")


def test_compare_grades_uses_grade_ordering() -> None:
    assert compare_grades("A", "B") == ("Better", "")
    assert compare_grades("C", "A") == ("", "Better")
    assert compare_grades("B", "B") == ("Tie", "Tie")


def test_build_deal_comparison_returns_metrics_and_rating_data(make_deal) -> None:
    comparison = build_deal_comparison(
        make_deal(monthly_rent=3000.0).__dict__,
        make_deal(monthly_rent=2200.0).__dict__,
    )

    assert comparison["deal_a"].monthly_rent == pytest.approx(3000.0)
    assert comparison["deal_b"].monthly_rent == pytest.approx(2200.0)
    assert comparison["metrics_a"].monthly_cash_flow > comparison["metrics_b"].monthly_cash_flow
    assert comparison["grade_a"] in {"A", "B", "C", "D"}
    assert comparison["verdict_b"] in {"Strong Buy", "Buy", "Maybe", "Pass"}
