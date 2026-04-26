# AI Deal Analyzer – TODO

## Current Status
- ✅ Environment setup complete
- ✅ Calculator working
- ✅ Basic scoring (verdict + strengths/concerns)
- ✅ AI analysis integrated
- ✅ Button-triggered AI (cost controlled)
- ✅ Deal grade (A/B/C/D)

## Completed Recently
- Local save/load for deal inputs using JSON files in `saved_deals/`
- Side-by-side comparison for two saved deals with metric highlights

---

## Next Session (High Priority)

### 1. Scenario Analysis (BIG upgrade)
Goal: Answer “What would make this a good deal?”

- [x] Add inputs for scenario tweaks:
  - rent increase
  - purchase price adjustment
  - interest rate change
- [x] Recalculate metrics dynamically
- [x] Show side-by-side comparison:
  - Original vs Scenario
- [x] Highlight what changed (cash flow, CoC, etc.)

---

### 2. AI “What Would Make This Work”
- [x] Add a second AI button:
  - “How to improve this deal”
- [x] Prompt should:
  - suggest target price
  - suggest rent improvements
  - identify biggest lever
- [x] Output actionable negotiation ideas

---

## Medium Priority (Product Thinking)

### 3. Save Deal Locally
- [x] Save deal inputs to JSON
- [x] Load previous deals
- [x] Simple dropdown to switch deals

---

### 4. Deal Comparison
- [x] Compare 2 deals side-by-side
- [x] Highlight best metrics visually

---

### 5. Better Scoring Logic
- [x] Make scoring configurable
- [x] Add:
  - rehab risk weighting
  - vacancy sensitivity
- [x] Add “confidence level”

---

## Longer-Term Ideas (Do NOT build yet)

### 6. Deal Sourcing
- [ ] Zillow / Redfin scraping (later)
- [ ] Auto-import deal data

### 7. Portfolio View
- [ ] Multiple properties
- [ ] Aggregate cash flow

### 8. Turn into SaaS
- [ ] User accounts
- [ ] Hosted version
- [ ] Subscription model

---

## Personal Notes

- Focus on:
  - decision quality > features
  - speed > perfection
- Only build what you personally use
- Avoid overengineering

---

## Definition of Success (Next Milestone)

“I used this tool to evaluate a real deal and it changed my decision.”


## Session Log

### YYYY-MM-DD
- What I built:
- Scenario analysis with rent, price, and rate adjustments
- Original vs Scenario comparison with metric deltas
- What I learned:
- Next step:

### 2026-04-25
- What I built:
- Configurable scoring thresholds with detailed scoring results
- Rehab risk weighting and higher-vacancy stress testing
- Confidence level output for main deal ratings
- Tests for scoring thresholds, risk penalties, vacancy stress, confidence, and score_deal compatibility
- What I learned:
- Deal grade is more useful when paired with confidence, because fragile deals can look good before stress testing.
- Next step:
- Use the tool on a real deal and tune the default thresholds if your target buy box differs.

### 2026-04-26
- What I built:
- Extracted scenario comparison rows and "What Changed" messages into `scenario_analysis.py`
- Added focused tests for scenario row formatting, metric deltas, improvement messages, and no-change behavior
- Updated README and test coverage docs for the current feature set
- What I learned:
- Scenario logic is easier to trust when the display text is covered outside Streamlit.
- Next step:
- Run the app against a real deal and capture any confusing inputs, labels, or defaults while using it.
