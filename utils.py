def format_currency(value: float) -> str:
    return f"${value:,.2f}"


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
