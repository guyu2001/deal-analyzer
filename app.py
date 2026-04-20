import streamlit as st

from calculator import calculate_metrics, score_deal
from models import DealInput
from utils import format_currency, format_percent
from ai_analysis import generate_ai_analysis

st.set_page_config(page_title="AI Deal Analyzer", page_icon="🏠", layout="wide")

st.title("AI Deal Analyzer")
st.caption("Personal rental deal analysis tool")

st.header("Deal Inputs")

col1, col2, col3 = st.columns(3)

with col1:
    purchase_price = st.number_input("Purchase Price", min_value=0.0, value=350000.0, step=1000.0)
    monthly_rent = st.number_input("Monthly Rent", min_value=0.0, value=2500.0, step=50.0)
    down_payment_pct = st.number_input("Down Payment %", min_value=0.0, max_value=100.0, value=25.0, step=1.0)
    interest_rate = st.number_input("Interest Rate %", min_value=0.0, value=6.5, step=0.1)
    loan_term_years = st.number_input("Loan Term (Years)", min_value=1, value=30, step=1)

with col2:
    property_tax_annual = st.number_input("Property Tax (Annual)", min_value=0.0, value=4200.0, step=100.0)
    insurance_annual = st.number_input("Insurance (Annual)", min_value=0.0, value=1200.0, step=100.0)
    maintenance_pct = st.number_input("Maintenance %", min_value=0.0, max_value=100.0, value=8.0, step=1.0)
    vacancy_pct = st.number_input("Vacancy %", min_value=0.0, max_value=100.0, value=5.0, step=1.0)
    property_management_pct = st.number_input("Property Management %", min_value=0.0, max_value=100.0, value=8.0, step=1.0)

with col3:
    hoa_monthly = st.number_input("HOA (Monthly)", min_value=0.0, value=0.0, step=25.0)
    closing_costs = st.number_input("Closing Costs", min_value=0.0, value=7000.0, step=500.0)
    rehab_cost = st.number_input("Rehab Cost", min_value=0.0, value=5000.0, step=500.0)

deal = DealInput(
    purchase_price=purchase_price,
    monthly_rent=monthly_rent,
    down_payment_pct=down_payment_pct,
    interest_rate=interest_rate,
    loan_term_years=int(loan_term_years),
    property_tax_annual=property_tax_annual,
    insurance_annual=insurance_annual,
    maintenance_pct=maintenance_pct,
    vacancy_pct=vacancy_pct,
    property_management_pct=property_management_pct,
    hoa_monthly=hoa_monthly,
    closing_costs=closing_costs,
    rehab_cost=rehab_cost,
)

metrics = calculate_metrics(deal)
grade, verdict, strengths, concerns = score_deal(metrics)

st.header("Calculated Metrics")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Monthly Mortgage", format_currency(metrics.monthly_mortgage))
m2.metric("Monthly Cash Flow", format_currency(metrics.monthly_cash_flow))
m3.metric("Annual Cash Flow", format_currency(metrics.annual_cash_flow))
m4.metric("NOI (Annual)", format_currency(metrics.noi_annual))

m5, m6, m7, m8 = st.columns(4)
m5.metric("Cap Rate", format_percent(metrics.cap_rate))
m6.metric("Cash-on-Cash Return", format_percent(metrics.cash_on_cash_return))
m7.metric("DSCR", f"{metrics.dscr:.2f}")
m8.metric("Total Cash Invested", format_currency(metrics.total_cash_invested))

st.header("Deal Rating")

g1, g2 = st.columns([1, 3])

with g1:
    st.metric("Grade", grade)

with g2:
    st.metric("Verdict", verdict)

st.header("Initial Verdict")

st.subheader(verdict)

v1, v2 = st.columns(2)

with v1:
    st.markdown("### Strengths")
    if strengths:
        for item in strengths:
            st.write(f"- {item}")
    else:
        st.write("No major strengths identified.")

with v2:
    st.markdown("### Concerns")
    if concerns:
        for item in concerns:
            st.write(f"- {item}")
    else:
        st.write("No major concerns identified.")

st.header("AI Analysis")

if "ai_analysis" not in st.session_state:
    st.session_state.ai_analysis = ""

if st.button("Run AI Analysis"):
    with st.spinner("Analyzing deal..."):
        st.session_state.ai_analysis = generate_ai_analysis(
            deal, metrics, verdict, strengths, concerns
        )

if st.session_state.ai_analysis:
    st.write(st.session_state.ai_analysis)
else:
    st.caption("Click the button to generate AI analysis.")