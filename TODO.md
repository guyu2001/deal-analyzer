# AI Deal Analyzer – TODO

## 🚀 Phase: Validation & Productization (Current Focus)

Goal:
Make the app usable by a new user with minimal context and gather early feedback,
while preserving future monetization options.

### Next Steps (Short Term)

- [x] Unified quick input flow
  - minimal inputs: price, rent
  - editable advanced assumptions
- [x] Assumption Transparency (show key assumptions clearly)
- [x] Confidence & Risk Clarity improvements
- [x] Shareable Deal Summary (copyable output)

### Guardrails

- Avoid adding heavy data integrations
- Avoid expanding feature surface too broadly
- Keep logic simple and explainable
- Preserve ability to introduce paid tiers later

### Product Direction

- Positioning: "AI second opinion for real estate deals"
- Focus on:
  - risk clarity
  - decision confidence
- Avoid competing on:
  - raw data
  - number of metrics

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
- Unified Analyze inputs so users start with deal name, price, and rent, then edit details only when needed
- Redesigned Deal Result into a verdict-first screen with numeric explanations and visible assumptions

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
- [x] Load saved deals from Portfolio ranking

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
- [x] Deal ranking / portfolio table
- [ ] Filtering by status (future)
- [ ] Aggregate cash flow (future)

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
- Added Quick Analysis Mode with price/rent-only inputs and clearly labeled default assumptions
- Added a copyable Shareable Summary with the current deal's key metrics, strengths, and concerns
- Added an editable Deal Name field used for saving, loading, and shareable summaries
- What I learned:
- Scenario logic is easier to trust when the display text is covered outside Streamlit.
- Quick analysis should use assumptions without overwriting the full underwriting inputs.
- Copyable plain text is enough for sharing early deal opinions without adding accounts or exports.
- Deal identity should be visible before saving, not introduced only at save time.
- Next step:
- Run the app against a real deal and capture any confusing inputs, labels, or defaults while using it.

### 2026-04-29
- What I built:
- Added first-time user onboarding to the Analyze tab with a concise app intro, Start here cue, and 3-step guide.
- Polished Quick Analysis so price and rent entry are prominent near the top, support comma-friendly input, and avoid duplicate lower inputs.
- Redesigned the Analyze tab into a cleaner hero, primary input card, primary result card, and collapsed secondary sections.
- What I learned:
- First user feedback: the app was not straightforward enough to understand what it does or where to start.
- Follow-up UX feedback: the app still felt like a college project, price entry was hard to find, and typing lots of zeros was error-prone.
- Latest UX feedback: the Analyze tab still felt too much like an engineering dashboard instead of a polished product flow.
- Next step:
- Watch whether new users can start with Quick Analysis within 5 seconds without extra explanation.
- Watch whether comma-friendly top-level inputs reduce entry mistakes for larger purchase prices.
- Watch whether the input card to result card flow makes the first screen self-explanatory.

### 2026-05-01
- What I built:
- Moved save/load management into a more natural flow: saving stays near the current deal, loading happens from Portfolio.
- Redesigned Deal Result around the verdict first, with supporting metrics below instead of competing for attention.
- Added numeric verdict explanations using cash flow, cash-on-cash return, DSCR, and stressed cash flow where relevant.
- Replaced the Quick vs Full Analysis toggle with one unified input flow and an Advanced assumptions expander.
- Added a visible assumptions-used line directly under the verdict explanation so users can see the key underwriting assumptions behind the verdict.
- Verified the final app state with `python -m py_compile app.py` and `python -m pytest` passing 79 tests.
- What I learned:
- The app feels more trustworthy when it explains the verdict with numbers before showing a grid of metrics.
- Advanced inputs should be available without making the first screen feel like an underwriting spreadsheet.
- Small assumption transparency belongs near the decision, not hidden after the metrics.
- Next step:
- Use the app on a real candidate deal and note which explanation, assumption, or threshold still feels unclear.
