# ==========================================================
# 💳 FinCrime Signals — Transactions Dashboard
# ----------------------------------------------------------
# Interactive AML transaction visualizer for synthetic data
# Displays alerts, volumes, and geographic risk exposure
# ==========================================================

import os
import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------
# 1️⃣ Data Loading
# ----------------------------------------------------------
@st.cache_data
def load_data():
    """Load both transactions.csv and customers.csv safely."""
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    tx_path = os.path.join(base_path, "data", "transactions.csv")
    cust_path = os.path.join(base_path, "data", "customers.csv")

    if not os.path.exists(tx_path):
        st.error(f"❌ transactions.csv not found at: {tx_path}")
        st.stop()
    if not os.path.exists(cust_path):
        st.error(f"❌ customers.csv not found at: {cust_path}")
        st.stop()

    df_tx = pd.read_csv(tx_path)
    df_cust = pd.read_csv(cust_path)

    # Merge risk_score and pep_flag for analysis
    merged = df_tx.merge(
        df_cust[["customer_id", "risk_score", "pep_flag", "residency_country"]],
        on="customer_id",
        how="left",
    )
    return merged

# ----------------------------------------------------------
# 2️⃣ Page Config
# ----------------------------------------------------------
st.set_page_config(
    page_title="FinCrime Signals — Transactions Dashboard",
    layout="wide",
)
st.title("💳 FinCrime Signals — Transactions Dashboard")

df = load_data()

# ----------------------------------------------------------
# 3️⃣ Sidebar Filters
# ----------------------------------------------------------
st.sidebar.header("🔍 Filter Transactions")

# Risk level filter
risk_opts = ["All"] + sorted(df["risk_score"].dropna().unique().tolist())
risk_filter = st.sidebar.selectbox("Risk Level", risk_opts)

# Flag filter - Normalize alert_type to string and handle NaN
df["alert_type"] = df["alert_type"].fillna("").astype(str)
flag_opts = ["All"] + sorted(df["alert_type"].replace("", "Unflagged").unique().tolist())

flag_filter = st.sidebar.selectbox("Alert Type", flag_opts)

# Country filter
country_opts = ["All"] + sorted(df["origin_country"].dropna().unique().tolist())
country_filter = st.sidebar.selectbox("Origin Country", country_opts)

# Apply filters
filtered = df.copy()
if risk_filter != "All":
    filtered = filtered[filtered["risk_score"] == risk_filter]
if flag_filter != "All":
    if flag_filter == "Unflagged":
        filtered = filtered[filtered["alert_type"] == ""]
    else:
        filtered = filtered[filtered["alert_type"] == flag_filter]
if country_filter != "All":
    filtered = filtered[filtered["origin_country"] == country_filter]

# ----------------------------------------------------------
# 4️⃣ Summary Metrics
# ----------------------------------------------------------
st.subheader("📊 Summary Metrics")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Transactions", f"{len(filtered):,}")
col2.metric("Flagged", f"{filtered['is_flagged'].sum():,}")
col3.metric("Unique Customers", f"{filtered['customer_id'].nunique():,}")
col4.metric("Countries", f"{filtered['origin_country'].nunique():,}")

with st.expander("🧾 Preview Filtered Transactions"):
    st.dataframe(filtered.head(), use_container_width=True)

# ----------------------------------------------------------
# 5️⃣ Alert Type Distribution
# ----------------------------------------------------------
st.subheader("🚨 Alert Type Breakdown")

if filtered.empty:
    st.warning("No transactions match your filters.")
else:
    alert_counts = (
        filtered["alert_type"].replace("", "Unflagged").value_counts().reset_index()
    )
    alert_counts.columns = ["Alert Type", "Count"]

    fig_alert = px.bar(
        alert_counts,
        x="Alert Type",
        y="Count",
        color="Alert Type",
        text_auto=True,
        title="Alert Type Frequency",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    st.plotly_chart(fig_alert, use_container_width=True)

# ----------------------------------------------------------
# 6️⃣ Transaction Volume by Risk
# ----------------------------------------------------------
st.subheader("💰 Transaction Volume by Risk Level")
volume_stats = (
    filtered.groupby("risk_score")["amount"]
    .sum()
    .reset_index()
    .sort_values("amount", ascending=False)
)
fig_volume = px.bar(
    volume_stats,
    x="risk_score",
    y="amount",
    color="risk_score",
    text_auto=".2s",
    title="Total Transaction Value by Risk Level",
    color_discrete_map={"Low": "lightgreen", "Medium": "orange", "High": "red"},
)
st.plotly_chart(fig_volume, use_container_width=True)

# ----------------------------------------------------------
# 7️⃣ Geographic Distribution — Origin to Destination
# ----------------------------------------------------------
st.subheader("🌍 Transaction Corridors (Origin → Destination)")

country_corridors = (
    filtered.groupby(["origin_country", "destination_country"])
    .size()
    .reset_index(name="Count")
)

fig_map = px.scatter_geo(
    country_corridors,
    locations="origin_country",
    locationmode="country names",
    color="Count",
    hover_name="origin_country",
    size="Count",
    title="Transaction Volume by Origin Country",
    projection="natural earth",
)
fig_map.update_layout(
    geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
    margin=dict(l=0, r=0, t=50, b=0),
)
st.plotly_chart(fig_map, use_container_width=True)

# ----------------------------------------------------------
# 8️⃣ Table — Flagged Transactions
# ----------------------------------------------------------
st.subheader("🧾 Flagged Transaction Details")

flagged = filtered[filtered["is_flagged"] == True]
if flagged.empty:
    st.info("No flagged transactions under current filters.")
else:
    st.dataframe(
        flagged[
            [
                "timestamp",
                "customer_id",
                "origin_country",
                "destination_country",
                "amount",
                "currency",
                "alert_type",
                "risk_score",
            ]
        ].sort_values("timestamp", ascending=False),
        use_container_width=True,
        height=400,
    )

# ----------------------------------------------------------
# Footer
# ----------------------------------------------------------
st.markdown("---")
st.caption("Synthetic dataset for AML simulation — © FinCrime Signals Project")
