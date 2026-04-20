from dataclasses import dataclass

@dataclass
class DealInput:
    purchase_price: float
    monthly_rent: float
    down_payment_pct: float
    interest_rate: float
    loan_term_years: int

    property_tax_annual: float
    insurance_annual: float
    maintenance_pct: float
    vacancy_pct: float
    property_management_pct: float
    hoa_monthly: float

    closing_costs: float
    rehab_cost: float


@dataclass
class DealMetrics:
    monthly_mortgage: float
    monthly_cash_flow: float
    annual_cash_flow: float
    noi_annual: float

    cap_rate: float
    cash_on_cash_return: float
    dscr: float

    total_cash_invested: float