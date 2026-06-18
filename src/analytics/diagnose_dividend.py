from screener import get_latest_ratios, add_valuation_data

latest = get_latest_ratios()
latest = add_valuation_data(latest)

print("Dividend yield stats:")
print(latest["dividend_yield_pct"].describe())

print()
print("Sample of dividend yield values:")
print(latest[["company_id", "dividend_yield_pct"]].head(15))
