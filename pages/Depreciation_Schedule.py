import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime as time
import io

st.set_page_config(page_title="Multi-Asset Depreciation Tool", layout="wide")

st.image("pages/logo.png", width=380)
st.title("Multi-Asset Depreciation Schedule")
st.markdown("---")

# 1. define asset types
asset_types = ["Equipment", "Car", "Computers", "Agreement", "Upgrades", "Accounts", "Goodwill"]

# category mapping
TANGIBLE_TYPES = ["Equipment", "Car", "Computers"]

def get_category(asset_type):
    return "Tangible" if asset_type in TANGIBLE_TYPES else "Intangible"

# 2. interactive asset input area
st.subheader("Asset Input")
st.info("You can add, modify, or delete rows directly in the table below.")

# initialize a sample table
if "df_assets" not in st.session_state:
    st.session_state.df_assets = pd.DataFrame([{
        "Asset Name": "Example Asset",
        "Type": "Equipment",
        "Cost": 10000.0,
        "Purchase Year": 2024,
        "Useful Life (Years)": 5
    }])

# use data_editor to allow user editing
edited_df = st.data_editor(
    st.session_state.df_assets,
    num_rows="dynamic", # allow user to add rows
    column_config={
        "Type": st.column_config.SelectboxColumn("Asset Type", options=asset_types, required=True),
        "Cost": st.column_config.NumberColumn("Cost ($)", min_value=0, format="$%d"),
        "Purchase Year": st.column_config.NumberColumn("Purchase Year", min_value=1900, max_value=2100, step=1),
        "Useful Life (Years)": st.column_config.NumberColumn("Life (Y)", min_value=1),
    },
    use_container_width=True,
    hide_index=True
)

# 3. calculation logic: expand depreciation by actual years based on Purchase Year
def generate_calendar_schedule(df):
    if df.empty:
        return pd.DataFrame()
    
    # calculate the end year for each asset
    df['End Year'] = df['Purchase Year'] + df['Useful Life (Years)'] - 1
    
    # determine the start and end years for the report
    start_year = int(df['Purchase Year'].min())
    end_year = int(df['End Year'].max())
    
    all_years = []
    
    for cal_year in range(start_year, end_year + 1):
        year_data = {"Year": cal_year}
        year_total_dep = 0
        
        for _, asset in df.iterrows():
            annual = asset["Cost"] / asset["Useful Life (Years)"]
            
            # determine if the current calendar year is within the asset's depreciation period
            if asset['Purchase Year'] <= cal_year <= asset['End Year']:
                year_total_dep += annual
                year_data[asset["Asset Name"]] = annual
            else:
                year_data[asset["Asset Name"]] = 0
                
        year_data["Total Annual Depreciation"] = year_total_dep
        all_years.append(year_data)
        
    return pd.DataFrame(all_years)

# call the new function
full_schedule = generate_calendar_schedule(edited_df)

# 4. display results
if not full_schedule.empty:
    st.markdown("---")
    st.subheader("Cumulative and Annual Depreciation Summary")
    
    # calculate cumulative depreciation
    full_schedule["Cumulative Depreciation"] = full_schedule["Total Annual Depreciation"].cumsum()
    
    # formatted display
    st.dataframe(
        full_schedule.style.format({
            "Year": "{:.0f}",  # force display as integer year without commas
            "Total Annual Depreciation": "${:,.2f}",
            "Cumulative Depreciation": "${:,.2f}"
        },precision=2),
        use_container_width=True,
        hide_index=True
    )

    # 5. By Asset Type Summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("By Asset Type")
        # calculate total depreciation by asset type
        fig = px.pie(
            edited_df.groupby("Type", as_index=False).sum(),
            names="Type",   
            values="Cost",  
            hole=0.4        
        )

        # force display percentage
        fig.update_traces(textinfo='percent+label')

        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        
        # --- Added: Pie chart by asset category ---
        st.subheader("By Asset Category (Tangible vs Intangible)")

        # Create a temporary DataFrame for category summary
        category_df = edited_df.copy()
        category_df["Category"] = category_df["Type"].apply(get_category)

        # Summarize Cost by Category
        cat_summary = category_df.groupby("Category", as_index=False)["Cost"].sum()

        # Use Plotly to draw the second pie chart
        fig_cat = px.pie(
            cat_summary,
            names="Category",
            values="Cost",
            hole=0.4,
            color="Category",
            # Custom colors: Tangible assets in blue, Intangible assets in orange
            color_discrete_map={"Tangible": "#1f77b4", "Intangible": "#ff7f0e"}
        )

        fig_cat.update_traces(textinfo='percent+label')

        st.plotly_chart(fig_cat, use_container_width=True)

# --- Added: Visualization of Depreciation Distribution by Year ---
    st.subheader("Depreciation Distribution by Year")

    if not full_schedule.empty:
        # Prepare data for plotting: we need columns for each asset but exclude cumulative and total columns
        # Assume your full_schedule columns include: Year, Total Annual Depreciation, and individual asset names
        
        # Filter columns for plotting (exclude total and cumulative columns, keep Year and individual assets)
        chart_cols = [col for col in full_schedule.columns if col not in ["Total Annual Depreciation", "Cumulative Depreciation"]]
        chart_data = full_schedule[chart_cols]

        # Use Streamlit built-in bar chart
        # x="Year" will set the year as the x-axis, other columns will be stacked automatically
        st.bar_chart(
            chart_data, 
            x="Year", 
            use_container_width=True
        )
        
        st.caption("Bar chart showing annual depreciation distribution across different assets over the years.")

    # 6. export functionality

    # --- Enhanced export functionality ---
    st.markdown("---")
    st.subheader("📥 Export Financial Report")

    # 1. Prepare summary data (consistent with web display)
    category_df = edited_df.copy()
    category_df["Category"] = category_df["Type"].apply(get_category)
    cat_summary = category_df.groupby("Category")["Cost"].sum().reset_index()
    type_summary = edited_df.groupby("Type")["Cost"].sum().reset_index()

    # 2. Create Excel buffer
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write input assets
        edited_df.to_excel(writer, sheet_name='Input Assets', index=False)
        
        # Write annual depreciation schedule
        full_schedule.to_excel(writer, sheet_name='Depreciation Schedule', index=False)
        
        # Write summary reports
        type_summary.to_excel(writer, sheet_name='Summary By Type', index=False)
        cat_summary.to_excel(writer, sheet_name='Summary By Category', index=False)

        # Get xlsxwriter objects for formatting (optional)
        workbook  = writer.book
        worksheet = writer.sheets['Depreciation Schedule']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
        
        # You can add more Excel styles here...



    # 3. Provide download button
    st.download_button(
        label="🚀 Download All Information (Excel)",
        data=buffer.getvalue(),
        file_name=f"Asset_Report_{time.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.ms-excel",
        help="This will export the input list, the full schedule, and all summaries into a single Excel file."
    )