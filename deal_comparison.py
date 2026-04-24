from calculator import calculate_metrics, score_deal
from models import DealInput


GRADE_RANK = {
    "A": 4,
    "B": 3,
    "C": 2,
    "D": 1,
}


def deal_input_from_dict(data: dict[str, float | int]) -> DealInput:
    return DealInput(
        purchase_price=float(data["purchase_price"]),
        monthly_rent=float(data["monthly_rent"]),
        down_payment_pct=float(data["down_payment_pct"]),
        interest_rate=float(data["interest_rate"]),
        loan_term_years=int(data["loan_term_years"]),
        property_tax_annual=float(data["property_tax_annual"]),
        insurance_annual=float(data["insurance_annual"]),
        maintenance_pct=float(data["maintenance_pct"]),
        vacancy_pct=float(data["vacancy_pct"]),
        property_management_pct=float(data["property_management_pct"]),
        hoa_monthly=float(data["hoa_monthly"]),
        closing_costs=float(data["closing_costs"]),
        rehab_cost=float(data["rehab_cost"]),
    )


def compare_values(value_a: float, value_b: float, higher_is_better: bool = True) -> tuple[str, str]:
    if value_a == value_b:
        return "Tie", "Tie"
    if higher_is_better:
        return ("Better", "") if value_a > value_b else ("", "Better")
    return ("Better", "") if value_a < value_b else ("", "Better")


def compare_grades(grade_a: str, grade_b: str) -> tuple[str, str]:
    return compare_values(GRADE_RANK[grade_a], GRADE_RANK[grade_b], higher_is_better=True)


def build_deal_comparison(saved_deal_a: dict[str, float | int], saved_deal_b: dict[str, float | int]) -> dict:
    deal_a = deal_input_from_dict(saved_deal_a)
    deal_b = deal_input_from_dict(saved_deal_b)

    metrics_a = calculate_metrics(deal_a)
    metrics_b = calculate_metrics(deal_b)

    grade_a, verdict_a, _, _ = score_deal(metrics_a)
    grade_b, verdict_b, _, _ = score_deal(metrics_b)

    return {
        "deal_a": deal_a,
        "deal_b": deal_b,
        "metrics_a": metrics_a,
        "metrics_b": metrics_b,
        "grade_a": grade_a,
        "grade_b": grade_b,
        "verdict_a": verdict_a,
        "verdict_b": verdict_b,
    }
