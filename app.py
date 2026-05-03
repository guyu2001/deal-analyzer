import json
import math
import os
import streamlit as st
from dataclasses import asdict, replace

from calculator import (
    DEFAULT_SCORING_CONFIG,
    build_scenario_deal,
    calculate_break_even_rent,
    calculate_metrics,
    score_deal,
    score_deal_detailed,
)
from models import DealInput
from scenario_analysis import build_scenario_change_messages, build_scenario_comparison_rows
from utils import format_currency, format_percent, parse_dollar_input
st.set_page_config(
    page_title="AI Real Estate Deal Analyzer",
    page_icon="🏠",
    layout="wide",
)

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
PENDING_DEAL_IMPORT_KEY = "pending_deal_import"

for key, default_value in DEAL_INPUT_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default_value
if "deal_name" not in st.session_state:
    st.session_state.deal_name = "Deal 1"
if "purchase_price_text" not in st.session_state:
    st.session_state.purchase_price_text = (
        f"{st.session_state.purchase_price:,.0f}"
    )
if "monthly_rent_text" not in st.session_state:
    st.session_state.monthly_rent_text = f"{st.session_state.monthly_rent:,.0f}"
if "deal_file_message" not in st.session_state:
    st.session_state.deal_file_message = ""
if "deal_import_toast" not in st.session_state:
    st.session_state.deal_import_toast = ""
if "last_imported_deal_file" not in st.session_state:
    st.session_state.last_imported_deal_file = ""
if "import_uploader_version" not in st.session_state:
    st.session_state.import_uploader_version = 0
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Analyze"
if "feedback_rating" not in st.session_state:
    st.session_state.feedback_rating = None

pending_deal_import = st.session_state.pop(PENDING_DEAL_IMPORT_KEY, None)
if pending_deal_import:
    imported_values = pending_deal_import["values"]
    for key in DEAL_INPUT_DEFAULTS:
        st.session_state[key] = imported_values[key]
    st.session_state.deal_name = pending_deal_import["deal_name"]
    st.session_state.purchase_price_text = (
        f"{st.session_state.purchase_price:,.0f}"
    )
    st.session_state.monthly_rent_text = f"{st.session_state.monthly_rent:,.0f}"

st.title("AI Real Estate Deal Analyzer")
st.caption("Get a quick second opinion on whether a rental deal is worth it.")
st.caption("Enter price and rent, then review the verdict instantly.")

if st.session_state.deal_import_toast:
    if hasattr(st, "toast"):
        st.toast(st.session_state.deal_import_toast)
    else:
        st.caption(st.session_state.deal_import_toast)
    st.session_state.deal_import_toast = ""


def get_feedback_url() -> str:
    try:
        feedback_url = st.secrets.get("FEEDBACK_URL", "")
    except Exception:
        feedback_url = ""

    if not feedback_url:
        feedback_url = os.environ.get("FEEDBACK_URL", "")

    return str(feedback_url).strip()


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


def current_deal_name() -> str:
    return st.session_state.deal_name.strip() or "Deal 1"


def deal_export_payload(deal_name: str, deal: DealInput) -> dict[str, float | int | str]:
    return {"deal_name": deal_name, **asdict(deal)}


def deal_export_json(deal_name: str, deal: DealInput) -> str:
    return json.dumps(deal_export_payload(deal_name, deal), indent=2)


def import_deal_payload(
    payload: dict,
    fallback_deal_name: str,
) -> tuple[str, dict[str, float | int], list[str]]:
    errors = []
    missing_fields = [
        field_name for field_name in DEAL_INPUT_DEFAULTS if field_name not in payload
    ]
    if missing_fields:
        errors.append(
            "Missing required deal fields: " + ", ".join(missing_fields) + "."
        )
        return "", {}, errors

    imported_values = {}
    for key in DEAL_INPUT_DEFAULTS:
        value = payload[key]
        try:
            if key == "loan_term_years":
                imported_values[key] = int(value)
            else:
                imported_values[key] = float(value)
        except (TypeError, ValueError):
            errors.append(f"{key} must be a number.")

    if errors:
        return "", {}, errors

    imported_deal_name = str(payload.get("deal_name") or fallback_deal_name).strip()
    return imported_deal_name or "Imported Deal", imported_values, []


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


def build_rent_to_price_hint(deal: DealInput) -> str | None:
    if deal.purchase_price <= 0:
        return None

    rent_to_price_ratio = deal.monthly_rent / deal.purchase_price
    ratio_text = f"{rent_to_price_ratio * 100:.2f}%"

    if rent_to_price_ratio < 0.005:
        return (
            f"Rent-to-price ratio is {ratio_text}; rent appears low relative to "
            "price (below ~0.5% rule), while typical rentals are ~0.8%-1.2%."
        )
    if rent_to_price_ratio < 0.008:
        return (
            f"Rent-to-price ratio is {ratio_text}; rent is somewhat low relative "
            "to price, and many rentals fall closer to ~0.8%-1.2%."
        )
    if rent_to_price_ratio <= 0.012:
        return (
            f"Rent-to-price ratio is {ratio_text}; this is within a typical "
            "range for rentals."
        )
    return (
        f"Rent-to-price ratio is {ratio_text}; this is strong compared to "
        "typical rental ranges."
    )


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


def build_verdict_explanation(metrics, scoring_result) -> str:
    config = DEFAULT_SCORING_CONFIG
    concerns = scoring_result.concerns
    cash_flow = format_currency(metrics.monthly_cash_flow)
    cash_on_cash = format_percent(metrics.cash_on_cash_return)
    dscr = f"{metrics.dscr:.2f}"

    if (
        "Weak or negative monthly cash flow" in concerns
        or metrics.monthly_cash_flow < config.cash_flow_positive
    ):
        first_sentence = (
            f"Monthly cash flow is {cash_flow}, below the "
            f"{format_currency(config.cash_flow_positive)} minimum target."
        )
    elif (
        "Low cash-on-cash return" in concerns
        or metrics.cash_on_cash_return < config.cash_on_cash_acceptable
    ):
        first_sentence = (
            f"Cash-on-cash return is {cash_on_cash}, below the "
            f"{format_percent(config.cash_on_cash_acceptable)} acceptable target."
        )
    elif (
        "Debt-service coverage is thin" in concerns
        or metrics.dscr < config.dscr_acceptable
    ):
        first_sentence = (
            f"DSCR is {dscr}, below the {config.dscr_acceptable:.2f} target."
        )
    elif metrics.monthly_cash_flow >= config.cash_flow_strong:
        first_sentence = (
            f"Monthly cash flow is {cash_flow}, above the "
            f"{format_currency(config.cash_flow_strong)} strong threshold."
        )
    elif metrics.cash_on_cash_return >= config.cash_on_cash_strong:
        first_sentence = (
            f"Cash-on-cash return is {cash_on_cash}, above the "
            f"{format_percent(config.cash_on_cash_strong)} strong threshold."
        )
    elif metrics.dscr >= config.dscr_strong:
        first_sentence = f"DSCR is {dscr}, giving the deal debt-service cushion."
    else:
        first_sentence = (
            f"Monthly cash flow is {cash_flow}, positive but below the "
            f"{format_currency(config.cash_flow_strong)} strong threshold."
        )

    stress_cash_flow = scoring_result.vacancy_stress_cash_flow
    if stress_cash_flow is not None and (
        stress_cash_flow < config.vacancy_cash_flow_buffer
        or scoring_result.confidence != "High"
    ):
        second_sentence = (
            f"Under higher vacancy, cash flow falls to "
            f"{format_currency(stress_cash_flow)}, so assumptions matter."
        )
    elif metrics.dscr >= config.dscr_strong:
        second_sentence = f"DSCR is {dscr}, giving the deal debt-service cushion."
    elif metrics.dscr >= config.dscr_acceptable:
        second_sentence = f"DSCR is {dscr}, adequate but not a large cushion."
    else:
        second_sentence = f"DSCR is {dscr}, below the {config.dscr_acceptable:.2f} target."

    if second_sentence == first_sentence:
        return first_sentence

    return f"{first_sentence} {second_sentence}"


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


analyze_tab, compare_tab, portfolio_tab = st.tabs(
    ["Analyze", "Compare", "Portfolio"],
    key="active_tab",
)

with analyze_tab:
    st.subheader("Quick second opinion for rental property deals")
    st.caption("Start here: enter the price and rent, then review the verdict below.")

    with st.container(border=True):
        st.markdown("**Deal basics**")
        st.text_input("Deal Name", key="deal_name")

        primary_col1, primary_col2 = st.columns(2)
        with primary_col1:
            st.text_input(
                "Purchase Price ($)",
                key="purchase_price_text",
                placeholder="750,000",
                help="You can type commas, like 750,000 or 1,000,000.",
            )
            st.caption("Example: 750,000")
        with primary_col2:
            st.text_input(
                "Monthly Rent ($)",
                key="monthly_rent_text",
                placeholder="2,500",
                help="You can type commas, like 2,500.",
            )
            st.caption("Example: 2,500")

        input_errors = []
        try:
            parsed_purchase_price = parse_dollar_input(
                st.session_state.purchase_price_text
            )
        except ValueError as exc:
            input_errors.append(f"Purchase Price: {exc}")
        else:
            if parsed_purchase_price is not None:
                st.session_state.purchase_price = parsed_purchase_price

        try:
            parsed_monthly_rent = parse_dollar_input(
                st.session_state.monthly_rent_text
            )
        except ValueError as exc:
            input_errors.append(f"Monthly Rent: {exc}")
        else:
            if parsed_monthly_rent is not None:
                st.session_state.monthly_rent = parsed_monthly_rent

        for input_error in input_errors:
            st.error(input_error)

        with st.expander("Advanced assumptions"):
            col1, col2, col3 = st.columns(3)

            with col1:
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

            with col3:
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
                st.number_input(
                    "HOA (Monthly)",
                    min_value=0.0,
                    step=25.0,
                    key="hoa_monthly",
                )
                st.number_input(
                    "Closing Costs",
                    min_value=0.0,
                    step=500.0,
                    key="closing_costs",
                )
                st.number_input(
                    "Rehab Cost",
                    min_value=0.0,
                    step=500.0,
                    key="rehab_cost",
                )

        with st.expander("Save / Import Deal File"):
            st.info(
                "Deals are saved only as files you download. "
                "This app does not store your deals."
            )

            uploaded_deal = st.file_uploader(
                "Import Deal",
                type="json",
                accept_multiple_files=False,
                help="Import a JSON deal file exported from this app.",
                key=f"import_deal_uploader_{st.session_state.import_uploader_version}",
            )
            if uploaded_deal is not None:
                uploaded_signature = f"{uploaded_deal.name}:{uploaded_deal.size}"
            else:
                uploaded_signature = ""
                st.session_state.last_imported_deal_file = ""

            if (
                uploaded_deal is not None
                and uploaded_signature != st.session_state.last_imported_deal_file
            ):
                try:
                    imported_payload = json.load(uploaded_deal)
                    if not isinstance(imported_payload, dict):
                        st.session_state.deal_file_message = (
                            "Import failed: deal JSON must be an object."
                        )
                    else:
                        fallback_name = uploaded_deal.name.rsplit(".", 1)[0]
                        imported_name, imported_values, import_errors = import_deal_payload(
                            imported_payload,
                            fallback_name,
                        )
                        if import_errors:
                            st.session_state.deal_file_message = (
                                "Import failed: " + " ".join(import_errors)
                            )
                        else:
                            st.session_state[PENDING_DEAL_IMPORT_KEY] = {
                                "deal_name": imported_name,
                                "values": imported_values,
                            }
                            st.session_state.deal_import_toast = (
                                f"Imported deal: {imported_name}"
                            )
                            st.session_state.last_imported_deal_file = uploaded_signature
                            st.session_state.import_uploader_version += 1
                            st.rerun()
                except json.JSONDecodeError:
                    st.session_state.deal_file_message = (
                        "Import failed: the uploaded file is not valid JSON."
                    )

            if st.session_state.deal_file_message:
                st.info(st.session_state.deal_file_message)
                st.session_state.deal_file_message = ""

            st.download_button(
                "Export Deal",
                data=deal_export_json(current_deal_name(), build_current_deal()),
                file_name=f"{current_deal_name().replace(' ', '_')}.json",
                mime="application/json",
            )

deal = build_current_deal()
metrics = calculate_metrics(deal)
scoring_result = score_deal_detailed(metrics, deal)
grade = scoring_result.grade
verdict = scoring_result.verdict
confidence = scoring_result.confidence
strengths = scoring_result.strengths
concerns = scoring_result.concerns
rehab_risk = calculate_rehab_risk(deal)

with analyze_tab:
    with st.container(border=True):
        st.markdown("**Deal result**")
        verdict_cues = {
            "Strong Buy": "✓",
            "Buy": "✓",
            "Maybe": "△",
            "Pass": "❌",
        }
        verdict_cue = verdict_cues.get(verdict, "△")

        st.markdown(f"## {verdict_cue} {verdict}")
        st.write(build_verdict_explanation(metrics, scoring_result))
        rent_to_price_hint = build_rent_to_price_hint(deal)
        st.markdown(
            "**Assumptions used:** "
            f"{deal.down_payment_pct:.0f}% down · "
            f"{deal.interest_rate:.2f}% interest · "
            f"{deal.vacancy_pct:.0f}% vacancy · "
            f"{deal.maintenance_pct:.0f}% maintenance · "
            "Edit in Advanced assumptions"
        )

        reason_items = []
        if rent_to_price_hint:
            reason_items.append((rent_to_price_hint, note_kind(rent_to_price_hint)))
        if strengths:
            reason_items.append((strengths[0], "positive"))
        if concerns:
            reason_items.append((concerns[0], note_kind(concerns[0])))
        for strength in strengths[1:]:
            if len(reason_items) >= 3:
                break
            reason_items.append((strength, "positive"))
        for concern in concerns[1:]:
            if len(reason_items) >= 3:
                break
            reason_items.append((concern, note_kind(concern)))

        if reason_items:
            st.markdown("**Why this verdict:**")
            for reason, reason_kind in reason_items:
                write_cued_note(reason, reason_kind)

        st.divider()

        support1, support2, support3 = st.columns(3)
        support1.metric("Cash Flow", format_currency(metrics.monthly_cash_flow))
        support2.metric(
            "Cash-on-Cash Return",
            format_percent(metrics.cash_on_cash_return),
        )
        support3.metric("DSCR", f"{metrics.dscr:.2f}")

        st.caption(
            f"Grade {grade} - {grade_caption(grade)} | "
            f"Confidence {confidence} - {confidence_caption(confidence)}"
        )

    with st.expander("Risk & Stability"):
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

    with st.expander("Make This Deal Work"):
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

    with st.expander("Scenario Analysis"):
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

        st.markdown("**Original vs Scenario**")
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

        st.markdown("**What Changed**")

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
    st.info(
        "Deal comparison is temporarily disabled while private file-based "
        "comparison is being redesigned."
    )

with portfolio_tab:
    st.header("Portfolio Ranking")
    st.info(
        "Portfolio ranking is temporarily disabled while private file-based "
        "portfolios are being redesigned."
    )

with analyze_tab:
    with st.expander("Shareable Summary"):
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

    st.markdown("**Feedback**")
    st.caption("Quick reaction here, detailed feedback through the form.")
    if hasattr(st, "feedback"):
        st.session_state.feedback_rating = st.feedback(
            "thumbs",
            key="feedback_rating_widget",
        )

    feedback_url = get_feedback_url()
    if feedback_url:
        st.link_button("Leave detailed feedback", feedback_url)
    else:
        st.caption("Detailed feedback form is not configured yet.")
