import streamlit as st
import pandas as pd
import plotly.express as px

# session defaults for inputs to allow import overrides
def handle_upload():
    if st.session_state.upgrade_fee_import is not None:
        try:
            # read file
            imported_df = pd.read_csv(st.session_state.upgrade_fee_import)
            if {"Description", "Value"}.issubset(imported_df.columns):
                item_to_value = dict(zip(imported_df["Description"], imported_df["Value"]))
                
                # Update Session State
                # Because this happens in a callback, Streamlit allows this modification
                st.session_state["billing"] = _parse_number(item_to_value.get("Contract Monthly Billing", 0.0))
                st.session_state["multiplier"] = _parse_number(item_to_value.get("Multiplier", 4.0))
                st.session_state["credits"] = _parse_number(item_to_value.get("Credits", 0.0))
                st.session_state["interest_rate"] = _parse_number(item_to_value.get("Interest Rate %", 10.0))
                st.session_state["terms"] = int(_parse_number(item_to_value.get("Payment Terms (Months)", 0)))
                
                st.toast("Successfully loaded previous data!")
        except Exception as e:
            st.error(f"failed to read fil: {e}")

default_state = {
    "billing": 0.0,
    "multiplier": 4.0,
    "credits": 0.0,
    "dp_pct": 25.0,
    "interest_rate": 10.0,
    "terms": 0,
}
for _k, _v in default_state.items():
    st.session_state.setdefault(_k, _v)


def _parse_number(value) -> float:
    """Best-effort float parser that strips $ , % symbols."""
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value)
    cleaned = text.replace("$", "").replace(",", "").replace("%", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

st.set_page_config(page_title="New Contract Upgrade Fee Estimator", layout="centered")

st.image("pages/logo.png", width=380)
st.title("New Contract Upgrade Fee Estimator")
st.write("Please enter the parameters in the sidebar for real-time calculation:")

# --- Input Section ---

st.sidebar.header("Input Data")

billing = st.sidebar.number_input(
    "Monthly Billing",
    step=100.0,
    key="billing",
    help="Enter the monthly billing amount for the contract.",
)

multiplier = st.sidebar.number_input(
    "Multiplier",
    step=0.1,
    key="multiplier",
    help="Enter the upgrade fee multiplier based on contract terms.",
)

credits = st.sidebar.number_input(
    "Credits",
    step=100.0,
    key="credits",
    help="Enter any credits applicable to the upgrade fee.",
)

dp_pct = st.sidebar.number_input(
    "Down Payment %",
    format="%.2f",
    key="dp_pct",
    help="Enter the down payment percentage for the upgrade.",
)

interest_rate = st.sidebar.number_input(
    "Interest Rate %",
    format="%.2f",
    key="interest_rate",
    help="Enter the interest rate for financing the upgrade.",
)

terms = st.sidebar.number_input(
    "Payment Terms (Months)",
    step=1,
    key="terms",
    help="Enter the number of months over which the upgrade fee will be paid.",
)


# --- Calculation Logic ---
upgrade_total = billing * multiplier
net_after_credits = upgrade_total - credits
dp_amount = net_after_credits * dp_pct / 100
amt_financed_base = net_after_credits - dp_amount
interest_amt = amt_financed_base * interest_rate / 100
total_financed = amt_financed_base + interest_amt
monthly_payment = total_financed / terms if terms > 0 else 0

# --- Results Display ---
st.divider()
st.subheader("Estimated Results Summary")

res1, res2, res3 = st.columns(3)
res1.metric("Total Upgrade Amount", f"${upgrade_total:,.2f}")
res2.metric("Down Payment Amount", f"${dp_amount:,.2f}")
res3.metric("Credits", f"${credits:,.2f}")

res4, res5 = st.columns(2)
res4.metric("Total Financed Amount (Including Interest)", f"${total_financed:,.2f}")
res5.metric("Estimated Monthly Payment (Upgrade Fee)", f"${monthly_payment:,.2f}", delta_color="inverse")
# --- Detailed Comparison Table (Optional) ---
with st.expander("View Calculation Details"):
    st.write(f"- **Base Upgrade Fee:** ${upgrade_total:,.2f}")
    st.write(f"- **Net After Credits:** ${net_after_credits:,.2f}")
    st.write(f"- **Principal Amount Financed:** ${amt_financed_base:,.2f}")
    st.write(f"- **Interest Amount:** ${interest_amt:,.2f}")
    
# Detailed Breakdown Table
data = {
    "Description": [
        "Contract Monthly Billing",
        "Multiplier",
        "Upgrade Subtotal",
        "Credits",
        "Net Amount (After Credits)",
        "Down Payment Amount",
        "Amount Financed (Principal)",
        "Interest Amount",
        "Total Financed Amount",
        "Payment Terms (Months)",
        "Estimated Monthly Upgrade Fee"
    ],
    "Value": [
        billing,
        multiplier,
        upgrade_total,
        credits,
        net_after_credits,
        dp_amount,
        amt_financed_base,
        interest_amt,
        total_financed,
        terms,
        monthly_payment
    ]
}

df_results = pd.DataFrame(data)


st.divider()
st.subheader("Financial Visualization")

# create two visualizations side by side
viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    # 1. upgrade fee composition pie chart
    pie_data = pd.DataFrame({
        "Category": ["Down Payment", "Principal Financed", "Credits"],
        "Amount": [dp_amount, amt_financed_base, credits]
    })
    
    fig_pie = px.pie(
        pie_data, 
        values='Amount', 
        names='Category', 
        title="Upgrade Fee Composition",
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Teal
    )
    st.plotly_chart(fig_pie)

with viz_col2:
    # 2. interest vs principal bar chart
    bar_data = pd.DataFrame({
        "Type": ["Principal", "Interest"],
        "Amount": [amt_financed_base, interest_amt]
    })
    
    fig_bar = px.bar(
        bar_data, 
        x='Type', 
        y='Amount', 
        title="Financing Breakdown",
        text_auto='.2s',
        color='Type',
        color_discrete_map={"Principal": "#2E86C1", "Interest": "#E74C3C"}
    )
    st.plotly_chart(fig_bar)

# --- 4. Export Functionality ---
st.markdown("---")
st.subheader("3. Export Data")

# Convert dataframe to CSV
csv = df_results.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download Estimate as CSV",
    data=csv,
    file_name='upgrade_fee_estimate.csv',
    mime='text/csv',
)

# --- 5. Import previously exported estimate (CSV) ---
st.markdown("---")
st.subheader("4. Import Previous Estimate (CSV)")

# set key for uploader to avoid conflicts
st.file_uploader(
    "Choose CSV file", 
    type="csv", 
    key="upgrade_fee_import", 
    on_change=handle_upload  
)
