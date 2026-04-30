def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def parse_dollar_input(value: str) -> float | None:
    cleaned_value = value.strip().replace(",", "").replace("$", "")
    if cleaned_value == "":
        return None

    try:
        parsed_value = float(cleaned_value)
    except ValueError as exc:
        raise ValueError("Enter a valid dollar amount.") from exc

    if parsed_value < 0:
        raise ValueError("Enter a dollar amount of 0 or more.")

    return parsed_value


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def format_delta(
    value: float,
    is_percent: bool = False,
    is_currency: bool = False,
) -> str:
    if is_currency:
        return f"{value:+,.2f}".replace("+", "+$", 1).replace("-", "-$", 1)
    if is_percent:
        return f"{value * 100:+.2f}%"
    return f"{value:+,.2f}"
