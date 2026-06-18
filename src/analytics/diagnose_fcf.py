import sqlite3
import pandas as pd
from ratios import load_table, compute_free_cash_flow

DB_PATH = "../../data/processed/nifty100.db"
conn = sqlite3.connect(DB_PATH)
cf = load_table("cashflow", conn)
conn.close()

fcf = compute_free_cash_flow(cf)
worst = fcf.loc[fcf["free_cash_flow_cr"].idxmin()]
print("Most negative FCF row:")
print(worst)

raw_cf = cf[(cf["company_id"] == worst["company_id"]) & (cf["year"] == worst["year"])]
print("Cash flow statement:")
print(raw_cf[["company_id", "year", "operating_activity", "investing_activity", "financing_activity"]])
