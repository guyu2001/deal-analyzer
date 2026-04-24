# Test Coverage Checklist

This checklist reflects the current codebase and the tests that exist today.

## Run Tests

From the repo root on Windows:

```powershell
.venv\Scripts\python -m pytest
.venv\Scripts\python -m pytest -v
```

## calculator.py

Covered:
- [x] `calculate_monthly_mortgage` basic happy path
- [x] `calculate_monthly_mortgage` zero-interest path
- [x] `calculate_monthly_mortgage` non-positive loan amount path
- [x] `calculate_monthly_mortgage` short-term loan case
- [x] `calculate_metrics` default representative deal
- [x] `calculate_metrics` zero purchase price / `cap_rate == 0.0`
- [x] `calculate_metrics` zero cash invested / `cash_on_cash_return == 0.0`
- [x] `calculate_metrics` zero debt service / `dscr == 0.0`
- [x] `calculate_break_even_rent` normal case
- [x] `calculate_break_even_rent` zero-mortgage / cash purchase case
- [x] `calculate_break_even_rent` impossible case when variable expenses hit 100%
- [x] `build_scenario_deal` applies adjustments correctly
- [x] `build_scenario_deal` clamps negative outputs to zero
- [x] `build_scenario_deal` does not mutate original deal
- [x] `build_scenario_deal` with no adjustments returns unchanged values
- [x] Scenario-adjusted metrics flow through `calculate_metrics`
- [x] `score_deal` `Strong Buy`
- [x] `score_deal` `Buy`
- [x] `score_deal` `Maybe`
- [x] `score_deal` `Pass`
- [x] Exact threshold boundary tests for `100`, `300`, `0.06`, `0.10`, `1.10`, `1.25`
- [x] Grade/verdict cutoff boundary tests

Not yet covered:
- [ ] Additional oddball financing inputs beyond the current representative cases

## utils.py

Covered:
- [x] `format_currency` positive
- [x] `format_currency` negative
- [x] `format_currency` zero
- [x] `format_percent` standard decimal ratio
- [x] `format_delta` plain positive/negative
- [x] `format_delta` currency positive/negative
- [x] `format_delta` percent positive/negative
- [x] `format_delta(0)` behavior
- [x] Precedence when both `is_percent=True` and `is_currency=True`

Not yet covered:
- [ ] Larger rounding edge cases

## models.py

Not yet covered:
- [ ] No direct tests for `DealInput`
- [ ] No direct tests for `DealMetrics`

Notes:
- These are simple dataclasses, so lack of direct tests is acceptable for now.

## ai_analysis.py

Covered:
- [x] Missing `OPENAI_API_KEY` path
- [x] Prompt assembly correctness for `generate_ai_analysis`
- [x] OpenAI client call shape
- [x] Exception handling path
- [x] Empty `strengths` / `concerns` formatting
- [x] Scenario-context prompt assembly for `generate_what_would_make_this_work`

Notes:
- OpenAI calls are mocked in tests; no real API requests are made.

## prompts.py

Not yet covered:
- [ ] No tests for prompt constants or expected prompt structure

## app.py

Not yet covered:
- [ ] Streamlit input wiring
- [ ] Scenario comparison rendering
- [ ] "What Changed" messaging logic
- [ ] AI button / session-state behavior

Notes:
- This is intentionally untested right now because we prioritized pure-function coverage and avoided UI-heavy tests.

## Summary

Strongly covered:
- [x] `calculator.py`
- [x] `utils.py`

Lightly or not covered:
- [ ] `models.py`
- [ ] `ai_analysis.py`
- [ ] `prompts.py`
- [ ] `app.py`

## Next Best Tests To Add

1. A small extraction from `app.py` for "What Changed" so that logic can be tested without testing Streamlit directly
2. Additional prompt-structure assertions if the prompt format becomes more complex
3. Broader edge-case tests for unusual financing and expense combinations
