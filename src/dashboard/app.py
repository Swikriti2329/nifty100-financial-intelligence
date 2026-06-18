import sys
import os
import streamlit as st
import pandas as pd

# Let this file import our existing, already-tested analytics code
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "analytics"))

from screener import get_latest_ratios, add_valuation_data
from health_score import compute_health_score

st.set_page_config(page_title="Nifty 100 Financial Intelligence", layout="wide")

@st.cache_data
def load_data():
    """Load and combine all our analytics into one table.
    Cached so it only recalculates when the underlying data changes,
    not on every single click."""
    latest = get_latest_ratios()
    latest = add_valuation_data(latest)
    scores = compute_health_score(latest)
    merged = latest.merge(
        scores[["company_id", "health_score", "health_band"]],
        on="company_id", how="left"
    )
    return merged

data = load_data()

st.title("Nifty 100 Financial Intelligence Platform")
st.caption(f"Analytics across {len(data)} Nifty 100 companies")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Companies", len(data))
col2.metric("Sectors Covered", data["broad_sector"].nunique())
col3.metric("Median ROE", f"{data['roe_pct'].median():.1f}%")
col4.metric("Excellent Health", (data["health_band"] == "Excellent").sum())

st.subheader("Median ROE by Sector")
sector_summary = data.groupby("broad_sector")["roe_pct"].median().sort_values(ascending=False)
st.bar_chart(sector_summary)

st.subheader("All Companies")
search = st.text_input("Search by company name or ticker")

display_cols = ["company_id", "company_name", "broad_sector", "roe_pct",
                 "debt_to_equity", "free_cash_flow_cr", "health_score", "health_band"]
filtered = data[display_cols].copy()

if search:
    mask = (
        filtered["company_id"].str.contains(search, case=False, na=False) |
        filtered["company_name"].str.contains(search, case=False, na=False)
    )
    filtered = filtered[mask]

st.dataframe(
    filtered.sort_values("health_score", ascending=False, na_position="last"),
    use_container_width=True,
    hide_index=True
)
