import streamlit as st
import pandas as pd
import plotly.express as px
import re

# store imported values between reruns
if "imported_values" not in st.session_state:
    st.session_state["imported_values"] = None

# page configuration
st.set_page_config(page_title="Profit Analysis Tool", layout="centered")

# Title
# insert company logo
st.image("pages/logo.png", width=380)
st.title("Profit Calculator")
st.write("Please enter the parameters in the sidebar for real-time calculation:")
st.markdown("---")

# Sidebar: User Input
st.sidebar.header("Input Data")

monthly_billing = st.sidebar.number_input("Contract Monthly Billing ($)", min_value=0.0, value=0.0, step=100.0,help="Enter the total monthly billing amount for the account.")

supply_cost = st.sidebar.number_input("Supply Cost ($)", min_value=0.0, value=0.0,help="Enter the estimated amount you spend on supplies and special equipment. Industry standard is 3% of monthly billing.")

other_cost = st.sidebar.number_input("Other Costs ($)", min_value=0.0, value=0.0,help="Enter any additional costs not covered elsewhere.")

upgrade_fee = st.sidebar.number_input("Upgrade Fee ($)", min_value=0.0, value=0.0,help="Enter any upgrade fees associated with the contract.")

cleaning_mode = st.sidebar.selectbox(
    "Cleaning Service Mode",
    ["Self-Cleaning", "Employees Do All Cleaning"],
    help="Check 'Self-Cleaning' if you are performing the services yourself."
)

# labor cost calculation
num_employees = st.sidebar.number_input("Number of Employees", min_value=0, value=0, step=1,help="Enter the number of employees working on this account. You should put 0 if you are a solo contractor.")

labor_cost = 0.0

employee_records = []

for i in range(int(num_employees)):
    st.sidebar.markdown(f"**Employee {i+1}**")

    hourly_wage = st.sidebar.number_input(f"  Hourly Wage for Employee {i+1} ($)", min_value=0.0, value=0.0,step=0.5)

    hours_per_night = st.sidebar.number_input(f"  Hours Worked for Employee {i+1} Per Night", min_value=0.0, value=0.0, step=0.5)
    
    nights_per_week = st.sidebar.number_input(f"  Nights Worked for Employee {i+1} Per Week", min_value=0, value=0, step=1)
    
    weeks_per_month = st.sidebar.number_input(f"  Weeks Worked for Employee {i+1} Per Month", min_value=0.00, value=4.33, step=0.01)

    labor_cost += hourly_wage * hours_per_night * nights_per_week * weeks_per_month
    
    # save the employee record for export
    employee_records.append({
        "Item": f"Employee {i+1}",
        "Hourly Wage ($)": hourly_wage,
        "Hours/Night": hours_per_night,
        "Nights/Week": nights_per_week,
        "Weeks/Month": weeks_per_month,
        "Monthly Cost ($)": hourly_wage * hours_per_night * nights_per_week * weeks_per_month
    })


# apply imported values (if any) after widgets are rendered
imported_values = st.session_state.get("imported_values")
if imported_values:
    monthly_billing = imported_values.get("monthly_billing", monthly_billing)
    supply_cost = imported_values.get("supply_cost", supply_cost)
    other_cost = imported_values.get("other_cost", other_cost)
    cleaning_mode = imported_values.get("cleaning_mode", cleaning_mode)

    imported_emps = imported_values.get("employee_records") or []
    if imported_emps:
        employee_records = imported_emps
        labor_cost = sum(emp.get("Monthly Cost ($)", 0.0) for emp in imported_emps)
    else:
        labor_cost = imported_values.get("labor_cost", labor_cost)


# --- Helpers for CSV import ---
def _parse_money(value: str) -> float:
    """Convert strings like "$1,234.56" to float; fallback to 0.0."""
    if isinstance(value, (int, float)):
        return float(value)
    if pd.isna(value):
        return 0.0
    cleaned = str(value).replace("$", "").replace(",", "").replace("%", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _parse_employee_detail(detail_str: str) -> dict:
    """Parse the exported employee detail row into a structured record."""
    wage_match = re.search(r"Wage:\s*\$?([\d.,]+)", detail_str)
    hours_match = re.search(r"Hours:\s*([\d.]+)", detail_str)
    nights_match = re.search(r"Nights:\s*([\d.]+)", detail_str)
    weeks_match = re.search(r"Weeks:\s*([\d.]+)", detail_str)
    total_match = re.search(r"Total:\s*\$?([\d.,]+)", detail_str)

    if not all([wage_match, hours_match, nights_match, weeks_match, total_match]):
        return {}

    hourly_wage = _parse_money(wage_match.group(1))
    hours_per_night = float(hours_match.group(1))
    nights_per_week = float(nights_match.group(1))
    weeks_per_month = float(weeks_match.group(1))
    monthly_cost = _parse_money(total_match.group(1))

    return {
        "Item": "Imported Employee",
        "Hourly Wage ($)": hourly_wage,
        "Hours/Night": hours_per_night,
        "Nights/Week": nights_per_week,
        "Weeks/Month": weeks_per_month,
        "Monthly Cost ($)": monthly_cost,
    }

# calculation logic

royalty_rate = 0.10  # 10% royalty

management_fee_rate = 0.05  # 5% management fee

insurance_rate = 0.055  # 5.5% insurance

commission_rate = 0  # 0% commission

labor_cost_percentage = (labor_cost / monthly_billing * 100) if monthly_billing > 0 else 0


total_cost = (
    supply_cost +
    other_cost +
    labor_cost +
    (monthly_billing * royalty_rate) +
    (monthly_billing * management_fee_rate) +
    (monthly_billing * insurance_rate) +
    (monthly_billing * commission_rate)
)

net_profit = monthly_billing - total_cost

profit_margin = (net_profit / monthly_billing) * 100 if monthly_billing > 0 else 0

col1, col2 = st.columns(2)

with col1:
    st.metric("Royalty", f"${monthly_billing * royalty_rate:,.2f}",help="Royalty fees are what you pay to the franchisor for the right to operate under their brand. This fee is 10% of your gross sales or revenue.")

    st.metric("Management Fee", f"${monthly_billing * management_fee_rate:,.2f}",help="Management fees cover the costs associated with managing and supporting the franchise network. This fee is typically 5% of your gross sales or revenue.")
    
    st.metric("Supply Cost", f"${supply_cost:,.2f}",help="Supply costs include expenses for cleaning supplies, equipment, and other materials needed to perform the cleaning services.")
    
    st.metric("Other Costs", f"${other_cost:,.2f}",help="Other costs encompass any additional expenses that do not fall under the specified categories, such as transportation, marketing, or administrative costs.")
    
    st.metric("Upgrade Fee", f"${upgrade_fee:,.2f}",help="Upgrade fees are costs associated with enhancing or upgrading the services used in the contract. ")

    st.metric("Insurance", f"${monthly_billing * insurance_rate:,.2f}",help="Insurance costs are essential for protecting your business against potential risks and liabilities. This fee is typically around 5.5% of your gross sales or revenue.")

    st.metric("Labor Cost", f"${labor_cost:,.2f}",help="Labor costs include wages paid to employees working on the account.")

    # labor cost percentage
    st.metric("Labor Cost Percentage", f"{labor_cost_percentage:.1f}%",help="This percentage indicates the proportion of your monthly billing that goes towards labor costs. If your labor cost percentage exceeds 50%, it may signal that your labor expenses are too high relative to your revenue, which could impact profitability.") 

    # labor cost alert message
    if labor_cost_percentage > 0 and monthly_billing > 0:
            # design a progress bar with color change based on labor cost percentage
        status_color = "#ff4b4b" if labor_cost_percentage > 50 else "#09ab3b"
        display_width = min(labor_cost_percentage, 100)

        st.markdown(f"""
            <style>
                .progress-container {{
                    width: 100%;
                    background-color: #f0f2f6;
                    border-radius: 10px;
                    height: 12px;
                    margin-bottom: 30px; 
                }}
                
                .progress-fill {{
                    width: {display_width}%;
                    background-color: {status_color};
                    height: 12px;
                    border-radius: 10px;
                    transition: width 0.8s ease-in-out;
                }}
            </style>
            
            <div class="progress-container">
                <div class="progress-fill"></div>
            </div>
            """, unsafe_allow_html=True)
        
        if labor_cost_percentage > 50:
            st.error(f"Alert: Labor cost is too high ({labor_cost_percentage:.1f}%)!")
        else:
            st.success("Labor cost is within healthy limits.")

    st.metric("Total Cost", f"${total_cost:,.2f}")
    
with col2:
    st.metric("Net Profit", f"${net_profit:,.2f}")
    st.metric("Profitability", f"{profit_margin:.1f}%",help="This percentage indicates how much profit you are making relative to your total billing. A higher percentage means better profitability. If you are cleaning by yourself, you should aim for at least 50% profitability to make it worthwhile. If you have employees, a profitability of 20% or higher is generally considered good. 10-20% is acceptable but leaves little room for unexpected expenses.")
    
    if monthly_billing > 0:
        if net_profit < 0:
            st.warning("⚠️ Warning: You are operating at a loss. Don't take this account.")
        elif profit_margin < 5 and cleaning_mode == "Self-Cleaning":
            st.info("ℹ️ Info: Your profitability is below the recommended threshold for solo contractors. Consider adjusting your pricing or reducing costs.")
        elif profit_margin < 10 and cleaning_mode == "Self-Cleaning":
            st.info("ℹ️ Info: This is not a good profit margin. Look for ways to improve efficiency and cut costs. Think carefully before taking this account.")
        elif profit_margin < 20 and cleaning_mode == "Self-Cleaning":
            st.info("ℹ️ Info: Your profitability is acceptable but could be improved. Go ahead and take the account.")
        elif profit_margin > 20 and cleaning_mode == "Self-Cleaning":
            st.success("✅ Success: You have a healthy profit margin! This account looks promising.")
        elif profit_margin < 5 and cleaning_mode == "Employees Do All Cleaning":
            st.info("ℹ️ Info: Your profitability is quite low. Don't take this account.If your estimations are inaccurate, you will likely struggle to make a profit.")
        elif profit_margin < 10 and cleaning_mode == "Employees Do All Cleaning":
            st.info("ℹ️ Info: This may or may not be a good profit margin. Look for ways to improve efficiency and cut costs. Think carefully before taking this account.")
        elif profit_margin > 20 and cleaning_mode == "Employees Do All Cleaning":
            st.success("✅ Success: You have a healthy profit margin! This account looks promising.")
        
st.markdown("---")


# --- 3. Visualizations ---
chart_data = {
    "Category": [
        "Net Profit", "Labor Cost", "Royalty", 
        "Management Fee", "Insurance", "Supplies", "Other"
    ],
    "Amount": [
        max(0, net_profit), # ensure non-negative for pie chart
        labor_cost,
        monthly_billing * royalty_rate,
        monthly_billing * management_fee_rate,
        monthly_billing * insurance_rate,
        supply_cost,
        other_cost
    ]
}
df_chart = pd.DataFrame(chart_data)

st.markdown("### Financial Distribution")

# create a pie chart using plotly express
fig = px.pie(
    df_chart, 
    values='Amount', 
    names='Category', 
    title="Revenue Allocation",
    color_discrete_sequence=px.colors.sequential.RdBu,
    hole=0.4 
)

# display the pie chart
st.plotly_chart(fig, use_container_width=True)

# create a bar chart using streamlit's built-in function
st.bar_chart(df_chart.set_index("Category"))

# --- 4. Export Functionality ---
summary_data = [
    {"Item": "--- SUMMARY ---", "Value": ""},
    {"Item": "Contract Monthly Billing", "Value": f"${monthly_billing:,.2f}"},
    {"Item": "Cleaning Mode", "Value": cleaning_mode},
    {"Item": "Supply Cost", "Value": f"${supply_cost:,.2f}"},
    {"Item": "Other Costs", "Value": f"${other_cost:,.2f}"},
    {"Item": "Royalty Fees", "Value": f"${royalty_rate * monthly_billing:,.2f}"},
    {"Item": "Management Fees", "Value": f"${management_fee_rate * monthly_billing:,.2f}"},
    {"Item": "Insurance Fees", "Value": f"${insurance_rate * monthly_billing:,.2f}"},
    {"Item": "Total Labor Cost", "Value": f"${labor_cost:,.2f}"},
    {"Item": "Total Expenses", "Value": f"${total_cost:,.2f}"},
    {"Item": "Net Profit", "Value": f"${net_profit:,.2f}"},
    {"Item": "Profit Margin (%)", "Value": f"{profit_margin:.2f}%"},
    {"Item": "", "Value": ""},
    {"Item": "--- EMPLOYEE BREAKDOWN ---", "Value": ""}
]

# convert summary data to DataFrame
df_summary = pd.DataFrame(summary_data)

# convert employee records to DataFrame and format
if employee_records:
    df_employees = pd.DataFrame(employee_records)
    # To merge, we convert the employee table structure to the same "Item" and "Value" format as the summary table, or directly append
    # Here we use a more readable way: expand each employee's details into multiple rows
    emp_rows = []
    for emp in employee_records:
        emp_rows.append({"Item": f"{emp['Item']} Details", "Value": f"Wage: ${emp['Hourly Wage ($)']}/hr, Hours: {emp['Hours/Night']}, Nights: {emp['Nights/Week']}, Weeks: {emp['Weeks/Month']}, Total: ${emp['Monthly Cost ($)']:,.2f}"})
    
    df_final = pd.concat([df_summary, pd.DataFrame(emp_rows)], ignore_index=True)
else:
    df_final = df_summary

# 导出为 CSV
csv_export = df_final.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Download Detailed Profit Report (CSV)",
    data=csv_export,
    file_name='detailed_profit_analysis.csv',
    mime='text/csv',
)

# --- 5. Import previously exported report (placed at bottom) ---
st.markdown("---")
st.subheader("📤 Import Previous Profit Report (CSV)")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv", key="profit_import")

if uploaded_file is not None:
    try:
        imported_df = pd.read_csv(uploaded_file)

        if not {"Item", "Value"}.issubset(imported_df.columns):
            st.error("The uploaded CSV must have 'Item' and 'Value' columns.")
        else:
            item_to_value = dict(zip(imported_df["Item"], imported_df["Value"]))

            imported_payload = {
                "monthly_billing": _parse_money(item_to_value.get("Contract Monthly Billing", monthly_billing)),
                "supply_cost": _parse_money(item_to_value.get("Supply Cost", supply_cost)),
                "other_cost": _parse_money(item_to_value.get("Other Costs", other_cost)),
                "cleaning_mode": item_to_value.get("Cleaning Mode", cleaning_mode),
            }

            parsed_employees = []
            for item_label, detail in item_to_value.items():
                if isinstance(item_label, str) and "Employee" in item_label and "Details" in item_label:
                    parsed = _parse_employee_detail(str(detail))
                    if parsed:
                        parsed["Item"] = item_label
                        parsed_employees.append(parsed)

            if parsed_employees:
                imported_payload["employee_records"] = parsed_employees
                imported_payload["labor_cost"] = sum(emp.get("Monthly Cost ($)", 0.0) for emp in parsed_employees)
            else:
                imported_payload["employee_records"] = []
                imported_payload["labor_cost"] = _parse_money(item_to_value.get("Total Labor Cost", labor_cost))

            st.session_state["imported_values"] = imported_payload
            st.success("File uploaded. Values will be applied above.")
            st.dataframe(imported_df)
            st.rerun()
    except Exception as e:
        st.error(f"Error reading the uploaded file: {e}")
