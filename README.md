# AI Deal Analyzer

A personal rental property analysis tool built with Streamlit and OpenAI.

## Features

- Analyze one rental property deal at a time
- Calculate:
  - monthly mortgage
  - monthly cash flow
  - annual cash flow
  - NOI
  - cap rate
  - cash-on-cash return
  - DSCR
  - total cash invested
- Generate a rule-based verdict
- Show a deal grade and confidence level
- Generate optional AI analysis
- Ask AI how to improve a weak or borderline deal
- Test scenario tweaks for rent, purchase price, and interest rate
- Compare original vs scenario metrics with deltas
- Save and load deal inputs locally from `saved_deals/`
- Compare two saved deals side-by-side

## Setup

1. Create and activate a virtual environment

2. Install dependencies:

    pip install -r requirements.txt

3. Create a `.env` file:

    OPENAI_API_KEY=your_api_key_here

   Do not commit `.env`; it is ignored by git.

4. Run the app:

    streamlit run app.py

## OpenAI API Key Setup

The app never hardcodes or displays the OpenAI API key. It checks for the key in this order:

1. Streamlit secrets: `st.secrets["OPENAI_API_KEY"]`
2. Local environment variable: `OPENAI_API_KEY`

For local development, create a `.env` file in the project root:

    OPENAI_API_KEY=your_api_key_here

For Streamlit Cloud, add this in the app's **Secrets** settings:

    OPENAI_API_KEY = "your_api_key_here"

If no key is configured, the app keeps working and shows a friendly message when an AI action is requested.

## AI Usage Limit

- AI features are limited to 5 uses per browser session by default
- Both `Run AI Analysis` and `What Would Make This Work?` count toward the same session limit
- Non-AI calculations, summaries, saved deals, scenarios, and comparisons are not limited
- Saved deals store only deal inputs, not API keys, secrets, or AI outputs

## Local Deal Storage

- Use the `Save / Load Deals` section in the app to save the current deal inputs locally
- Saved deals are stored as one JSON file per deal in `saved_deals/`
- Only main deal inputs are stored; AI outputs, API keys, and secrets are not saved

## Files

- `app.py` - Streamlit UI  
- `deal_storage.py` - local JSON save/load helpers  
- `deal_comparison.py` - saved-deal comparison helpers  
- `scenario_analysis.py` - scenario comparison and change-summary helpers  
- `calculator.py` - financial calculations and scoring  
- `ai_analysis.py` - OpenAI call  
- `models.py` - data models  
- `prompts.py` - AI prompts  
- `utils.py` - formatting helpers
