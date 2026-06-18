import sqlite3
import pandas as pd
from ratios import load_table

DB_PATH = "../../data/processed/nifty100.db"
conn = sqlite3.connect(DB_PATH)
pl = load_table("profitandloss", conn)
bs = load_table("balancesheet", conn)
conn.close()

merged = pd.merge(
    pl[["company_id", "year", "net_profit"]],
    bs[["company_id", "year", "equity_capital", "reserves"]],
    on=["company_id", "year"], how="inner"
)
merged["total_equity"] = merged["equity_capital"] + merged["reserves"]
merged["raw_roe_pct"] = merged["net_profit"] / merged["total_equity"] * 100
flagged = merged[merged["raw_roe_pct"].abs() > 200].copy()
flagged.to_csv("../../reports/ratio_anomalies.csv", index=False)
print(f"Logged {len(flagged)} extreme ROE cases to reports/ratio_anomalies.csv")
print(flagged[["company_id", "year", "net_profit", "total_equity", "raw_roe_pct"]])
