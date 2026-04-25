import streamlit as st
import time

from calculator import (
    build_scenario_deal,
    calculate_metrics,
    score_deal,
    score_deal_detailed,
)
from deal_comparison import build_deal_comparison, compare_grades, compare_values
from deal_storage import list_saved_deals, load_deal, save_deal
from models import DealInput
from utils import format_currency, format_delta, format_percent
from ai_analysis import generate_ai_analysis, generate_what_would_make_this_work

st.set_page_config(page_title="AI Deal Analyzer", page_icon="🏠", layout="wide")

st.title("AI Deal Analyzer")
st.caption("Personal rental deal analysis tool")

DEAL_INPUT_DEFAULTS = {
    "purchase_price": 350000.0,
    "monthly_rent": 2500.0,
    "down_payment_pct": 25.0,
    "interest_rate": 6.5,
    "loan_term_years": 30,
    "property_tax_annual": 4200.0,
    "insurance_annual": 1200.0,
    "maintenance_pct": 8.0,
    "vacancy_pct": 5.0,
    "property_management_pct": 8.0,
    "hoa_monthly": 0.0,
    "closing_costs": 7000.0,
    "rehab_cost": 5000.0,
}

for key, default_value in DEAL_INPUT_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default_value
if "deal_storage_message" not in st.session_state:
    st.session_state.deal_storage_message = ""
if "ai_analysis" not in st.session_state:
    st.session_state.ai_analysis = ""
if "what_would_make_this_work" not in st.session_state:
    st.session_state.what_would_make_this_work = ""


def build_current_deal() -> DealInput:
    return DealInput(
        purchase_price=st.session_state.purchase_price,
        monthly_rent=st.session_state.monthly_rent,
        down_payment_pct=st.session_state.down_payment_pct,
        interest_rate=st.session_state.interest_rate,
        loan_term_years=int(st.session_state.loan_term_years),
        property_tax_annual=st.session_state.property_tax_annual,
        insurance_annual=st.session_state.insurance_annual,
        maintenance_pct=st.session_state.maintenance_pct,
        vacancy_pct=st.session_state.vacancy_pct,
        property_management_pct=st.session_state.property_management_pct,
        hoa_monthly=st.session_state.hoa_monthly,
        closing_costs=st.session_state.closing_costs,
        rehab_cost=st.session_state.rehab_cost,
    )


def format_optional_currency(value: float | None) -> str:
    if value is None:
        return "N/A"
    return format_currency(value)


def format_optional_dscr(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}"


def calculate_rehab_risk(deal: DealInput) -> float | None:
    if deal.purchase_price > 0:
        return deal.rehab_cost / deal.purchase_price
    if deal.rehab_cost > 0:
        return None
    return 0.0


def build_confidence_notes(scoring_result) -> list[str]:
    notes = []
    stress_parts = []

    if scoring_result.vacancy_stress_cash_flow is not None:
        stress_parts.append(
            f"cash flow drops to {format_currency(scoring_result.vacancy_stress_cash_flow)}"
        )
    if scoring_result.vacancy_stress_dscr is not None:
        stress_parts.append(f"DSCR to {scoring_result.vacancy_stress_dscr:.2f}")
    if stress_parts:
        notes.append(f"Under higher vacancy: {', '.join(stress_parts)}.")

    if scoring_result.cash_flow_buffer_ratio is not None:
        notes.append(
            f"Cash flow buffer: {scoring_result.cash_flow_buffer_ratio:.2f}x mortgage."
        )

    priority_terms = ("vacancy", "rehab", "cash flow")
    signals = scoring_result.concerns + scoring_result.strengths
    for term in priority_terms:
        for signal in signals:
            if term in signal.lower() and signal not in notes:
                notes.append(signal)
                break
        if len(notes) >= 3:
            break

    if not notes:
        notes.append("No major confidence drivers identified.")

    return notes[:3]


def show_deal_storage_message(message: str) -> None:
    if hasattr(st, "toast"):
        st.toast(message)
        return

    placeholder = st.empty()
    placeholder.info(message)
    time.sleep(2)
    placeholder.empty()


deal = build_current_deal()
metrics = calculate_metrics(deal)
scoring_result = score_deal_detailed(metrics, deal)
grade = scoring_result.grade
verdict = scoring_result.verdict
confidence = scoring_result.confidence
strengths = scoring_result.strengths
concerns = scoring_result.concerns
rehab_risk = calculate_rehab_risk(deal)
saved_deal_options = list_saved_deals()

st.header("Deal Summary")

with st.container():
    summary1, summary2, summary3 = st.columns(3)
    summary1.metric("Grade", grade)
    summary2.metric("Verdict", verdict)
    summary3.metric("Confidence", confidence)

    summary4, summary5, summary6 = st.columns(3)
    summary4.metric("Monthly Cash Flow", format_currency(metrics.monthly_cash_flow))
    summary5.metric(
        "Cash-on-Cash Return",
        format_percent(metrics.cash_on_cash_return),
    )
    summary6.metric("DSCR", f"{metrics.dscr:.2f}")

st.header("Risk & Stability")

with st.container():
    risk1, risk2, risk3 = st.columns(3)
    risk1.metric(
        "Rehab Risk",
        "N/A" if rehab_risk is None else format_percent(rehab_risk),
        help="Rehab cost as a percentage of purchase price.",
    )
    risk2.metric(
        "Stressed Cash Flow",
        format_optional_currency(scoring_result.vacancy_stress_cash_flow),
        help="Cash flow after increasing vacancy by 5 percentage points.",
    )
    risk3.metric(
        "Stressed DSCR",
        format_optional_dscr(scoring_result.vacancy_stress_dscr),
        help="DSCR after increasing vacancy by 5 percentage points.",
    )

    st.caption("Confidence notes")
    for note in build_confidence_notes(scoring_result):
        st.markdown(f"- {note}")

    stability_col1, stability_col2 = st.columns(2)
    with stability_col1:
        st.subheader("Strengths")
        if strengths:
            for item in strengths:
                st.write(f"- {item}")
        else:
            st.write("No major strengths identified.")

    with stability_col2:
        st.subheader("Concerns")
        if concerns:
            for item in concerns:
                st.write(f"- {item}")
        else:
            st.write("No major concerns identified.")

with st.expander("Additional Metrics"):
    detail1, detail2, detail3 = st.columns(3)
    detail1.metric("Monthly Mortgage", format_currency(metrics.monthly_mortgage))
    detail2.metric("Annual Cash Flow", format_currency(metrics.annual_cash_flow))
    detail3.metric("NOI (Annual)", format_currency(metrics.noi_annual))

    detail4, detail5 = st.columns(2)
    detail4.metric("Cap Rate", format_percent(metrics.cap_rate))
    detail5.metric("Total Cash Invested", format_currency(metrics.total_cash_invested))

st.header("Deal Inputs")

with st.expander("Save, Load, and Edit Deal Inputs", expanded=True):
    st.subheader("Save / Load Deals")

    if st.session_state.deal_storage_message:
        show_deal_storage_message(st.session_state.deal_storage_message)
        st.session_state.deal_storage_message = ""

    save_col, load_col = st.columns(2)

    with save_col:
        deal_name = st.text_input("Deal Name", placeholder="e.g. 123 Main St")
        if st.button("Save Deal"):
            if deal_name.strip():
                saved_path = save_deal(
                    deal_name,
                    DealInput(
                        purchase_price=st.session_state.purchase_price,
                        monthly_rent=st.session_state.monthly_rent,
                        down_payment_pct=st.session_state.down_payment_pct,
                        interest_rate=st.session_state.interest_rate,
                        loan_term_years=int(st.session_state.loan_term_years),
                        property_tax_annual=st.session_state.property_tax_annual,
                        insurance_annual=st.session_state.insurance_annual,
                        maintenance_pct=st.session_state.maintenance_pct,
                        vacancy_pct=st.session_state.vacancy_pct,
                        property_management_pct=st.session_state.property_management_pct,
                        hoa_monthly=st.session_state.hoa_monthly,
                        closing_costs=st.session_state.closing_costs,
                        rehab_cost=st.session_state.rehab_cost,
                    ),
                )
                st.session_state.deal_storage_message = f"Saved deal to {saved_path.name}."
                st.rerun()
            else:
                st.error("Enter a deal name before saving.")

    with load_col:
        selected_saved_deal = st.selectbox(
            "Saved Deals",
            options=saved_deal_options,
            index=None,
            placeholder="Select a saved deal",
        )
        if st.button("Load Deal"):
            if selected_saved_deal:
                try:
                    loaded_deal = load_deal(selected_saved_deal)
                    for key in DEAL_INPUT_DEFAULTS:
                        st.session_state[key] = loaded_deal[key]
                    st.session_state.deal_storage_message = f"Loaded deal: {selected_saved_deal}."
                    st.rerun()
                except FileNotFoundError:
                    st.error("That saved deal could not be found.")
            else:
                st.error("Select a saved deal to load.")

    st.subheader("Property & Financing")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.number_input(
            "Purchase Price",
            min_value=0.0,
            step=1000.0,
            key="purchase_price",
        )
        st.number_input("Monthly Rent", min_value=0.0, step=50.0, key="monthly_rent")
        st.number_input(
            "Down Payment %",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key="down_payment_pct",
        )
        st.number_input(
            "Interest Rate %",
            min_value=0.0,
            step=0.1,
            key="interest_rate",
        )
        st.number_input(
            "Loan Term (Years)",
            min_value=1,
            step=1,
            key="loan_term_years",
        )

    with col2:
        st.number_input(
            "Property Tax (Annual)",
            min_value=0.0,
            step=100.0,
            key="property_tax_annual",
        )
        st.number_input(
            "Insurance (Annual)",
            min_value=0.0,
            step=100.0,
            key="insurance_annual",
        )
        st.number_input(
            "Maintenance %",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key="maintenance_pct",
        )
        st.number_input(
            "Vacancy %",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key="vacancy_pct",
        )
        st.number_input(
            "Property Management %",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key="property_management_pct",
        )

    with col3:
        st.number_input("HOA (Monthly)", min_value=0.0, step=25.0, key="hoa_monthly")
        st.number_input(
            "Closing Costs",
            min_value=0.0,
            step=500.0,
            key="closing_costs",
        )
        st.number_input("Rehab Cost", min_value=0.0, step=500.0, key="rehab_cost")

st.header("Scenario Analysis")
st.caption("Test what changes would make the deal stronger.")

s1, s2, s3 = st.columns(3)

with s1:
    scenario_rent_increase = st.number_input(
        "Rent Increase",
        value=0.0,
        step=50.0,
        help="Increase or decrease the monthly rent for the scenario.",
    )

with s2:
    scenario_purchase_price_adjustment = st.number_input(
        "Purchase Price Adjustment",
        value=0.0,
        step=1000.0,
        help="Use a negative number for a lower purchase price.",
    )

with s3:
    scenario_interest_rate_change = st.number_input(
        "Interest Rate Change (%)",
        value=0.0,
        step=0.1,
        help="Use a negative number for a lower interest rate.",
    )

scenario_deal = build_scenario_deal(
    deal,
    rent_increase=scenario_rent_increase,
    purchase_price_adjustment=scenario_purchase_price_adjustment,
    interest_rate_change=scenario_interest_rate_change,
)
scenario_metrics = calculate_metrics(scenario_deal)
scenario_grade, scenario_verdict, _, _ = score_deal(scenario_metrics)

scenario_summary1, scenario_summary2, scenario_summary3 = st.columns(3)
scenario_summary1.metric("Scenario Grade", scenario_grade)
scenario_summary2.metric("Scenario Verdict", scenario_verdict)
scenario_summary3.metric(
    "Cash Flow Improvement",
    format_currency(scenario_metrics.monthly_cash_flow),
    delta=format_currency(scenario_metrics.monthly_cash_flow - metrics.monthly_cash_flow),
)

st.subheader("Original vs Scenario")
header1, header2, header3 = st.columns([2, 2, 2])
header1.markdown("**Metric**")
header2.markdown("**Original**")
header3.markdown("**Scenario**")

scenario_comparison_rows = [
    (
        "Monthly Rent",
        deal.monthly_rent,
        scenario_deal.monthly_rent,
        format_currency,
        False,
        True,
    ),
    (
        "Purchase Price",
        deal.purchase_price,
        scenario_deal.purchase_price,
        format_currency,
        False,
        True,
    ),
    (
        "Interest Rate",
        deal.interest_rate / 100,
        scenario_deal.interest_rate / 100,
        format_percent,
        True,
        False,
    ),
    (
        "Monthly Cash Flow",
        metrics.monthly_cash_flow,
        scenario_metrics.monthly_cash_flow,
        format_currency,
        False,
        True,
    ),
    (
        "Annual Cash Flow",
        metrics.annual_cash_flow,
        scenario_metrics.annual_cash_flow,
        format_currency,
        False,
        True,
    ),
    (
        "Cash-on-Cash Return",
        metrics.cash_on_cash_return,
        scenario_metrics.cash_on_cash_return,
        format_percent,
        True,
        False,
    ),
    (
        "Cap Rate",
        metrics.cap_rate,
        scenario_metrics.cap_rate,
        format_percent,
        True,
        False,
    ),
    (
        "DSCR",
        metrics.dscr,
        scenario_metrics.dscr,
        lambda value: f"{value:.2f}",
        False,
        False,
    ),
]

for label, original, scenario, formatter, is_percent, is_currency in scenario_comparison_rows:
    c1, c2, c3 = st.columns([2, 2, 2])
    c1.write(label)
    c2.write(formatter(original))
    c3.write(
        f"{formatter(scenario)} "
        f"({format_delta(scenario - original, is_percent=is_percent, is_currency=is_currency)})"
    )

st.subheader("What Changed")

improvements = []
if scenario_metrics.monthly_cash_flow > metrics.monthly_cash_flow:
    improvements.append(
        f"Monthly cash flow improved by {format_currency(scenario_metrics.monthly_cash_flow - metrics.monthly_cash_flow)}."
    )
if scenario_metrics.cash_on_cash_return > metrics.cash_on_cash_return:
    improvements.append(
        f"Cash-on-cash return improved by {format_delta(scenario_metrics.cash_on_cash_return - metrics.cash_on_cash_return, is_percent=True)}."
    )
if scenario_metrics.dscr > metrics.dscr:
    improvements.append(f"DSCR improved by {scenario_metrics.dscr - metrics.dscr:.2f}.")
if scenario_verdict != verdict:
    improvements.append(f"Verdict changed from {verdict} to {scenario_verdict}.")

if improvements:
    for item in improvements:
        st.write(f"- {item}")
else:
    st.write("No meaningful improvement yet. Try changing rent, price, or rate.")

st.header("Deal Comparison")

compare_col1, compare_col2 = st.columns(2)

with compare_col1:
    comparison_deal_a = st.selectbox(
        "Deal A",
        options=saved_deal_options,
        index=None,
        placeholder="Select Deal A",
    )

with compare_col2:
    comparison_deal_b = st.selectbox(
        "Deal B",
        options=saved_deal_options,
        index=None,
        placeholder="Select Deal B",
    )

if comparison_deal_a and comparison_deal_b:
    try:
        comparison = build_deal_comparison(
            load_deal(comparison_deal_a),
            load_deal(comparison_deal_b),
        )

        st.caption("Compare saved deals side-by-side.")

        compare_header1, compare_header2, compare_header3 = st.columns([2, 2, 2])
        compare_header1.markdown("**Metric**")
        compare_header2.markdown(f"**{comparison_deal_a}**")
        compare_header3.markdown(f"**{comparison_deal_b}**")

        comparison_rows = [
            (
                "Purchase Price",
                comparison["deal_a"].purchase_price,
                comparison["deal_b"].purchase_price,
                format_currency,
                False,
            ),
            (
                "Monthly Rent",
                comparison["deal_a"].monthly_rent,
                comparison["deal_b"].monthly_rent,
                format_currency,
                True,
            ),
            (
                "Monthly Cash Flow",
                comparison["metrics_a"].monthly_cash_flow,
                comparison["metrics_b"].monthly_cash_flow,
                format_currency,
                True,
            ),
            (
                "Cap Rate",
                comparison["metrics_a"].cap_rate,
                comparison["metrics_b"].cap_rate,
                format_percent,
                True,
            ),
            (
                "Cash-on-Cash Return",
                comparison["metrics_a"].cash_on_cash_return,
                comparison["metrics_b"].cash_on_cash_return,
                format_percent,
                True,
            ),
            (
                "DSCR",
                comparison["metrics_a"].dscr,
                comparison["metrics_b"].dscr,
                lambda value: f"{value:.2f}",
                True,
            ),
            (
                "Total Cash Invested",
                comparison["metrics_a"].total_cash_invested,
                comparison["metrics_b"].total_cash_invested,
                format_currency,
                False,
            ),
        ]

        for label, value_a, value_b, formatter, higher_is_better in comparison_rows:
            better_a, better_b = compare_values(
                value_a,
                value_b,
                higher_is_better=higher_is_better,
            )
            row1, row2, row3 = st.columns([2, 2, 2])
            row1.write(label)
            row2.write(f"{formatter(value_a)} {better_a}".strip())
            row3.write(f"{formatter(value_b)} {better_b}".strip())

        grade_better_a, grade_better_b = compare_grades(
            comparison["grade_a"],
            comparison["grade_b"],
        )

        grade_row1, grade_row2, grade_row3 = st.columns([2, 2, 2])
        grade_row1.write("Grade / Verdict")
        grade_row2.write(
            f'{comparison["grade_a"]} / {comparison["verdict_a"]} {grade_better_a}'.strip()
        )
        grade_row3.write(
            f'{comparison["grade_b"]} / {comparison["verdict_b"]} {grade_better_b}'.strip()
        )
    except FileNotFoundError:
        st.error("One of the selected saved deals could not be found.")
else:
    st.caption("Select two saved deals to compare them side-by-side.")

st.header("AI Insights")

ai_col1, ai_col2 = st.columns(2)

with ai_col1:
    if st.button("Run AI Analysis"):
        with st.spinner("Analyzing deal..."):
            st.session_state.ai_analysis = generate_ai_analysis(
                deal, metrics, verdict, strengths, concerns
            )

with ai_col2:
    if st.button("What Would Make This Work?"):
        with st.spinner("Analyzing what would make this deal work..."):
            st.session_state.what_would_make_this_work = generate_what_would_make_this_work(
                deal,
                metrics,
                grade,
                verdict,
                strengths,
                concerns,
                scenario_deal,
                scenario_metrics,
                scenario_grade,
                scenario_verdict,
            )

if st.session_state.ai_analysis:
    st.subheader("AI Analysis")
    st.write(st.session_state.ai_analysis)
else:
    st.caption("Click the button to generate AI analysis.")

if st.session_state.what_would_make_this_work:
    st.subheader("What Would Make This Work?")
    st.write(st.session_state.what_would_make_this_work)
else:
    st.caption("Click the button to get practical deal-improvement guidance.")
