from scenario_analysis import build_scenario_change_messages, build_scenario_comparison_rows


def test_build_scenario_comparison_rows_formats_values_and_deltas(
    make_deal,
    make_metrics,
) -> None:
    original_deal = make_deal()
    scenario_deal = make_deal(
        monthly_rent=2700.0,
        purchase_price=340000.0,
        interest_rate=6.0,
    )
    original_metrics = make_metrics(
        monthly_cash_flow=150.0,
        annual_cash_flow=1800.0,
        cash_on_cash_return=0.07,
        cap_rate=0.065,
        dscr=1.15,
    )
    scenario_metrics = make_metrics(
        monthly_cash_flow=275.0,
        annual_cash_flow=3300.0,
        cash_on_cash_return=0.085,
        cap_rate=0.072,
        dscr=1.28,
    )

    rows = build_scenario_comparison_rows(
        original_deal,
        scenario_deal,
        original_metrics,
        scenario_metrics,
    )

    assert [row.label for row in rows] == [
        "Monthly Rent",
        "Purchase Price",
        "Interest Rate",
        "Monthly Cash Flow",
        "Annual Cash Flow",
        "Cash-on-Cash Return",
        "Cap Rate",
        "DSCR",
    ]
    assert rows[0].format_original() == "$2,500.00"
    assert rows[0].format_scenario_with_delta() == "$2,700.00 (+$200.00)"
    assert rows[1].format_scenario_with_delta() == "$340,000.00 (-$10,000.00)"
    assert rows[2].format_scenario_with_delta() == "6.00% (-0.50%)"
    assert rows[-1].format_scenario_with_delta() == "1.28 (+0.13)"


def test_build_scenario_change_messages_describes_improvements(make_metrics) -> None:
    original_metrics = make_metrics(
        monthly_cash_flow=100.0,
        cash_on_cash_return=0.05,
        dscr=1.05,
    )
    scenario_metrics = make_metrics(
        monthly_cash_flow=250.0,
        cash_on_cash_return=0.075,
        dscr=1.2,
    )

    messages = build_scenario_change_messages(
        original_metrics,
        scenario_metrics,
        "Maybe",
        "Buy",
    )

    assert messages == [
        "Monthly cash flow improved by $150.00.",
        "Cash-on-cash return improved by +2.50%.",
        "DSCR improved by 0.15.",
        "Verdict changed from Maybe to Buy.",
    ]


def test_build_scenario_change_messages_returns_empty_when_nothing_improves(
    make_metrics,
) -> None:
    metrics = make_metrics(
        monthly_cash_flow=250.0,
        cash_on_cash_return=0.075,
        dscr=1.2,
    )

    assert build_scenario_change_messages(metrics, metrics, "Buy", "Buy") == []
