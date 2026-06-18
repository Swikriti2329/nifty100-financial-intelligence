import sqlite3
import pandas as pd
from ratios import load_table, compute_roe

DB_PATH = "../../data/processed/nifty100.db"
conn = sqlite3.connect(DB_PATH)
pl = load_table("profitandloss", conn)
bs = load_table("balancesheet", conn)
conn.close()

roe = compute_roe(pl, bs)
worst = roe.loc[roe["roe_pct"].idxmax()]
print("Highest ROE row:")
print(worst)

raw_bs = bs[(bs["company_id"] == worst["company_id"]) & (bs["year"] == worst["year"])]
raw_pl = pl[(pl["company_id"] == worst["company_id"]) & (pl["year"] == worst["year"])]
print("Balance sheet:")
print(raw_bs[["company_id", "year", "equity_capital", "reserves"]])
print("P&L:")
print(raw_pl[["company_id", "year", "net_profit"]])
