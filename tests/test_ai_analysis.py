import ai_analysis


class FakeResponses:
    def __init__(self, output_text: str = "Mocked AI response", should_raise: bool = False):
        self.output_text = output_text
        self.should_raise = should_raise
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.should_raise:
            raise RuntimeError("boom")
        return type("FakeResponse", (), {"output_text": self.output_text})()


class FakeClient:
    def __init__(self, responses: FakeResponses):
        self.responses = responses


def test_generate_ai_analysis_returns_missing_key_message_without_api_call(monkeypatch, make_deal) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = ai_analysis.generate_ai_analysis(
        make_deal(),
        ai_analysis.DealMetrics(
            monthly_mortgage=1000.0,
            monthly_cash_flow=200.0,
            annual_cash_flow=2400.0,
            noi_annual=18000.0,
            cap_rate=0.06,
            cash_on_cash_return=0.08,
            dscr=1.2,
            total_cash_invested=50000.0,
        ),
        "Buy",
        ["Positive monthly cash flow"],
        ["Cap rate is on the low side"],
    )

    assert result == "OpenAI API key is not configured. Add it to Streamlit secrets or OPENAI_API_KEY."


def test_get_openai_api_key_prefers_streamlit_secrets(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    result = ai_analysis.get_openai_api_key({"OPENAI_API_KEY": "secret-key"})

    assert result == "secret-key"


def test_get_openai_api_key_falls_back_to_environment(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    result = ai_analysis.get_openai_api_key({})

    assert result == "env-key"


def test_get_openai_api_key_returns_none_when_missing(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = ai_analysis.get_openai_api_key({})

    assert result is None


def test_generate_ai_analysis_calls_openai_with_expected_prompt_content(
    monkeypatch,
    make_deal,
    make_metrics,
) -> None:
    responses = FakeResponses(output_text="Analysis complete")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(ai_analysis, "OpenAI", lambda api_key: FakeClient(responses))

    result = ai_analysis.generate_ai_analysis(
        make_deal(),
        make_metrics(),
        "Buy",
        ["Positive monthly cash flow"],
        ["Cap rate is on the low side"],
    )

    assert result == "Analysis complete"
    assert len(responses.calls) == 1
    assert responses.calls[0]["model"] == "gpt-5.4-mini"
    assert responses.calls[0]["input"][0]["content"] == ai_analysis.SYSTEM_PROMPT
    user_prompt = responses.calls[0]["input"][1]["content"]
    assert "Purchase Price: 350000.0" in user_prompt
    assert "Current" not in user_prompt
    assert "Rule-based verdict:\nBuy" in user_prompt
    assert "- Positive monthly cash flow" in user_prompt
    assert "- Cap rate is on the low side" in user_prompt


def test_generate_ai_analysis_formats_empty_lists_and_handles_exceptions(
    monkeypatch,
    make_deal,
    make_metrics,
) -> None:
    responses = FakeResponses(should_raise=True)

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(ai_analysis, "OpenAI", lambda api_key: FakeClient(responses))

    result = ai_analysis.generate_ai_analysis(
        make_deal(),
        make_metrics(),
        "Pass",
        [],
        [],
    )

    user_prompt = responses.calls[0]["input"][1]["content"]
    assert "Rule-based strengths:\n- None" in user_prompt
    assert "Rule-based concerns:\n- None" in user_prompt
    assert result == "AI analysis failed: boom"


def test_generate_what_would_make_this_work_uses_scenario_context(
    monkeypatch,
    make_deal,
    make_metrics,
) -> None:
    responses = FakeResponses(output_text="Workable with better terms")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(ai_analysis, "OpenAI", lambda api_key: FakeClient(responses))

    result = ai_analysis.generate_what_would_make_this_work(
        deal=make_deal(),
        metrics=make_metrics(),
        grade="C",
        verdict="Maybe",
        strengths=["Positive monthly cash flow"],
        concerns=["Cap rate is on the low side"],
        scenario_deal=make_deal(monthly_rent=2700.0, purchase_price=340000.0, interest_rate=6.0),
        scenario_metrics=make_metrics(
            monthly_cash_flow=350.0,
            annual_cash_flow=4200.0,
            cap_rate=0.07,
            cash_on_cash_return=0.10,
            dscr=1.25,
        ),
        scenario_grade="A",
        scenario_verdict="Strong Buy",
    )

    assert result == "Workable with better terms"
    assert len(responses.calls) == 1
    user_prompt = responses.calls[0]["input"][1]["content"]
    assert "Current rule-based grade: C" in user_prompt
    assert "Current rule-based verdict: Maybe" in user_prompt
    assert "Scenario rule-based grade: A" in user_prompt
    assert "Scenario rule-based verdict: Strong Buy" in user_prompt
    assert "Monthly Rent: 2700.0" in user_prompt
    assert "Purchase Price: 340000.0" in user_prompt


def test_generate_what_would_make_this_work_handles_api_exceptions(
    monkeypatch,
    make_deal,
    make_metrics,
) -> None:
    responses = FakeResponses(should_raise=True)

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(ai_analysis, "OpenAI", lambda api_key: FakeClient(responses))

    result = ai_analysis.generate_what_would_make_this_work(
        deal=make_deal(),
        metrics=make_metrics(),
        grade="D",
        verdict="Pass",
        strengths=[],
        concerns=["Weak or negative monthly cash flow"],
        scenario_deal=make_deal(),
        scenario_metrics=make_metrics(),
        scenario_grade="D",
        scenario_verdict="Pass",
    )

    assert result == "AI analysis failed: boom"
