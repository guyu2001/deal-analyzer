from ai_usage import (
    AI_USAGE_COUNT_KEY,
    DEFAULT_AI_USAGE_LIMIT,
    ensure_ai_usage_state,
    get_ai_usage_count,
    is_ai_usage_limit_reached,
    record_ai_usage,
)


def test_ai_usage_state_starts_at_zero() -> None:
    session_state = {}

    ensure_ai_usage_state(session_state)

    assert session_state[AI_USAGE_COUNT_KEY] == 0
    assert get_ai_usage_count(session_state) == 0


def test_record_ai_usage_increments_until_limit() -> None:
    session_state = {}

    for _ in range(DEFAULT_AI_USAGE_LIMIT):
        assert record_ai_usage(session_state) is True

    assert get_ai_usage_count(session_state) == DEFAULT_AI_USAGE_LIMIT
    assert is_ai_usage_limit_reached(session_state) is True
    assert record_ai_usage(session_state) is False
    assert get_ai_usage_count(session_state) == DEFAULT_AI_USAGE_LIMIT


def test_custom_ai_usage_limit() -> None:
    session_state = {}

    assert record_ai_usage(session_state, limit=1) is True
    assert is_ai_usage_limit_reached(session_state, limit=1) is True
    assert record_ai_usage(session_state, limit=1) is False
