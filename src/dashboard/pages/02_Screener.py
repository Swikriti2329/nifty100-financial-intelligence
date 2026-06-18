import sys
import os
import streamlit as st
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "analytics"))

from screener import get_latest_ratios, add_valuation_data
from health_score import compute_health_score

st.set_page_config(page_title="Screener", layout="wide")
st.title("Investment Screener")

@st.cache_data
def load_data():
    latest = get_latest_ratios()
    latest = add_valuation_data(latest)
    scores = compute_health_score(latest)
    return latest.merge(scores[["company_id", "health_score", "health_band"]], on="company_id", how="left")

data = load_data()

st.sidebar.header("Filters")

min_roe = st.sidebar.slider("Minimum ROE (%)", -50, 100, 0)
max_de = st.sidebar.slider("Maximum Debt-to-Equity", 0.0, 10.0, 10.0)
min_fcf = st.sidebar.number_input("Minimum Free Cash Flow (Cr)", value=-100000)

sector_options = sorted(data["broad_sector"].dropna().unique())
selected_sectors = st.sidebar.multiselect("Sectors", sector_options, default=sector_options)

filtered = data.copy()
filtered = filtered[
    (filtered["roe_pct"].fillna(-9999) >= min_roe) &
    (filtered["debt_to_equity"].fillna(9999) <= max_de) &
    (filtered["free_cash_flow_cr"].fillna(-9999999) >= min_fcf) &
    (filtered["broad_sector"].isin(selected_sectors))
]

st.write("**" + str(len(filtered)) + " companies match your filters**")

display_cols = ["company_id", "company_name", "broad_sector", "roe_pct",
                 "net_profit_margin_pct", "debt_to_equity", "free_cash_flow_cr",
                 "health_score", "health_band"]

st.dataframe(
    filtered[display_cols].sort_values("health_score", ascending=False, na_position="last"),
    use_container_width=True,
    hide_index=True
)

csv = filtered[display_cols].to_csv(index=False)
st.download_button("Download results as CSV", csv, "screener_results.csv", "text/csv")
