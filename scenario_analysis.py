from dataclasses import dataclass
from typing import Literal

from models import DealInput, DealMetrics
from utils import format_currency, format_delta, format_percent


FormatterName = Literal["currency", "percent", "number"]


@dataclass(frozen=True)
class ScenarioComparisonRow:
    label: str
    original: float
    scenario: float
    formatter: FormatterName

    @property
    def delta(self) -> float:
        return self.scenario - self.original

    def format_value(self, value: float) -> str:
        if self.formatter == "currency":
            return format_currency(value)
        if self.formatter == "percent":
            return format_percent(value)
        return f"{value:.2f}"

    def format_original(self) -> str:
        return self.format_value(self.original)

    def format_scenario_with_delta(self) -> str:
        return (
            f"{self.format_value(self.scenario)} "
            f"({format_delta(self.delta, is_percent=self.formatter == 'percent', is_currency=self.formatter == 'currency')})"
        )


def build_scenario_comparison_rows(
    original_deal: DealInput,
    scenario_deal: DealInput,
    original_metrics: DealMetrics,
    scenario_metrics: DealMetrics,
) -> list[ScenarioComparisonRow]:
    return [
        ScenarioComparisonRow(
            "Monthly Rent",
            original_deal.monthly_rent,
            scenario_deal.monthly_rent,
            "currency",
        ),
        ScenarioComparisonRow(
            "Purchase Price",
            original_deal.purchase_price,
            scenario_deal.purchase_price,
            "currency",
        ),
        ScenarioComparisonRow(
            "Interest Rate",
            original_deal.interest_rate / 100,
            scenario_deal.interest_rate / 100,
            "percent",
        ),
        ScenarioComparisonRow(
            "Monthly Cash Flow",
            original_metrics.monthly_cash_flow,
            scenario_metrics.monthly_cash_flow,
            "currency",
        ),
        ScenarioComparisonRow(
            "Annual Cash Flow",
            original_metrics.annual_cash_flow,
            scenario_metrics.annual_cash_flow,
            "currency",
        ),
        ScenarioComparisonRow(
            "Cash-on-Cash Return",
            original_metrics.cash_on_cash_return,
            scenario_metrics.cash_on_cash_return,
            "percent",
        ),
        ScenarioComparisonRow(
            "Cap Rate",
            original_metrics.cap_rate,
            scenario_metrics.cap_rate,
            "percent",
        ),
        ScenarioComparisonRow(
            "DSCR",
            original_metrics.dscr,
            scenario_metrics.dscr,
            "number",
        ),
    ]


def build_scenario_change_messages(
    original_metrics: DealMetrics,
    scenario_metrics: DealMetrics,
    original_verdict: str,
    scenario_verdict: str,
) -> list[str]:
    messages = []

    if scenario_metrics.monthly_cash_flow > original_metrics.monthly_cash_flow:
        messages.append(
            "Monthly cash flow improved by "
            f"{format_currency(scenario_metrics.monthly_cash_flow - original_metrics.monthly_cash_flow)}."
        )

    if scenario_metrics.cash_on_cash_return > original_metrics.cash_on_cash_return:
        messages.append(
            "Cash-on-cash return improved by "
            f"{format_delta(scenario_metrics.cash_on_cash_return - original_metrics.cash_on_cash_return, is_percent=True)}."
        )

    if scenario_metrics.dscr > original_metrics.dscr:
        messages.append(f"DSCR improved by {scenario_metrics.dscr - original_metrics.dscr:.2f}.")

    if scenario_verdict != original_verdict:
        messages.append(f"Verdict changed from {original_verdict} to {scenario_verdict}.")

    return messages
