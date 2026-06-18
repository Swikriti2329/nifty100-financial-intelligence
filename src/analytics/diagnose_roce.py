import sqlite3
import pandas as pd
from ratios import load_table
from growth_ratios import compute_roce

DB_PATH = "../../data/processed/nifty100.db"
conn = sqlite3.connect(DB_PATH)
pl = load_table("profitandloss", conn)
bs = load_table("balancesheet", conn)
sectors = load_table("sectors", conn)
conn.close()

merged = pd.merge(
    pl[["company_id", "year", "operating_profit", "depreciation"]],
    bs[["company_id", "year", "equity_capital", "reserves", "borrowings"]],
    on=["company_id", "year"], how="inner"
)
merged = merged.merge(sectors[["company_id", "broad_sector"]], on="company_id", how="left")

print("Total merged rows:", len(merged))
print("Rows where sector is Financials:", (merged["broad_sector"] == "Financials").sum())
print("Rows with missing depreciation:", merged["depreciation"].isna().sum())
print("Rows with missing operating_profit:", merged["operating_profit"].isna().sum())

capital_employed = merged["equity_capital"] + merged["reserves"] + merged["borrowings"]
print("Rows where capital_employed <= 0:", (capital_employed <= 0).sum())
print("Rows where capital_employed is null:", capital_employed.isna().sum())
