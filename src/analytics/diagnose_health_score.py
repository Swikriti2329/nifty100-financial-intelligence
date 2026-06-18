import sqlite3
import pandas as pd
from screener import get_latest_ratios
from health_score import compute_health_score, percentile_score

latest = get_latest_ratios()

# Show the raw component scores for the three insurance companies
df = latest.copy()
df["roe_score"] = percentile_score(df["roe_pct"])
df["npm_score"] = percentile_score(df["net_profit_margin_pct"])
df["fcf_score"] = percentile_score(df["free_cash_flow_cr"])
df["de_score"] = percentile_score(-df["debt_to_equity"])

insurers = df[df["company_id"].isin(["SBILIFE", "HDFCLIFE", "ICICIPRULI"])]
print("Component scores for life insurers:")
print(insurers[["company_id", "roe_pct", "roe_score", "net_profit_margin_pct", "npm_score",
                 "free_cash_flow_cr", "fcf_score", "debt_to_equity", "de_score"]].to_string(index=False))

print()
print("Average FCF score by sector:")
print(df.groupby("broad_sector")["fcf_score"].mean().sort_values())
