from utils import format_currency, format_delta, format_percent


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
