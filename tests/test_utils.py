import pytest

from utils import format_currency, format_delta, format_percent, parse_dollar_input


def test_parse_dollar_input_handles_comma_separated_values() -> None:
    assert parse_dollar_input("750,000") == 750000.0
    assert parse_dollar_input("1,000,000") == 1000000.0
    assert parse_dollar_input("2,500") == 2500.0


def test_parse_dollar_input_handles_blank_values() -> None:
    assert parse_dollar_input("") is None
    assert parse_dollar_input("   ") is None


def test_parse_dollar_input_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        parse_dollar_input("750k")

    with pytest.raises(ValueError):
        parse_dollar_input("-100")


def test_parse_dollar_input_handles_normal_numeric_strings() -> None:
    assert parse_dollar_input("750000") == 750000.0
    assert parse_dollar_input("2500") == 2500.0


def test_format_currency_formats_positive_value() -> None:
    assert format_currency(1234.5) == "$1,234.50"


def test_format_currency_formats_negative_value() -> None:
    assert format_currency(-1234.5) == "$-1,234.50"


def test_format_currency_formats_zero() -> None:
    assert format_currency(0.0) == "$0.00"


def test_format_percent_formats_decimal_ratio() -> None:
    assert format_percent(0.065) == "6.50%"


def test_format_delta_formats_plain_positive_and_negative_values() -> None:
    assert format_delta(1234.5) == "+1,234.50"
    assert format_delta(-1234.5) == "-1,234.50"


def test_format_delta_formats_currency_positive_and_negative_values() -> None:
    assert format_delta(1234.5, is_currency=True) == "+$1,234.50"
    assert format_delta(-1234.5, is_currency=True) == "-$1,234.50"


def test_format_delta_formats_percent_positive_and_negative_values() -> None:
    assert format_delta(0.0125, is_percent=True) == "+1.25%"
    assert format_delta(-0.0125, is_percent=True) == "-1.25%"


def test_format_delta_formats_zero_values_consistently() -> None:
    assert format_delta(0.0) == "+0.00"
    assert format_delta(0.0, is_currency=True) == "+$0.00"
    assert format_delta(0.0, is_percent=True) == "+0.00%"


def test_format_delta_prefers_currency_when_currency_and_percent_are_both_true() -> None:
    assert format_delta(0.0125, is_percent=True, is_currency=True) == "+$0.01"
