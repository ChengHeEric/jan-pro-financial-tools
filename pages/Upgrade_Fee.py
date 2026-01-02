import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="New Contract Upgrade Fee Estimator", layout="centered")

st.image("pages/logo.png", width=380)
st.title("New Contract Upgrade Fee Estimator")
st.write("Please enter the parameters in the sidebar for real-time calculation:")

# --- Input Section ---

st.sidebar.header("Input Data")

billing = st.sidebar.number_input("Monthly Billing", value=0.0, step=100.0, help="Enter the monthly billing amount for the contract.")

multiplier = st.sidebar.number_input("Multiplier", value=4.0, step=0.1, help="Enter the upgrade fee multiplier based on contract terms.")

credits = st.sidebar.number_input("Credits", value=0.0, step=100.0, help="Enter any credits applicable to the upgrade fee.")

dp_pct = st.sidebar.number_input("Down Payment %", value=25.00, format="%.2f", help="Enter the down payment percentage for the upgrade.")

interest_rate = st.sidebar.number_input("Interest Rate %", value=10.00, format="%.2f", help="Enter the interest rate for financing the upgrade.")

terms = st.sidebar.number_input("Payment Terms (Months)", value=0, step=1, help="Enter the number of months over which the upgrade fee will be paid.")


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
st.subheader("📊 Estimated Results Summary")

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
st.subheader("📈 Financial Visualization")

# 创建两列，分别显示饼图和对比图
viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    # 1. 升级费构成饼图
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
    st.plotly_chart(fig_pie, use_container_width=True)

with viz_col2:
    # 2. 本金与利息对比图
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
    st.plotly_chart(fig_bar, use_container_width=True)

# --- 4. Export Functionality ---
st.markdown("---")
st.subheader("3. Export Data")

# Convert dataframe to CSV
csv = df_results.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Download Estimate as CSV",
    data=csv,
    file_name='upgrade_fee_estimate.csv',
    mime='text/csv',
)