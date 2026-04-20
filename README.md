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

## Setup

1. Create and activate a virtual environment

2. Install dependencies:

    pip install -r requirements.txt

3. Create a `.env` file:

    OPENAI_API_KEY=your_api_key_here

4. Run the app:

    streamlit run app.py

## Files

- `app.py` - Streamlit UI  
- `calculator.py` - financial calculations and scoring  
- `ai_analysis.py` - OpenAI call  
- `models.py` - data models  
- `prompts.py` - AI prompts  
- `utils.py` - formatting helpers