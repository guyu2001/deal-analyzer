import os

from dotenv import load_dotenv
from openai import OpenAI

from models import DealInput, DealMetrics
from prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    WHAT_WOULD_MAKE_THIS_WORK_TEMPLATE,
)


load_dotenv()


def get_openai_api_key(secrets=None) -> str | None:
    if secrets is None:
        try:
            import streamlit as st

            secrets = st.secrets
        except Exception:
            secrets = None

    if secrets is not None:
        try:
            api_key = secrets.get("OPENAI_API_KEY")
        except AttributeError:
            try:
                api_key = secrets["OPENAI_API_KEY"]
            except (KeyError, TypeError):
                api_key = None
        except Exception:
            api_key = None

        if api_key:
            return str(api_key)

    return os.getenv("OPENAI_API_KEY") or None


def _format_deal_inputs(deal: DealInput) -> str:
    return f"""
Purchase Price: {deal.purchase_price}
Monthly Rent: {deal.monthly_rent}
Down Payment %: {deal.down_payment_pct}
Interest Rate %: {deal.interest_rate}
Loan Term Years: {deal.loan_term_years}
Property Tax Annual: {deal.property_tax_annual}
Insurance Annual: {deal.insurance_annual}
Maintenance %: {deal.maintenance_pct}
Vacancy %: {deal.vacancy_pct}
Property Management %: {deal.property_management_pct}
HOA Monthly: {deal.hoa_monthly}
Closing Costs: {deal.closing_costs}
Rehab Cost: {deal.rehab_cost}
""".strip()


def _format_deal_metrics(metrics: DealMetrics) -> str:
    return f"""
Monthly Mortgage: {metrics.monthly_mortgage:.2f}
Monthly Cash Flow: {metrics.monthly_cash_flow:.2f}
Annual Cash Flow: {metrics.annual_cash_flow:.2f}
NOI Annual: {metrics.noi_annual:.2f}
Cap Rate: {metrics.cap_rate:.4f}
Cash-on-Cash Return: {metrics.cash_on_cash_return:.4f}
DSCR: {metrics.dscr:.4f}
Total Cash Invested: {metrics.total_cash_invested:.2f}
""".strip()


def _format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- None"


def _create_client() -> OpenAI | str:
    api_key = get_openai_api_key()
    if not api_key:
        return "OpenAI API key is not configured. Add it to Streamlit secrets or OPENAI_API_KEY."
    return OpenAI(api_key=api_key)


def generate_ai_analysis(
    deal: DealInput,
    metrics: DealMetrics,
    verdict: str,
    strengths: list[str],
    concerns: list[str],
) -> str:
    client = _create_client()
    if isinstance(client, str):
        return client

    user_prompt = USER_PROMPT_TEMPLATE.format(
        deal_inputs=_format_deal_inputs(deal),
        deal_metrics=_format_deal_metrics(metrics),
        verdict=verdict,
        strengths=_format_bullets(strengths),
        concerns=_format_bullets(concerns),
    )
    try:
        response = client.responses.create(
            model="gpt-5.4-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.output_text

    except Exception as e:
        return f"AI analysis failed: {str(e)}"


def generate_what_would_make_this_work(
    deal: DealInput,
    metrics: DealMetrics,
    grade: str,
    verdict: str,
    strengths: list[str],
    concerns: list[str],
    scenario_deal: DealInput,
    scenario_metrics: DealMetrics,
    scenario_grade: str,
    scenario_verdict: str,
) -> str:
    client = _create_client()
    if isinstance(client, str):
        return client

    user_prompt = WHAT_WOULD_MAKE_THIS_WORK_TEMPLATE.format(
        deal_inputs=_format_deal_inputs(deal),
        deal_metrics=_format_deal_metrics(metrics),
        grade=grade,
        verdict=verdict,
        strengths=_format_bullets(strengths),
        concerns=_format_bullets(concerns),
        scenario_inputs=_format_deal_inputs(scenario_deal),
        scenario_metrics=_format_deal_metrics(scenario_metrics),
        scenario_grade=scenario_grade,
        scenario_verdict=scenario_verdict,
    )

    try:
        response = client.responses.create(
            model="gpt-5.4-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.output_text
    except Exception as e:
        return f"AI analysis failed: {str(e)}"
