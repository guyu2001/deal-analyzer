DEFAULT_AI_USAGE_LIMIT = 5
AI_USAGE_COUNT_KEY = "ai_usage_count"


def ensure_ai_usage_state(session_state: dict) -> None:
    if AI_USAGE_COUNT_KEY not in session_state:
        session_state[AI_USAGE_COUNT_KEY] = 0


def get_ai_usage_count(session_state: dict) -> int:
    ensure_ai_usage_state(session_state)
    return int(session_state[AI_USAGE_COUNT_KEY])


def is_ai_usage_limit_reached(
    session_state: dict,
    limit: int = DEFAULT_AI_USAGE_LIMIT,
) -> bool:
    return get_ai_usage_count(session_state) >= limit


def record_ai_usage(
    session_state: dict,
    limit: int = DEFAULT_AI_USAGE_LIMIT,
) -> bool:
    if is_ai_usage_limit_reached(session_state, limit):
        return False

    session_state[AI_USAGE_COUNT_KEY] = get_ai_usage_count(session_state) + 1
    return True
