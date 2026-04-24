import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from models import DealInput, DealMetrics


@pytest.fixture
def make_deal():
    def _make_deal(**overrides: float) -> DealInput:
        deal = DealInput(
            purchase_price=350000.0,
            monthly_rent=2500.0,
            down_payment_pct=25.0,
            interest_rate=6.5,
            loan_term_years=30,
            property_tax_annual=4200.0,
            insurance_annual=1200.0,
            maintenance_pct=8.0,
            vacancy_pct=5.0,
            property_management_pct=8.0,
            hoa_monthly=0.0,
            closing_costs=7000.0,
            rehab_cost=5000.0,
        )

        for field_name, value in overrides.items():
            setattr(deal, field_name, value)

        return deal

    return _make_deal


@pytest.fixture
def make_metrics():
    def _make_metrics(**overrides: float) -> DealMetrics:
        metrics = DealMetrics(
            monthly_mortgage=1500.0,
            monthly_cash_flow=150.0,
            annual_cash_flow=1800.0,
            noi_annual=22000.0,
            cap_rate=0.065,
            cash_on_cash_return=0.07,
            dscr=1.15,
            total_cash_invested=45000.0,
        )

        for field_name, value in overrides.items():
            setattr(metrics, field_name, value)

        return metrics

    return _make_metrics


@pytest.fixture
def temporary_storage_dir():
    storage_dir = Path(".tmp") / "test_saved_deals" / uuid4().hex
    storage_dir.mkdir(parents=True, exist_ok=True)
    yield storage_dir
    shutil.rmtree(storage_dir, ignore_errors=True)
