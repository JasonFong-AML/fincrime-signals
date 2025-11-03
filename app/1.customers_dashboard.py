import os
import streamlit as st
import pandas as pd
import plotly.express as px

# --- Load data safely ---
@st.cache_data
def load_data():
    base_path = os.path.dirname(os.path.dirname(__file__))
    data_path = os.path.join(base_path, "data", "customers.csv")

    if not os.path.exists(data_path):
        st.error(f"❌ customers.csv not found at: {data_path}")
        st.stop()

    df = pd.read_csv(data_path)
    return df

# --- Streamlit App Body ---
st.set_page_config(page_title="FinCrime Signals — Customers Dashboard", layout="wide")
st.title("🧠 FinCrime Signals — Customer Overview")

# Load the CSV
df = load_data()

# --- Basic Sanity Check ---
st.write(f"✅ Loaded {len(df):,} customer records.")
st.write("Here are the first few rows of the dataset:")
st.dataframe(df.head())

# --- Basic visualizations ---
st.subheader("📊 Risk Level Distribution")
risk_counts = df["risk_score"].value_counts().reset_index()
risk_counts.columns = ["Risk Level", "Count"]
fig_risk = px.pie(
    risk_counts,
    values="Count",
    names="Risk Level",
    color="Risk Level",
    color_discrete_map={"Low": "lightgreen", "Medium": "orange", "High": "red"},
    hole=0.4,
)
st.plotly_chart(fig_risk, use_container_width=True)

st.subheader("✅ Onboarding Decision Breakdown")
decision_counts = df["onboarding_decision"].value_counts().reset_index()
decision_counts.columns = ["Decision", "Count"]
fig_decision = px.bar(
    decision_counts,
    x="Decision",
    y="Count",
    color="Decision",
    text_auto=True,
)
st.plotly_chart(fig_decision, use_container_width=True)

st.markdown("---")
st.caption("Synthetic dataset generated for AML/KYC simulation — © FinCrime Signals Project")
