import sqlite3
import pandas as pd
from ratios import load_table, compute_debt_to_equity

DB_PATH = "../../data/processed/nifty100.db"
conn = sqlite3.connect(DB_PATH)
bs = load_table("balancesheet", conn)
sectors = load_table("sectors", conn)
conn.close()

de = compute_debt_to_equity(bs, sectors)
valid_de = de.dropna(subset=["debt_to_equity"])
worst = valid_de.loc[valid_de["debt_to_equity"].idxmax()]
print("Highest non-Financials D/E row:")
print(worst)

raw_bs = bs[(bs["company_id"] == worst["company_id"]) & (bs["year"] == worst["year"])]
print("Balance sheet:")
print(raw_bs[["company_id", "year", "borrowings", "equity_capital", "reserves"]])

sector_row = sectors[sectors["company_id"] == worst["company_id"]]
print("Sector:")
print(sector_row[["company_id", "broad_sector", "sub_sector"]])
