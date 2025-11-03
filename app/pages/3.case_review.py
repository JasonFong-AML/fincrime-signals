# ==========================================================
# 🧩 FinCrime Signals — Investigator Case Review (Dropdown View)
# ==========================================================
import os
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.express as px

# ----------------------------------------------------------
# Load data
# ----------------------------------------------------------
@st.cache_data
def load_data():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    tx_path = os.path.join(base_path, "data", "transactions.csv")
    cust_path = os.path.join(base_path, "data", "customers.csv")

    if not os.path.exists(tx_path) or not os.path.exists(cust_path):
        st.error("❌ Missing CSV files in /data/. Generate them first.")
        st.stop()

    df_tx = pd.read_csv(tx_path)
    df_cust = pd.read_csv(cust_path)
    return df_tx, df_cust, base_path


df_tx, df_cust, BASE_PATH = load_data()
flagged = df_tx[df_tx["is_flagged"] == True].copy()

st.set_page_config(page_title="FinCrime Signals — Case Review", layout="wide")
st.title("🕵️ Investigator Case Review Form")

# ----------------------------------------------------------
# Sidebar Case Selector
# ----------------------------------------------------------
st.sidebar.header("🎯 Case Selection Filters")

# Join transactions with customer info
merged = flagged.merge(
    df_cust[["customer_id", "risk_score", "jurisdiction_risk", "name"]],
    on="customer_id", how="left"
)

# --- 1️⃣ Filter: Alert Type
alert_types = ["All"] + sorted(merged["alert_type"].dropna().unique().tolist())
selected_alert = st.sidebar.selectbox("Alert Type", alert_types)

# --- 2️⃣ Filter: Customer Risk Level
risk_levels = ["All"] + sorted(merged["risk_score"].dropna().unique().tolist())
selected_risk = st.sidebar.selectbox("Customer Risk Level", risk_levels)

# --- 3️⃣ Filter: Jurisdiction Risk
jur_risks = ["All"] + sorted(merged["jurisdiction_risk"].dropna().unique().tolist())
selected_jur = st.sidebar.selectbox("Jurisdiction Risk", jur_risks)

# --- Apply Filters
filtered = merged.copy()
if selected_alert != "All":
    filtered = filtered[filtered["alert_type"] == selected_alert]
if selected_risk != "All":
    filtered = filtered[filtered["risk_score"] == selected_risk]
if selected_jur != "All":
    filtered = filtered[filtered["jurisdiction_risk"] == selected_jur]

if filtered.empty:
    st.sidebar.warning("⚠️ No cases match the selected filters.")
    st.stop()

# --- 🧮 Compute Summary Stats
case_count = filtered["customer_id"].nunique()
avg_amount = filtered["amount"].mean()

# Convert risk levels to numeric (Low=1, Medium=2, High=3) for averaging
risk_map = {"Low": 1, "Medium": 2, "High": 3}
inv_map = {1: "Low", 2: "Medium", 3: "High"}
filtered["risk_score_num"] = filtered["risk_score"].map(risk_map)
avg_risk_val = filtered["risk_score_num"].mean()
avg_risk_label = inv_map[round(avg_risk_val)] if not pd.isna(avg_risk_val) else "N/A"

# --- 💡 Summary Widget (compact version)
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
### 📊 Case Summary
**Matching Cases:** {case_count}  
**Average Risk:** {avg_risk_label}  
**Average Amount:** €{avg_amount:,.2f}
""")
st.sidebar.markdown("---")

# --- Build Dropdown Case List
filtered["display_name"] = (
    filtered["name"].fillna("Unknown") +
    " (" + filtered["alert_type"] +
    f", Risk: " + filtered["risk_score"] +
    f", Jurisdiction: " + filtered["jurisdiction_risk"] + ")"
)

# Deduplicate customer-alert pairs
case_list = (
    filtered.groupby(["customer_id", "alert_type", "display_name"])
    .size().reset_index(name="tx_count")
)
case_list["display"] = (
    case_list["display_name"] + " — " + case_list["tx_count"].astype(str) + " tx"
)

selected_display = st.sidebar.selectbox("Select Case", case_list["display"].tolist())
selected_case = case_list[case_list["display"] == selected_display].iloc[0]
cust_id = selected_case["customer_id"]
alert_type = selected_case["alert_type"]

# ----------------------------------------------------------
# Case & Customer Context
# ----------------------------------------------------------
cust = df_cust[df_cust["customer_id"] == cust_id].squeeze()
cust_tx = df_tx[df_tx["customer_id"] == cust_id].copy()
cust_tx["timestamp"] = pd.to_datetime(cust_tx["timestamp"], errors="coerce")

st.divider()
st.header(f"📁 Case Metadata — {cust_id}")
case_id = f"CASE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
col1, col2, col3 = st.columns(3)
col1.metric("Case ID", case_id)
col2.metric("Alert Type", alert_type)
col3.metric("Status", "🟠 Open")

st.markdown(f"""
**Date Opened:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Assigned Investigator:** Analyst (You)  
**Customer Name:** {cust['name']}  
**Customer Risk Level:** {cust['risk_score']}  
**Jurisdiction Risk:** {cust['jurisdiction_risk']}  
**PEP Flag:** {"Yes ✅" if cust['pep_flag'] else "No ❌"}
""")

# ----------------------------------------------------------
# 🧍 Customer Profile Summary
# ----------------------------------------------------------
st.subheader("🧍 Customer Context")
colA, colB, colC = st.columns(3)
colA.write(f"**Account Type:** {cust['account_type']}")
colB.write(f"**Occupation:** {cust['occupation']}")
colC.write(f"**Source of Funds:** {cust['source_of_funds']}")
colA.write(f"**Residency:** {cust['residency_country']}")
colB.write(f"**Device Count:** {cust['device_count']}")
colC.write(f"**Join Date:** {cust['join_date']}")
st.divider()

# ----------------------------------------------------------
# 💰 Transactional Behavior
# ----------------------------------------------------------
st.subheader("💰 Transactional Behavior Summary")

total_tx = len(cust_tx)
avg_amount = cust_tx["amount"].mean()
corridors = cust_tx["destination_country"].nunique()
flagged_ratio = (cust_tx["is_flagged"].mean()) * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Transactions", total_tx)
c2.metric("Avg. Amount", f"${avg_amount:,.2f}")
c3.metric("Corridors", corridors)
c4.metric("Flagged %", f"{flagged_ratio:.1f}%")

agg = cust_tx.groupby("destination_country")["amount"].sum().reset_index()
fig = px.choropleth(
    agg,
    locations="destination_country",
    locationmode="country names",
    color="amount",
    title="🌎 Aggregated Transaction Corridors",
    color_continuous_scale="Reds",
)
st.plotly_chart(fig, use_container_width=True)
st.divider()

# ----------------------------------------------------------
# ⚠️ Typology Indicators
# ----------------------------------------------------------
st.subheader("⚠️ Typology Indicators")
st.caption("Mark observed AML typologies below to guide SAR reasoning.")

cols = st.columns(2)
typology_flags = {
    "Structuring": cols[0].checkbox("Structuring — multiple small transactions under threshold"),
    "Velocity": cols[0].checkbox("Velocity — rapid movement of funds"),
    "Layering": cols[1].checkbox("Layering — multiple destinations or hops"),
    "Round-tripping": cols[1].checkbox("Round-tripping — inflow equals outflow"),
    "High-Risk Corridor": cols[0].checkbox("High-Risk Corridor — risky jurisdictions"),
    "Shell Entity": cols[1].checkbox("Shell/Front Entity — mismatch with declared business"),
    "Funnel Account": cols[0].checkbox("Funnel Account — third-party deposits"),
    "Sanctions Evasion": cols[1].checkbox("Possible sanctions evasion or circumvention"),
}
selected_typologies = [k for k,v in typology_flags.items() if v]
st.divider()

# ----------------------------------------------------------
# 🧾 Analyst Findings
# ----------------------------------------------------------
st.subheader("🧾 Analyst Findings & Decision")
summary = st.text_area("Summary of Findings", placeholder="Summarize key findings and anomalies...")
decision = st.selectbox("Final Decision", ["Pending","Cleared","Escalated","SAR Filed"])
confidence = st.slider("Confidence Level", 0,100,75)
followup = st.radio("Follow-Up Required?", ["No","Yes"])
notes = st.text_area("Reviewer Notes", placeholder="Add rationale or escalation instructions...")
st.divider()

# ----------------------------------------------------------
# 📄 Case Summary Preview
# ----------------------------------------------------------
if st.button("📄 Generate Case Summary Preview"):
    st.success(f"✅ Case Summary generated for {cust_id}")
    typologies_text = ", ".join(selected_typologies) if selected_typologies else "None selected"
    followup_text = "Yes — additional EDD or document verification required." if followup == "Yes" else "No follow-up required."
    st.markdown(f"""
    ### 🧾 Case Summary Preview
    **Case ID:** {case_id}  
    **Customer:** {cust['name']} ({cust_id})  
    **Jurisdiction Risk:** {cust['jurisdiction_risk']}  
    **Account Type:** {cust['account_type']}  
    **Alert Type:** {alert_type}  
    **Decision:** {decision}  
    **Confidence:** {confidence}%  

    ---

    ### ⚠️ Detected Typologies
    {typologies_text}

    ---

    ### 💬 Findings
    > {summary or "No findings provided."}

    **Follow-Up:** {followup_text}  
    **Reviewer Notes:** {notes or "N/A"}  

    ---

    **Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """)

st.markdown("---")
st.caption("Investigator module — FinCrime Signals Project © 2025")