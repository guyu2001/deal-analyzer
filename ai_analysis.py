import os
from xmlrpc import client

from dotenv import load_dotenv
from openai import OpenAI

from models import DealInput, DealMetrics
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


load_dotenv()


def generate_ai_analysis(
    deal: DealInput,
    metrics: DealMetrics,
    verdict: str,
    strengths: list[str],
    concerns: list[str],
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OPENAI_API_KEY not found in .env file."

    client = OpenAI(api_key=api_key)

    deal_inputs = f"""
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

    deal_metrics = f"""
Monthly Mortgage: {metrics.monthly_mortgage:.2f}
Monthly Cash Flow: {metrics.monthly_cash_flow:.2f}
Annual Cash Flow: {metrics.annual_cash_flow:.2f}
NOI Annual: {metrics.noi_annual:.2f}
Cap Rate: {metrics.cap_rate:.4f}
Cash-on-Cash Return: {metrics.cash_on_cash_return:.4f}
DSCR: {metrics.dscr:.4f}
Total Cash Invested: {metrics.total_cash_invested:.2f}
""".strip()

    user_prompt = USER_PROMPT_TEMPLATE.format(
        deal_inputs=deal_inputs,
        deal_metrics=deal_metrics,
        verdict=verdict,
        strengths="\n".join(f"- {item}" for item in strengths) if strengths else "- None",
        concerns="\n".join(f"- {item}" for item in concerns) if concerns else "- None",
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
    
    return response.output_text