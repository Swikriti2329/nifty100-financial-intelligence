import sys
import os
import sqlite3
import pandas as pd
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "analytics"))

from ratios import load_table
from screener import get_latest_ratios, add_valuation_data
from health_score import compute_health_score
from growth_ratios import compute_roce, compute_revenue_cagr_5yr

import pathlib
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
DB_PATH = str(PROJECT_ROOT / "data" / "processed" / "nifty100.db")

st.set_page_config(page_title="Company Profile", layout="wide")
st.title("Company Profile")

@st.cache_data
def load_everything():
    conn = sqlite3.connect(DB_PATH)
    pl = load_table("profitandloss", conn)
    bs = load_table("balancesheet", conn)
    sectors = load_table("sectors", conn)
    conn.close()

    latest = get_latest_ratios()
    latest = add_valuation_data(latest)
    scores = compute_health_score(latest)
    roce = compute_roce(pl, bs, sectors)
    cagr = compute_revenue_cagr_5yr(pl)

    latest = latest.merge(scores[["company_id", "health_score", "health_band"]], on="company_id", how="left")
    latest_roce = roce.dropna(subset=["roce_pct"]).sort_values("year").groupby("company_id").last().reset_index()
    latest = latest.merge(latest_roce[["company_id", "roce_pct"]], on="company_id", how="left")
    latest = latest.merge(cagr, on="company_id", how="left")

    return latest, pl

latest, pl = load_everything()

company_list = latest[["company_id", "company_name"]].sort_values("company_name")
options = company_list["company_id"] + " - " + company_list["company_name"]
selected = st.selectbox("Search for a company", options)
selected_id = selected.split(" - ")[0]

row = latest[latest["company_id"] == selected_id].iloc[0]

st.header(row["company_name"])
st.caption("Sector: " + str(row["broad_sector"]) + "  |  Health Band: " + str(row["health_band"]))

c1, c2, c3, c4, c5 = st.columns(5)
roe_val = row["roe_pct"]
npm_val = row["net_profit_margin_pct"]
de_val = row["debt_to_equity"]
fcf_val = row["free_cash_flow_cr"]
roce_val = row["roce_pct"]

c1.metric("ROE", "N/A" if pd.isna(roe_val) else "{:.1f}%".format(roe_val))
c2.metric("Net Profit Margin", "N/A" if pd.isna(npm_val) else "{:.1f}%".format(npm_val))
c3.metric("Debt-to-Equity", "N/A" if pd.isna(de_val) else "{:.2f}".format(de_val))
c4.metric("Free Cash Flow", "N/A" if pd.isna(fcf_val) else "Rs {:,.0f} Cr".format(fcf_val))
c5.metric("ROCE", "N/A" if pd.isna(roce_val) else "{:.1f}%".format(roce_val))

score_val = row["health_score"]
score_display = "N/A" if pd.isna(score_val) else "{:.0f} / 100".format(score_val)
st.metric("Financial Health Score", score_display)

st.subheader("Revenue and Net Profit Over Time")
history = pl[pl["company_id"] == selected_id].sort_values("year")
history = history.dropna(subset=["sales"])

if len(history) > 0:
    chart_data = history.set_index("year")[["sales", "net_profit"]]
    chart_data = chart_data.rename(columns={"sales": "Revenue (Cr)", "net_profit": "Net Profit (Cr)"})
    st.line_chart(chart_data)
else:
    st.write("No historical data available for this company.")
