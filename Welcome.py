import streamlit as st

# set page configuration
st.set_page_config(page_title="Jan-Pro Tools for CBOs")

st.image("pages/logo.png", width=380)
st.title("Welcome to the Jan-Pro Tool Box for CBOs")
st.markdown("Please select a tool from the left sidebar")


st.divider() 

# Use column layout to display tool introductions
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Depreciation Calculation")
    st.write("Calculate asset depreciation schedules over different years.")
    # Prompt user to go to sidebar
    st.info("Go to the sidebar and select **Depreciation Schedule**")

with col2:
    st.subheader("Profit and Loss Calculation")
    st.write("Quickly assess your business income and expenses.")
    st.info("Go to the sidebar and select **Profit Analysis**")

with col3:
    st.subheader("Upgrade Fee Estimation")
    st.write("Estimate the costs required for contract upgrades.")
    st.info("Go to the sidebar and select **Upgrade Fee**")

st.divider()

# Additional tips
st.sidebar.success("Select a tool from above to get started")