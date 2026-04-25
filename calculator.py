from dataclasses import dataclass, replace

from models import DealInput, DealMetrics


@dataclass(frozen=True)
class ScoringConfig:
    cash_flow_strong: float = 300.0
    cash_flow_positive: float = 100.0

    cash_on_cash_strong: float = 0.10
    cash_on_cash_acceptable: float = 0.06

    cap_rate_acceptable: float = 0.06

    dscr_strong: float = 1.25
    dscr_acceptable: float = 1.10

    rehab_moderate_pct: float = 0.10
    rehab_high_pct: float = 0.20

    vacancy_stress_increase_pct: float = 5.0
    vacancy_cash_flow_buffer: float = 100.0
    vacancy_dscr_floor: float = 1.10

    grade_a_min: int = 5
    grade_b_min: int = 3
    grade_c_min: int = 1


@dataclass(frozen=True)
class ScoringResult:
    grade: str
    verdict: str
    confidence: str
    strengths: list[str]
    concerns: list[str]
    score: int
    cash_flow_buffer_ratio: float | None = None
    vacancy_stress_cash_flow: float | None = None
    vacancy_stress_dscr: float | None = None


DEFAULT_SCORING_CONFIG = ScoringConfig()


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


def calculate_break_even_rent(deal: DealInput) -> float:
    """Calculate the monthly rent needed for zero monthly cash flow."""
    down_payment = deal.purchase_price * (deal.down_payment_pct / 100)
    loan_amount = deal.purchase_price - down_payment

    monthly_mortgage = calculate_monthly_mortgage(
        loan_amount=loan_amount,
        annual_interest_rate=deal.interest_rate,
        loan_term_years=deal.loan_term_years,
    )

    variable_expense_ratio = (
        deal.vacancy_pct
        + deal.property_management_pct
        + deal.maintenance_pct
    ) / 100

    if variable_expense_ratio >= 1:
        return float("inf")

    fixed_monthly_costs = (
        deal.property_tax_annual / 12
        + deal.insurance_annual / 12
        + deal.hoa_monthly
        + monthly_mortgage
    )

    return fixed_monthly_costs / (1 - variable_expense_ratio)


def build_scenario_deal(
    deal: DealInput,
    rent_increase: float = 0.0,
    purchase_price_adjustment: float = 0.0,
    interest_rate_change: float = 0.0,
) -> DealInput:
    """Return a copy of the deal with scenario adjustments applied."""
    return replace(
        deal,
        monthly_rent=max(0.0, deal.monthly_rent + rent_increase),
        purchase_price=max(0.0, deal.purchase_price + purchase_price_adjustment),
        interest_rate=max(0.0, deal.interest_rate + interest_rate_change),
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

def _grade_and_verdict(score: int, config: ScoringConfig) -> tuple[str, str]:
    if score >= config.grade_a_min:
        return "A", "Strong Buy"
    if score >= config.grade_b_min:
        return "B", "Buy"
    if score >= config.grade_c_min:
        return "C", "Maybe"
    return "D", "Pass"


def _confidence_level(
    metrics: DealMetrics,
    config: ScoringConfig,
    vacancy_stress_metrics: DealMetrics | None,
    high_rehab_risk: bool = False,
) -> str:
    stress_cash_flow = (
        vacancy_stress_metrics.monthly_cash_flow
        if vacancy_stress_metrics is not None
        else metrics.monthly_cash_flow
    )
    stress_dscr = (
        vacancy_stress_metrics.dscr
        if vacancy_stress_metrics is not None
        else metrics.dscr
    )
    has_debt_service = metrics.monthly_mortgage > 0

    if high_rehab_risk:
        return "Low"

    if (
        stress_cash_flow < 0
        or (has_debt_service and stress_dscr < config.vacancy_dscr_floor)
    ):
        return "Low"

    if (
        metrics.monthly_cash_flow >= config.cash_flow_strong
        and stress_cash_flow >= config.vacancy_cash_flow_buffer
        and (
            not has_debt_service
            or (
                metrics.dscr >= config.dscr_strong
                and stress_dscr >= config.vacancy_dscr_floor
            )
        )
    ):
        return "High"

    return "Medium"


def score_deal_detailed(
    metrics: DealMetrics,
    deal: DealInput | None = None,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> ScoringResult:
    """Score a deal with configurable rules and return explanatory details."""
    score = 0
    strengths = []
    concerns = []
    high_rehab_risk = False
    cash_flow_buffer_ratio = (
        metrics.monthly_cash_flow / metrics.monthly_mortgage
        if metrics.monthly_mortgage > 0
        else None
    )

    if metrics.monthly_cash_flow >= config.cash_flow_strong:
        score += 2
        strengths.append("Healthy monthly cash flow")
    elif metrics.monthly_cash_flow >= config.cash_flow_positive:
        score += 1
        strengths.append("Positive monthly cash flow")
    else:
        score -= 2
        concerns.append("Weak or negative monthly cash flow")

    if metrics.cash_on_cash_return >= config.cash_on_cash_strong:
        score += 2
        strengths.append("Strong cash-on-cash return")
    elif metrics.cash_on_cash_return >= config.cash_on_cash_acceptable:
        score += 1
        strengths.append("Acceptable cash-on-cash return")
    else:
        score -= 1
        concerns.append("Low cash-on-cash return")

    if metrics.cap_rate >= config.cap_rate_acceptable:
        score += 1
        strengths.append("Reasonable cap rate")
    else:
        score -= 1
        concerns.append("Cap rate is on the low side")

    if metrics.dscr >= config.dscr_strong:
        score += 2
        strengths.append("Healthy debt-service coverage")
    elif metrics.dscr >= config.dscr_acceptable:
        score += 1
        strengths.append("Adequate debt-service coverage")
    else:
        score -= 2
        concerns.append("Debt-service coverage is thin")

    vacancy_stress_metrics = None
    if deal is not None:
        if deal.purchase_price > 0:
            rehab_pct = deal.rehab_cost / deal.purchase_price
        elif deal.rehab_cost > 0:
            rehab_pct = float("inf")
        else:
            rehab_pct = 0.0

        if rehab_pct >= config.rehab_high_pct:
            score -= 2
            high_rehab_risk = True
            concerns.append("High rehab cost relative to purchase price")
        elif rehab_pct >= config.rehab_moderate_pct:
            score -= 1
            concerns.append("Moderate rehab cost relative to purchase price")

        stressed_deal = replace(
            deal,
            vacancy_pct=min(
                100.0,
                deal.vacancy_pct + config.vacancy_stress_increase_pct,
            ),
        )
        vacancy_stress_metrics = calculate_metrics(stressed_deal)
        stress_dscr_ok = (
            metrics.monthly_mortgage <= 0
            or vacancy_stress_metrics.dscr >= config.vacancy_dscr_floor
        )

        if (
            vacancy_stress_metrics.monthly_cash_flow >= config.vacancy_cash_flow_buffer
            and stress_dscr_ok
        ):
            strengths.append("Deal holds up under higher vacancy")
        elif vacancy_stress_metrics.monthly_cash_flow < 0:
            score -= 2
            concerns.append("Higher vacancy turns cash flow negative")
        elif (
            vacancy_stress_metrics.monthly_cash_flow < config.vacancy_cash_flow_buffer
            or not stress_dscr_ok
        ):
            score -= 1
            concerns.append("Vacancy stress leaves a limited cash flow buffer")

    grade, verdict = _grade_and_verdict(score, config)
    confidence = _confidence_level(
        metrics,
        config,
        vacancy_stress_metrics,
        high_rehab_risk=high_rehab_risk,
    )

    return ScoringResult(
        grade=grade,
        verdict=verdict,
        confidence=confidence,
        strengths=strengths,
        concerns=concerns,
        score=score,
        cash_flow_buffer_ratio=cash_flow_buffer_ratio,
        vacancy_stress_cash_flow=(
            vacancy_stress_metrics.monthly_cash_flow
            if vacancy_stress_metrics is not None
            else None
        ),
        vacancy_stress_dscr=(
            vacancy_stress_metrics.dscr
            if vacancy_stress_metrics is not None
            else None
        ),
    )


def score_deal(metrics: DealMetrics) -> tuple[str, str, list[str], list[str]]:
    result = score_deal_detailed(metrics)
    return result.grade, result.verdict, result.strengths, result.concerns
