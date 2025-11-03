# ==========================================================
# 💳 FinCrime Signals — transactions_gen.py
# ----------------------------------------------------------
# Generates a synthetic transactions.csv aligned with customers.csv
# - ~10,000 transactions
# - Risk-weighted sampling (High > Medium > Low)
# - Cross-border logic and AML flagging rules
# - Reproducible with a fixed seed
# ==========================================================

import os
import math
import uuid
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
Faker.seed(SEED)
fake = Faker()

# -------------------------------
# Paths (robust to working dir)
# -------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CUSTOMERS_PATH = os.path.join(BASE_DIR, "data", "customers.csv")
OUT_PATH = os.path.join(BASE_DIR, "data", "transactions.csv")

# -------------------------------
# Load onboarded customers only
# -------------------------------
def load_customers(path=CUSTOMERS_PATH) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"customers.csv not found at: {path}")
    df = pd.read_csv(path)
    # Keep only onboarded population (Approved / Manual Review)
    df = df[df["onboarding_decision"].isin(["Approved", "Manual Review"])].copy()
    if df.empty:
        raise ValueError("No onboarded customers found after filtering.")
    # Light normalization
    if "residency_country" not in df.columns:
        raise ValueError("Expected column 'residency_country' missing from customers.csv")
    return df

# -------------------------------------------
# Config: currencies, channels, tx types, etc
# -------------------------------------------
CURRENCIES = ["EUR", "USD", "GBP"]
CHANNELS = ["Online", "Mobile", "ATM", "Branch", "API", "POS"]
TX_TYPES = ["Transfer", "Payment", "Deposit", "Withdrawal", "Bill Payment"]

# Offshore-ish / financial centers for PEP/offshore rule
OFFSHORE_SET = {
    "Cayman Islands", "British Virgin Islands", "Bermuda", "Seychelles",
    "Mauritius", "Panama", "Cyprus", "Malta", "Gibraltar", "Isle of Man",
    "Guernsey", "Jersey", "Aruba", "Curaçao", "Sint Maarten"
}

# High-risk jurisdictions from your classification (subset used for corridor rule)
HIGH_RISK_COUNTRIES = {
    "Algeria", "Cameroon", "Côte d’Ivoire", "Kenya", "Madagascar", "Mozambique",
    "Nigeria", "Tanzania", "Cambodia", "China", "Kuwait", "Laos", "Nepal",
    "Tajikistan", "Vietnam", "Solomon Islands"
}

# -------------------------------------------
# Helper: sample destination country
# -------------------------------------------
def choose_destination(origin: str, all_countries: list, risk_level: str) -> (str, bool):
    """
    Choose destination country with cross-border probability skewed by risk.
    Returns (destination_country, is_cross_border).
    """
    # Base cross-border probability by risk (more cross-border for higher risk)
    p_cross = {"Low": 0.25, "Medium": 0.45, "High": 0.65}.get(risk_level, 0.35)
    if random.random() > p_cross:
        return origin, False

    # Bias some proportion towards high-risk corridors
    bias_high = {"Low": 0.10, "Medium": 0.20, "High": 0.35}.get(risk_level, 0.15)

    if random.random() < bias_high:
        # Prefer a high-risk destination if available
        candidates = [c for c in all_countries if c in HIGH_RISK_COUNTRIES and c != origin]
        if candidates:
            return random.choice(candidates), True

    # Otherwise pick any other destination (not origin)
    others = [c for c in all_countries if c != origin]
    return random.choice(others), True if others else (origin, False)

# -------------------------------------------
# Amount generation (log-normal by account type)
# -------------------------------------------
def sample_amount(account_type: str) -> float:
    """
    Business accounts tend to have larger/heavier-tailed amounts.
    Return positive float rounded to cents.
    """
    if account_type == "Business":
        # Mean ~ 2,000–8,000 with long tail
        amt = np.random.lognormal(mean=8.0, sigma=0.8) / 100  # scale down
    else:
        # Mean ~ 100–1,500 with occasional spikes
        amt = np.random.lognormal(mean=7.2, sigma=0.7) / 100
    # Clamp to a reasonable cap for demo (e.g., 250k)
    amt = min(amt, 250_000)
    return round(amt, 2)

# -------------------------------------------
# Device id simulator (within customer's device_count)
# -------------------------------------------
def sample_device_id(customer_row: pd.Series) -> str:
    # Deterministic subset of device ids per customer
    n = int(customer_row.get("device_count", 1))
    n = max(1, min(n, 5))
    # Make a stable pool per customer
    rng = random.Random(hash(customer_row["customer_id"]) % (2**32 - 1))
    pool = [f"{customer_row['customer_id'][:8]}-dev-{i+1}" for i in range(n)]
    return rng.choice(pool)

# -------------------------------------------
# Generate timestamps over a window
# -------------------------------------------
def sample_timestamp(start: datetime, months: int = 9) -> datetime:
    """
    Sample a timestamp over the last `months` months with slight bias to recent.
    """
    end = datetime.now()
    start = end - timedelta(days=30*months)
    # Bias to recent by squaring a uniform
    u = random.random() ** 2
    delta_seconds = (end - start).total_seconds()
    ts = start + timedelta(seconds=u * delta_seconds)
    # Add random intra-day time
    ts += timedelta(seconds=random.randint(0, 86399))
    return ts

# -------------------------------------------
# Core generator
# -------------------------------------------
def generate_transactions(n_rows: int = 10_000) -> pd.DataFrame:
    customers = load_customers()

    # Risk-weighted sampling: High > Medium > Low
    risk_weights = customers["risk_score"].map({"Low": 1.0, "Medium": 1.75, "High": 2.5}).fillna(1.0)
    prob = risk_weights / risk_weights.sum()
    # Pre-pick customers for each transaction (allows same customer many times)
    picked_idx = np.random.choice(customers.index, size=n_rows, replace=True, p=prob.values)
    picked = customers.loc[picked_idx].reset_index(drop=True)

    # All possible destination countries (from onboarded residencies)
    country_universe = sorted(customers["residency_country"].dropna().unique().tolist())

    rows = []
    for i, cust in picked.iterrows():
        origin_country = cust["residency_country"]
        risk_level = cust["risk_score"]
        account_type = cust.get("account_type", "Personal")

        # Pick destination + cross-border
        destination_country, is_cross_border = choose_destination(origin_country, country_universe, risk_level)

        # Currency choice: simple bias by region (fallback uniform)
        if origin_country in {"United States", "Puerto Rico", "Guam", "American Samoa", "Northern Mariana Islands"}:
            currency = "USD"
        elif origin_country in {"United Kingdom", "Gibraltar", "Guernsey", "Jersey", "Isle of Man"}:
            currency = "GBP"
        else:
            currency = random.choices(CURRENCIES, weights=[0.55, 0.35, 0.10])[0]

        amount = sample_amount(account_type)
        channel = random.choices(CHANNELS, weights=[0.45, 0.30, 0.05, 0.05, 0.10, 0.05])[0]
        tx_type = random.choices(TX_TYPES, weights=[0.55, 0.20, 0.15, 0.05, 0.05])[0]
        is_cash = tx_type in {"Deposit", "Withdrawal"} and random.random() < (0.20 if account_type == "Personal" else 0.08)
        device_id = sample_device_id(cust)
        ts = sample_timestamp(datetime.now(), months=9)

        rows.append({
            "transaction_id": f"TX{str(uuid.uuid4())[:12].upper()}",
            "customer_id": cust["customer_id"],
            "timestamp": ts.isoformat(timespec="seconds"),
            "amount": amount,
            "currency": currency,
            "origin_country": origin_country,
            "destination_country": destination_country,
            "channel": channel,
            "transaction_type": tx_type,
            "counterparty_type": random.choices(["Individual", "Business", "Exchange"], weights=[0.6, 0.3, 0.1])[0],
            "is_cross_border": bool(is_cross_border),
            "is_cash": bool(is_cash),
            "device_id": device_id,
            # placeholders for rules (computed next)
            "is_flagged": False,
            "alert_type": ""
        })

    tx = pd.DataFrame(rows)

    # -------------------------------------------
    # Flagging logic (post-processing)
    # -------------------------------------------

    # Helper: same-day key
    tx["ts_dt"] = pd.to_datetime(tx["timestamp"])
    tx["day"] = tx["ts_dt"].dt.date

    # 1) STRUCTURING: many sub-threshold credits in 24h (simulate 10k reporting threshold)
    #    We'll flag customers with >= 4 deposits/transfers in [9000, 10000) (USD/EUR/GBP) in same day
    near_threshold = (
        (tx["amount"].between(9000, 9999.99))
        & (tx["transaction_type"].isin(["Deposit", "Transfer"]))
        & (tx["currency"].isin(["USD", "EUR", "GBP"]))
    )
    grp = tx[near_threshold].groupby(["customer_id", "day"]).size().reset_index(name="cnt")
    structuring_keys = set(grp[grp["cnt"] >= 4].apply(lambda r: (r["customer_id"], r["day"]), axis=1).tolist())
    tx["rule_structuring"] = tx.apply(lambda r: near_threshold.loc[r.name] and ((r["customer_id"], r["day"]) in structuring_keys), axis=1)

    # 2) VELOCITY: >= 15 tx for same customer within any rolling 24h
    #    Approx: per day counts >= 15
    day_counts = tx.groupby(["customer_id", "day"]).size().reset_index(name="dcount")
    velocity_keys = set(day_counts[day_counts["dcount"] >= 15].apply(lambda r: (r["customer_id"], r["day"]), axis=1).tolist())
    tx["rule_velocity"] = tx.apply(lambda r: (r["customer_id"], r["day"]) in velocity_keys, axis=1)

    # 3) HIGH-RISK CORRIDOR: cross-border AND destination in HIGH_RISK_COUNTRIES
    tx["rule_corridor"] = tx["is_cross_border"] & tx["destination_country"].isin(HIGH_RISK_COUNTRIES)

    # 4) LAYERING: >= 3 distinct destination countries within 48h window
    #    Approximation: per customer per 2-day bucket distinct dest >= 3
    tx["two_day_bucket"] = (tx["ts_dt"].dt.floor("48H")).astype(str)
    dest_counts = (
        tx[tx["is_cross_border"]]
        .groupby(["customer_id", "two_day_bucket"])["destination_country"]
        .nunique()
        .reset_index(name="ndest")
    )
    layering_keys = set(dest_counts[dest_counts["ndest"] >= 3].apply(lambda r: (r["customer_id"], r["two_day_bucket"]), axis=1).tolist())
    tx["rule_layering"] = tx.apply(lambda r: r["is_cross_border"] and ((r["customer_id"], r["two_day_bucket"]) in layering_keys), axis=1)

    # 5) PEP / OFFSHORE: customer is PEP and cross-border to offshore/financial center
    #    Merge minimal customer data to tx for PEP flag
    customers = load_customers()  # reload (cheap) to get pep_flag
    pep_map = customers.set_index("customer_id")["pep_flag"]
    tx["pep_flag"] = tx["customer_id"].map(pep_map).fillna(False)
    tx["rule_pep_offshore"] = tx["pep_flag"] & tx["is_cross_border"] & tx["destination_country"].isin(OFFSHORE_SET)

    # Combine rules into single flags, prioritize type
    def choose_alert(row) -> str:
        if row["rule_corridor"]:
            return "High-Risk Corridor"
        if row["rule_structuring"]:
            return "Structuring"
        if row["rule_velocity"]:
            return "Velocity"
        if row["rule_layering"]:
            return "Layering"
        if row["rule_pep_offshore"]:
            return "PEP-Offshore"
        return ""

    tx["alert_type"] = tx.apply(choose_alert, axis=1)
    tx["is_flagged"] = tx["alert_type"] != ""

    # Housekeeping: drop helper cols
    tx = tx.drop(columns=["ts_dt", "day", "two_day_bucket", "rule_structuring", "rule_velocity", "rule_corridor", "rule_layering", "rule_pep_offshore", "pep_flag"])

    # Sort by time for readability
    tx = tx.sort_values("timestamp").reset_index(drop=True)

    return tx

# -------------------------------------------
# Main
# -------------------------------------------
if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df_tx = generate_transactions(n_rows=10_000)
    df_tx.to_csv(OUT_PATH, index=False)

    # Console summary (quick sanity check)
    print(f"✅ Generated {len(df_tx):,} transactions -> {OUT_PATH}")
    print("Flag breakdown:")
    print(df_tx["alert_type"].value_counts(dropna=False).to_string())
    print("\nSample:")
    print(df_tx.head(5).to_string(index=False))
