import math
import streamlit as st
import time
from dataclasses import replace

from calculator import (
    DEFAULT_SCORING_CONFIG,
    build_scenario_deal,
    calculate_break_even_rent,
    calculate_metrics,
    score_deal,
    score_deal_detailed,
)
from deal_comparison import (
    build_deal_comparison,
    compare_grades,
    compare_values,
    deal_input_from_dict,
)
from deal_storage import list_saved_deals, load_deal, save_deal
from models import DealInput
from scenario_analysis import build_scenario_change_messages, build_scenario_comparison_rows
from utils import format_currency, format_percent
from ai_analysis import generate_ai_analysis, generate_what_would_make_this_work
from ai_usage import (
    DEFAULT_AI_USAGE_LIMIT,
    ensure_ai_usage_state,
    get_ai_usage_count,
    is_ai_usage_limit_reached,
    record_ai_usage,
)

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

QUICK_ANALYSIS_ASSUMPTIONS = {
    "down_payment_pct": 25.0,
    "interest_rate": 6.5,
    "loan_term_years": 30,
    "property_tax_pct": 1.2,
    "insurance_pct": 0.35,
    "maintenance_pct": 8.0,
    "vacancy_pct": 8.0,
    "property_management_pct": 8.0,
    "hoa_monthly": 0.0,
    "closing_costs_pct": 2.0,
    "rehab_cost": 0.0,
}

for key, default_value in DEAL_INPUT_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default_value
if "analysis_mode" not in st.session_state:
    st.session_state.analysis_mode = "Full Analysis"
if "analysis_mode_selector" not in st.session_state:
    st.session_state.analysis_mode_selector = st.session_state.analysis_mode
if "deal_name" not in st.session_state:
    st.session_state.deal_name = "Deal 1"
if "quick_purchase_price" not in st.session_state:
    st.session_state.quick_purchase_price = st.session_state.purchase_price
if "quick_monthly_rent" not in st.session_state:
    st.session_state.quick_monthly_rent = st.session_state.monthly_rent
if "deal_storage_message" not in st.session_state:
    st.session_state.deal_storage_message = ""
if "ai_analysis" not in st.session_state:
    st.session_state.ai_analysis = ""
if "what_would_make_this_work" not in st.session_state:
    st.session_state.what_would_make_this_work = ""
if "loaded_query_deal" not in st.session_state:
    st.session_state.loaded_query_deal = ""
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Analyze"
if "pending_saved_deal" not in st.session_state:
    st.session_state.pending_saved_deal = ""
if "pending_portfolio_deal" not in st.session_state:
    st.session_state.pending_portfolio_deal = ""
if "last_opened_portfolio_deal" not in st.session_state:
    st.session_state.last_opened_portfolio_deal = ""
ensure_ai_usage_state(st.session_state)


def build_current_deal() -> DealInput:
    if st.session_state.analysis_mode == "Quick Analysis":
        purchase_price = st.session_state.quick_purchase_price
        return DealInput(
            purchase_price=purchase_price,
            monthly_rent=st.session_state.quick_monthly_rent,
            down_payment_pct=QUICK_ANALYSIS_ASSUMPTIONS["down_payment_pct"],
            interest_rate=QUICK_ANALYSIS_ASSUMPTIONS["interest_rate"],
            loan_term_years=int(QUICK_ANALYSIS_ASSUMPTIONS["loan_term_years"]),
            property_tax_annual=(
                purchase_price * QUICK_ANALYSIS_ASSUMPTIONS["property_tax_pct"] / 100
            ),
            insurance_annual=(
                purchase_price * QUICK_ANALYSIS_ASSUMPTIONS["insurance_pct"] / 100
            ),
            maintenance_pct=QUICK_ANALYSIS_ASSUMPTIONS["maintenance_pct"],
            vacancy_pct=QUICK_ANALYSIS_ASSUMPTIONS["vacancy_pct"],
            property_management_pct=QUICK_ANALYSIS_ASSUMPTIONS[
                "property_management_pct"
            ],
            hoa_monthly=QUICK_ANALYSIS_ASSUMPTIONS["hoa_monthly"],
            closing_costs=(
                purchase_price * QUICK_ANALYSIS_ASSUMPTIONS["closing_costs_pct"] / 100
            ),
            rehab_cost=QUICK_ANALYSIS_ASSUMPTIONS["rehab_cost"],
        )

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


def load_deal_into_session(deal_name: str) -> None:
    loaded_deal = load_deal(deal_name)
    for key in DEAL_INPUT_DEFAULTS:
        st.session_state[key] = loaded_deal[key]
    st.session_state.analysis_mode = "Full Analysis"
    st.session_state.analysis_mode_selector = "Full Analysis"
    st.session_state.quick_purchase_price = loaded_deal["purchase_price"]
    st.session_state.quick_monthly_rent = loaded_deal["monthly_rent"]
    st.session_state.deal_name = deal_name
    st.session_state.deal_storage_message = f"Loaded deal: {deal_name}."


def current_deal_name() -> str:
    return st.session_state.deal_name.strip() or "Deal 1"


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


def calculate_target_rent_for_cash_flow(
    deal: DealInput,
    target_cash_flow: float,
) -> float:
    break_even_rent = calculate_break_even_rent(deal)
    variable_expense_ratio = (
        deal.vacancy_pct
        + deal.property_management_pct
        + deal.maintenance_pct
    ) / 100

    if variable_expense_ratio >= 1:
        return float("inf")

    return break_even_rent + (target_cash_flow / (1 - variable_expense_ratio))


def format_rent_target(value: float) -> str:
    if math.isinf(value):
        return "Not achievable with current expense assumptions"
    return format_currency(value)


def buy_verdict_reached(verdict_value: str) -> bool:
    return verdict_value in {"Buy", "Strong Buy"}


def calculate_rent_needed_for_buy(
    deal: DealInput,
    current_verdict: str,
    step: float = 50.0,
    max_iterations: int = 200,
) -> float:
    if buy_verdict_reached(current_verdict):
        return deal.monthly_rent

    test_rent = max(0.0, deal.monthly_rent)
    max_rent = test_rent + (step * max_iterations)

    while test_rent <= max_rent:
        test_deal = replace(deal, monthly_rent=test_rent)
        test_metrics = calculate_metrics(test_deal)
        test_scoring = score_deal_detailed(test_metrics, test_deal)

        if buy_verdict_reached(test_scoring.verdict):
            return test_rent

        test_rent += step

    return float("inf")


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


def grade_caption(grade_value: str) -> str:
    captions = {
        "A": "✓ Strong profile",
        "B": "✓ Workable profile",
        "C": "△ Borderline profile",
        "D": "! Risk-heavy profile",
    }
    return captions.get(grade_value, "Review profile")


def verdict_caption(verdict_value: str) -> str:
    captions = {
        "Strong Buy": "✓ Meets strong-deal signals",
        "Buy": "✓ Clears core checks",
        "Maybe": "△ Needs closer underwriting",
        "Pass": "! Does not clear the bar",
    }
    return captions.get(verdict_value, "Review decision")


def confidence_caption(confidence_value: str) -> str:
    captions = {
        "High": "✓ Stable under stress",
        "Medium": "△ Assumptions matter",
        "Low": "! Fragile under stress",
    }
    return captions.get(confidence_value, "Review confidence")


def note_kind(note: str) -> str:
    risk_terms = ("negative", "weak", "thin", "low", "high rehab", "pass")
    caution_terms = ("limited", "drops", "stress", "moderate", "borderline")
    lowered_note = note.lower()

    if any(term in lowered_note for term in risk_terms):
        return "risk"
    if any(term in lowered_note for term in caution_terms):
        return "caution"
    return "positive"


def note_prefix(kind: str) -> str:
    prefixes = {
        "positive": "✓",
        "caution": "△",
        "risk": "!",
        "neutral": "-",
    }
    return prefixes.get(kind, "-")


def write_cued_note(note: str, kind: str = "neutral") -> None:
    st.markdown(f"{note_prefix(kind)} {note}")


def format_comparison_signal(signal: str) -> str:
    if signal == "Better":
        return "✓ Better"
    if signal == "Tie":
        return "- Tie"
    return signal


def build_portfolio_rows(saved_deal_names: list[str]) -> list[dict]:
    rows = []

    for saved_deal_name in saved_deal_names:
        saved_deal = deal_input_from_dict(load_deal(saved_deal_name))
        saved_metrics = calculate_metrics(saved_deal)
        saved_scoring = score_deal_detailed(saved_metrics, saved_deal)
        rows.append(
            {
                "Deal": saved_deal_name,
                "Grade": saved_scoring.grade,
                "Verdict": saved_scoring.verdict,
                "Confidence": saved_scoring.confidence,
                "Monthly Cash Flow": saved_metrics.monthly_cash_flow,
                "Cash-on-Cash Return": saved_metrics.cash_on_cash_return * 100,
                "Cap Rate": saved_metrics.cap_rate * 100,
                "DSCR": saved_metrics.dscr,
            }
        )

    return rows


def build_shareable_summary(
    deal_name: str,
    deal: DealInput,
    metrics,
    grade: str,
    verdict: str,
    confidence: str,
    strengths: list[str],
    concerns: list[str],
) -> str:
    top_strengths = strengths[:2] or ["No major strengths identified."]
    top_concerns = concerns[:2] or ["No major concerns identified."]

    return "\n".join(
        [
            f"Deal Summary: {deal_name}",
            f"Purchase Price: {format_currency(deal.purchase_price)}",
            f"Monthly Rent: {format_currency(deal.monthly_rent)}",
            f"Grade: {grade}",
            f"Verdict: {verdict}",
            f"Confidence: {confidence}",
            f"Monthly Cash Flow: {format_currency(metrics.monthly_cash_flow)}",
            f"Cash-on-Cash Return: {format_percent(metrics.cash_on_cash_return)}",
            f"Cap Rate: {format_percent(metrics.cap_rate)}",
            f"DSCR: {metrics.dscr:.2f}",
            "",
            "Top Strengths:",
            *[f"- {item}" for item in top_strengths],
            "",
            "Top Concerns:",
            *[f"- {item}" for item in top_concerns],
        ]
    )


pending_deal_name = (
    st.session_state.pending_saved_deal
    or st.session_state.pending_portfolio_deal
)
if pending_deal_name:
    try:
        load_deal_into_session(pending_deal_name)
    except FileNotFoundError:
        st.session_state.deal_storage_message = (
            f"Saved deal not found: {pending_deal_name}."
        )
    st.session_state.pending_saved_deal = ""
    st.session_state.pending_portfolio_deal = ""
    st.session_state.active_tab = "Analyze"
    st.query_params.clear()

query_deal_name = st.query_params.get("load_deal")
if query_deal_name and query_deal_name != st.session_state.loaded_query_deal:
    try:
        load_deal_into_session(query_deal_name)
        st.session_state.loaded_query_deal = query_deal_name
        st.session_state.active_tab = "Analyze"
    except FileNotFoundError:
        st.session_state.deal_storage_message = (
            f"Saved deal not found: {query_deal_name}."
        )

analyze_tab, compare_tab, portfolio_tab = st.tabs(
    ["Analyze", "Compare", "Portfolio"],
    key="active_tab",
)

with analyze_tab:
    st.session_state.analysis_mode = st.segmented_control(
        "Analysis Mode",
        options=["Full Analysis", "Quick Analysis"],
        key="analysis_mode_selector",
    )
    if st.session_state.analysis_mode == "Quick Analysis":
        st.caption("This is a rough estimate based on typical assumptions.")

    st.text_input("Deal Name", key="deal_name")

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

with analyze_tab:
    st.header("Deal Summary")

    with st.container():
        summary1, summary2, summary3 = st.columns(3)
        summary1.metric("Grade", grade)
        summary1.caption(grade_caption(grade))
        summary2.metric("Verdict", verdict)
        summary2.caption(verdict_caption(verdict))
        summary3.metric("Confidence", confidence)
        summary3.caption(confidence_caption(confidence))

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
            write_cued_note(note, note_kind(note))

        stability_col1, stability_col2 = st.columns(2)
        with stability_col1:
            st.subheader("Strengths")
            if strengths:
                for item in strengths:
                    write_cued_note(item, "positive")
            else:
                write_cued_note("No major strengths identified.", "neutral")

        with stability_col2:
            st.subheader("Concerns")
            if concerns:
                for item in concerns:
                    write_cued_note(item, note_kind(item))
            else:
                write_cued_note("No major concerns identified.", "neutral")

    st.header("Make This Deal Work")

    with st.container():
        break_even_rent = calculate_break_even_rent(deal)
        positive_cash_flow_rent = calculate_target_rent_for_cash_flow(
            deal,
            DEFAULT_SCORING_CONFIG.cash_flow_positive,
        )
        buy_rent = calculate_rent_needed_for_buy(deal, verdict)

        st.markdown(f"**Break-even rent:** {format_rent_target(break_even_rent)}")
        st.markdown(
            "**Positive cash flow rent:** "
            f"{format_rent_target(positive_cash_flow_rent)}"
        )
        st.markdown(f"**Rent needed for Buy:** {format_rent_target(buy_rent)}")
        st.caption(
            "Positive cash flow uses the app's current threshold of "
            f"{format_currency(DEFAULT_SCORING_CONFIG.cash_flow_positive)} per month."
        )

        if buy_verdict_reached(verdict):
            st.success("This deal already meets Buy criteria")

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
            if st.button("Save Deal"):
                saved_path = save_deal(current_deal_name(), deal)
                st.session_state.deal_storage_message = f"Saved deal to {saved_path.name}."
                st.rerun()

        with load_col:
            selected_saved_deal = st.selectbox(
                "Saved Deals",
                options=saved_deal_options,
                index=None,
                placeholder="Select a saved deal",
            )
            if st.button("Load Deal"):
                if selected_saved_deal:
                    st.session_state.pending_saved_deal = selected_saved_deal
                    st.rerun()
                else:
                    st.error("Select a saved deal to load.")

        if st.session_state.analysis_mode == "Quick Analysis":
            st.subheader("Quick Inputs")
            st.caption("This is a rough estimate based on typical assumptions.")

            quick_col1, quick_col2 = st.columns(2)
            with quick_col1:
                st.number_input(
                    "Purchase Price",
                    min_value=0.0,
                    step=1000.0,
                    key="quick_purchase_price",
                )
            with quick_col2:
                st.number_input(
                    "Monthly Rent",
                    min_value=0.0,
                    step=50.0,
                    key="quick_monthly_rent",
                )

            st.caption("Quick Analysis assumptions")
            assumption_col1, assumption_col2, assumption_col3 = st.columns(3)
            with assumption_col1:
                st.markdown(
                    f"- Vacancy: {QUICK_ANALYSIS_ASSUMPTIONS['vacancy_pct']:.1f}%"
                )
                st.markdown(
                    f"- Maintenance: {QUICK_ANALYSIS_ASSUMPTIONS['maintenance_pct']:.1f}%"
                )
                st.markdown(
                    "- Management: "
                    f"{QUICK_ANALYSIS_ASSUMPTIONS['property_management_pct']:.1f}%"
                )
            with assumption_col2:
                st.markdown(
                    "- Property tax: "
                    f"{QUICK_ANALYSIS_ASSUMPTIONS['property_tax_pct']:.2f}% of price "
                    f"({format_currency(deal.property_tax_annual)}/yr)"
                )
                st.markdown(
                    "- Insurance: "
                    f"{QUICK_ANALYSIS_ASSUMPTIONS['insurance_pct']:.2f}% of price "
                    f"({format_currency(deal.insurance_annual)}/yr)"
                )
                st.markdown(
                    "- Closing costs: "
                    f"{QUICK_ANALYSIS_ASSUMPTIONS['closing_costs_pct']:.1f}% of price "
                    f"({format_currency(deal.closing_costs)})"
                )
            with assumption_col3:
                st.markdown(
                    "- Down payment: "
                    f"{QUICK_ANALYSIS_ASSUMPTIONS['down_payment_pct']:.1f}%"
                )
                st.markdown(
                    f"- Interest rate: {QUICK_ANALYSIS_ASSUMPTIONS['interest_rate']:.2f}%"
                )
                st.markdown(
                    f"- Loan term: {QUICK_ANALYSIS_ASSUMPTIONS['loan_term_years']} years"
                )
        else:
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
    scenario_summary1.caption(grade_caption(scenario_grade))
    scenario_summary2.metric("Scenario Verdict", scenario_verdict)
    scenario_summary2.caption(verdict_caption(scenario_verdict))
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

    scenario_comparison_rows = build_scenario_comparison_rows(
        deal,
        scenario_deal,
        metrics,
        scenario_metrics,
    )

    for row in scenario_comparison_rows:
        c1, c2, c3 = st.columns([2, 2, 2])
        c1.write(row.label)
        c2.write(row.format_original())
        c3.write(row.format_scenario_with_delta())

    st.subheader("What Changed")

    improvements = build_scenario_change_messages(
        metrics,
        scenario_metrics,
        verdict,
        scenario_verdict,
    )

    if improvements:
        for item in improvements:
            write_cued_note(item, "positive")
    else:
        write_cued_note(
            "No meaningful improvement yet. Try changing rent, price, or rate.",
            "caution",
        )

with compare_tab:
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
                row2.write(f"{formatter(value_a)} {format_comparison_signal(better_a)}".strip())
                row3.write(f"{formatter(value_b)} {format_comparison_signal(better_b)}".strip())

            grade_better_a, grade_better_b = compare_grades(
                comparison["grade_a"],
                comparison["grade_b"],
            )

            grade_row1, grade_row2, grade_row3 = st.columns([2, 2, 2])
            grade_row1.write("Grade / Verdict")
            grade_row2.write(
                f'{comparison["grade_a"]} / {comparison["verdict_a"]} {format_comparison_signal(grade_better_a)}'.strip()
            )
            grade_row3.write(
                f'{comparison["grade_b"]} / {comparison["verdict_b"]} {format_comparison_signal(grade_better_b)}'.strip()
            )
        except FileNotFoundError:
            st.error("One of the selected saved deals could not be found.")
    else:
        st.caption("Select two saved deals to compare them side-by-side.")

with portfolio_tab:
    st.header("Portfolio Ranking")

    if saved_deal_options:
        try:
            portfolio_rows = build_portfolio_rows(saved_deal_options)
            st.caption("Select a row to load it in Analyze.")
            portfolio_selection = st.dataframe(
                portfolio_rows,
                column_config={
                    "Deal": st.column_config.TextColumn("Deal"),
                    "Monthly Cash Flow": st.column_config.NumberColumn(
                        "Monthly Cash Flow",
                        format="$%.2f",
                    ),
                    "Cash-on-Cash Return": st.column_config.NumberColumn(
                        "Cash-on-Cash Return",
                        format="%.2f%%",
                    ),
                    "Cap Rate": st.column_config.NumberColumn(
                        "Cap Rate",
                        format="%.2f%%",
                    ),
                    "DSCR": st.column_config.NumberColumn("DSCR", format="%.2f"),
                },
                hide_index=True,
                width="stretch",
                key="portfolio_ranking_table",
                on_select="rerun",
                selection_mode="single-row",
            )

            selected_rows = portfolio_selection.selection.rows
            if selected_rows:
                selected_deal_name = portfolio_rows[selected_rows[0]]["Deal"]
                if selected_deal_name != st.session_state.last_opened_portfolio_deal:
                    st.session_state.pending_portfolio_deal = selected_deal_name
                    st.session_state.last_opened_portfolio_deal = selected_deal_name
                    st.rerun()

            st.caption("Saved deals use the current scoring and metric rules.")
        except FileNotFoundError:
            st.error("A saved deal could not be found while building the portfolio ranking.")
        except KeyError:
            st.error("A saved deal is missing required fields and could not be ranked.")
    else:
        st.caption("Save deals to build a portfolio ranking.")

with analyze_tab:
    st.header("Shareable Summary")
    st.caption("Plain text summary for email or chat.")
    shareable_summary = build_shareable_summary(
        current_deal_name(),
        deal,
        metrics,
        grade,
        verdict,
        confidence,
        strengths,
        concerns,
    )
    st.code(shareable_summary, language="text")

    st.header("AI Insights")
    ai_usage_count = get_ai_usage_count(st.session_state)
    ai_limit_reached = is_ai_usage_limit_reached(
        st.session_state,
        DEFAULT_AI_USAGE_LIMIT,
    )
    ai_usage_caption = st.empty()
    ai_usage_caption.caption(
        f"AI uses this session: {ai_usage_count} / {DEFAULT_AI_USAGE_LIMIT}"
    )
    if ai_limit_reached:
        st.caption("Session AI limit reached. Non-AI deal analysis still works.")

    ai_col1, ai_col2 = st.columns(2)

    with ai_col1:
        if st.button("Run AI Analysis", disabled=ai_limit_reached):
            if not record_ai_usage(st.session_state, DEFAULT_AI_USAGE_LIMIT):
                st.info("Session AI limit reached. Non-AI deal analysis still works.")
            else:
                ai_usage_caption.caption(
                    "AI uses this session: "
                    f"{get_ai_usage_count(st.session_state)} / {DEFAULT_AI_USAGE_LIMIT}"
                )
                with st.spinner("Analyzing deal..."):
                    st.session_state.ai_analysis = generate_ai_analysis(
                        deal, metrics, verdict, strengths, concerns
                    )

    with ai_col2:
        if st.button("What Would Make This Work?", disabled=ai_limit_reached):
            if not record_ai_usage(st.session_state, DEFAULT_AI_USAGE_LIMIT):
                st.info("Session AI limit reached. Non-AI deal analysis still works.")
            else:
                ai_usage_caption.caption(
                    "AI uses this session: "
                    f"{get_ai_usage_count(st.session_state)} / {DEFAULT_AI_USAGE_LIMIT}"
                )
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
