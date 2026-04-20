from models import DealInput, DealMetrics


def calculate_monthly_mortgage(
    loan_amount: float,
    annual_interest_rate: float,
    loan_term_years: int,
) -> float:
    """Calculate the monthly principal + interest payment."""
    monthly_rate = annual_interest_rate / 100 / 12
    number_of_payments = loan_term_years * 12

    if loan_amount <= 0:
        return 0.0

    if monthly_rate == 0:
        return loan_amount / number_of_payments

    return loan_amount * (
        monthly_rate * (1 + monthly_rate) ** number_of_payments
    ) / (
        (1 + monthly_rate) ** number_of_payments - 1
    )


def calculate_metrics(deal: DealInput) -> DealMetrics:
    down_payment = deal.purchase_price * (deal.down_payment_pct / 100)
    loan_amount = deal.purchase_price - down_payment

    monthly_mortgage = calculate_monthly_mortgage(
        loan_amount=loan_amount,
        annual_interest_rate=deal.interest_rate,
        loan_term_years=deal.loan_term_years,
    )

    vacancy_monthly = deal.monthly_rent * (deal.vacancy_pct / 100)
    management_monthly = deal.monthly_rent * (deal.property_management_pct / 100)
    maintenance_monthly = deal.monthly_rent * (deal.maintenance_pct / 100)

    property_tax_monthly = deal.property_tax_annual / 12
    insurance_monthly = deal.insurance_annual / 12

    monthly_operating_expenses = (
        vacancy_monthly
        + management_monthly
        + maintenance_monthly
        + property_tax_monthly
        + insurance_monthly
        + deal.hoa_monthly
    )

    monthly_cash_flow = (
        deal.monthly_rent
        - monthly_operating_expenses
        - monthly_mortgage
    )

    annual_cash_flow = monthly_cash_flow * 12

    noi_annual = (
        deal.monthly_rent * 12
        - monthly_operating_expenses * 12
    )

    cap_rate = noi_annual / deal.purchase_price if deal.purchase_price > 0 else 0.0

    total_cash_invested = (
        down_payment
        + deal.closing_costs
        + deal.rehab_cost
    )

    cash_on_cash_return = (
        annual_cash_flow / total_cash_invested
        if total_cash_invested > 0 else 0.0
    )

    annual_debt_service = monthly_mortgage * 12
    dscr = noi_annual / annual_debt_service if annual_debt_service > 0 else 0.0

    return DealMetrics(
        monthly_mortgage=monthly_mortgage,
        monthly_cash_flow=monthly_cash_flow,
        annual_cash_flow=annual_cash_flow,
        noi_annual=noi_annual,
        cap_rate=cap_rate,
        cash_on_cash_return=cash_on_cash_return,
        dscr=dscr,
        total_cash_invested=total_cash_invested,
    )

def score_deal(metrics: DealMetrics) -> tuple[str, str, list[str], list[str]]:
    """
    Return:
    - verdict: Strong Buy / Maybe / Pass
    - strengths: list of positive signals
    - concerns: list of negative signals
    """
    score = 0
    strengths = []
    concerns = []

    if metrics.monthly_cash_flow >= 300:
        score += 2
        strengths.append("Healthy monthly cash flow")
    elif metrics.monthly_cash_flow >= 100:
        score += 1
        strengths.append("Positive monthly cash flow")
    else:
        score -= 2
        concerns.append("Weak or negative monthly cash flow")

    if metrics.cash_on_cash_return >= 0.10:
        score += 2
        strengths.append("Strong cash-on-cash return")
    elif metrics.cash_on_cash_return >= 0.06:
        score += 1
        strengths.append("Acceptable cash-on-cash return")
    else:
        score -= 1
        concerns.append("Low cash-on-cash return")

    if metrics.cap_rate >= 0.06:
        score += 1
        strengths.append("Reasonable cap rate")
    else:
        score -= 1
        concerns.append("Cap rate is on the low side")

    if metrics.dscr >= 1.25:
        score += 2
        strengths.append("Healthy debt-service coverage")
    elif metrics.dscr >= 1.10:
        score += 1
        strengths.append("Adequate debt-service coverage")
    else:
        score -= 2
        concerns.append("Debt-service coverage is thin")
    
    if score >= 5:
        grade = "A"
        verdict = "Strong Buy"
    elif score >= 3:
        grade = "B"
        verdict = "Buy"
    elif score >= 1:
        grade = "C"
        verdict = "Maybe"
    else:
        grade = "D"
        verdict = "Pass"

    return grade, verdict, strengths, concerns