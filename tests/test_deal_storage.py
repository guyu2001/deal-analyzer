import json

import pytest

from deal_storage import get_deal_path, list_saved_deals, load_deal, sanitize_deal_name, save_deal


def test_sanitize_deal_name_creates_safe_filename() -> None:
    assert sanitize_deal_name(" 123 Main St. / Duplex ") == "123-main-st-duplex"
    assert sanitize_deal_name("!!!") == "untitled-deal"


def test_save_deal_creates_storage_dir_and_writes_json(temporary_storage_dir, make_deal) -> None:
    deal = make_deal()

    saved_path = save_deal("123 Main St", deal, temporary_storage_dir)

    assert saved_path == get_deal_path("123 Main St", temporary_storage_dir)
    assert saved_path.exists()

    with saved_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    assert payload == {
        "purchase_price": pytest.approx(350000.0),
        "monthly_rent": pytest.approx(2500.0),
        "down_payment_pct": pytest.approx(25.0),
        "interest_rate": pytest.approx(6.5),
        "loan_term_years": 30,
        "property_tax_annual": pytest.approx(4200.0),
        "insurance_annual": pytest.approx(1200.0),
        "maintenance_pct": pytest.approx(8.0),
        "vacancy_pct": pytest.approx(5.0),
        "property_management_pct": pytest.approx(8.0),
        "hoa_monthly": pytest.approx(0.0),
        "closing_costs": pytest.approx(7000.0),
        "rehab_cost": pytest.approx(5000.0),
    }


def test_save_deal_overwrites_existing_file_with_same_name(temporary_storage_dir, make_deal) -> None:
    save_deal("My Deal", make_deal(monthly_rent=2500.0), temporary_storage_dir)

    save_deal("My Deal", make_deal(monthly_rent=2800.0), temporary_storage_dir)
    loaded = load_deal("My Deal", temporary_storage_dir)

    assert loaded["monthly_rent"] == pytest.approx(2800.0)


def test_list_saved_deals_returns_sorted_sanitized_names(temporary_storage_dir, make_deal) -> None:
    save_deal("Z Deal", make_deal(), temporary_storage_dir)
    save_deal("A Deal", make_deal(), temporary_storage_dir)

    assert list_saved_deals(temporary_storage_dir) == ["a-deal", "z-deal"]


def test_load_deal_returns_saved_inputs(temporary_storage_dir, make_deal) -> None:
    save_deal("Triplex", make_deal(interest_rate=5.75, rehab_cost=12000.0), temporary_storage_dir)

    loaded = load_deal("Triplex", temporary_storage_dir)

    assert loaded["interest_rate"] == pytest.approx(5.75)
    assert loaded["rehab_cost"] == pytest.approx(12000.0)
    assert loaded["loan_term_years"] == 30


def test_load_deal_raises_for_missing_file(temporary_storage_dir) -> None:
    with pytest.raises(FileNotFoundError):
        load_deal("missing-deal", temporary_storage_dir)
