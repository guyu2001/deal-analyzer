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
- Generate optional AI analysis
- Save and load deal inputs locally from `saved_deals/`

## Setup

1. Create and activate a virtual environment

2. Install dependencies:

    pip install -r requirements.txt

3. Create a `.env` file:

    OPENAI_API_KEY=your_api_key_here

4. Run the app:

    streamlit run app.py

## Local Deal Storage

- Use the `Save / Load Deals` section in the app to save the current deal inputs locally
- Saved deals are stored as one JSON file per deal in `saved_deals/`
- Only main deal inputs are stored; AI outputs, API keys, and secrets are not saved

## Files

- `app.py` - Streamlit UI  
- `deal_storage.py` - local JSON save/load helpers  
- `calculator.py` - financial calculations and scoring  
- `ai_analysis.py` - OpenAI call  
- `models.py` - data models  
- `prompts.py` - AI prompts  
- `utils.py` - formatting helpers
