import sqlite3
import pandas as pd
from screener import get_latest_ratios, add_valuation_data

latest = get_latest_ratios()
latest = add_valuation_data(latest)

print("How many companies have debt_to_equity == 0 exactly:")
print((latest["debt_to_equity"] == 0).sum())

print()
print("Distribution of debt_to_equity values near zero:")
print(latest[latest["debt_to_equity"] < 0.05][["company_id", "debt_to_equity", "roe_pct"]])

print()
print("How many companies have roe_pct > 12:")
print((latest["roe_pct"] > 12).sum())

print()
print("Companies with debt_to_equity == 0 AND roe_pct not null:")
zero_de = latest[latest["debt_to_equity"] == 0]
print(zero_de[["company_id", "debt_to_equity", "roe_pct"]])
