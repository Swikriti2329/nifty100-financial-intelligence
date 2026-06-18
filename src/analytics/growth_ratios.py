import sqlite3
import pandas as pd
from ratios import load_table

DB_PATH = "../../data/processed/nifty100.db"

def compute_roce(pl, bs, sectors):
    """ROCE = EBIT / (equity + reserves + borrowings) * 100.
    EBIT = operating_profit - depreciation.
    Excluded for Financials sector, same reasoning as D/E (borrowings
    means something different for banks/NBFCs/insurers)."""
    merged = pd.merge(
        pl[["company_id", "year", "operating_profit", "depreciation"]],
        bs[["company_id", "year", "equity_capital", "reserves", "borrowings"]],
        on=["company_id", "year"], how="inner"
    )
    merged = merged.merge(sectors[["company_id", "broad_sector"]], on="company_id", how="left")

    merged["ebit"] = merged["operating_profit"] - merged["depreciation"].fillna(0)
    merged["capital_employed"] = merged["equity_capital"] + merged["reserves"] + merged["borrowings"]

    def calc(row):
        if row["broad_sector"] == "Financials":
            return None
        cap = row["capital_employed"]
        if pd.isna(cap) or cap <= 0:
            return None
        ratio = row["ebit"] / cap * 100
        if abs(ratio) > 200:
            return None
        return ratio

    merged["roce_pct"] = merged.apply(calc, axis=1)
    return merged[["company_id", "year", "roce_pct"]]

def compute_revenue_cagr_5yr(pl):
    """5-year Revenue CAGR = ((end_sales / start_sales)^(1/5) - 1) * 100.
    None if fewer than 5 years of history, or if start_sales <= 0
    (a negative-to-positive turnaround makes CAGR meaningless - flagged
    separately rather than computed, matching the project spec's
    turnaround-flag logic)."""
    results = []
    for company_id, group in pl.groupby("company_id"):
        group = group.dropna(subset=["sales"]).sort_values("year")
        if len(group) < 6:  # need at least 6 data points to span a 5-year gap
            results.append({"company_id": company_id, "revenue_cagr_5yr_pct": None})
            continue

        start_sales = group.iloc[-6]["sales"]
        end_sales = group.iloc[-1]["sales"]

        if start_sales <= 0 or end_sales <= 0:
            results.append({"company_id": company_id, "revenue_cagr_5yr_pct": None})
            continue

        cagr = ((end_sales / start_sales) ** (1/5) - 1) * 100
        results.append({"company_id": company_id, "revenue_cagr_5yr_pct": cagr})

    return pd.DataFrame(results)

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    pl = load_table("profitandloss", conn)
    bs = load_table("balancesheet", conn)
    sectors = load_table("sectors", conn)
    conn.close()

    roce = compute_roce(pl, bs, sectors)
    valid_roce = roce["roce_pct"].dropna()
    print("ROCE stats: min={:.2f}, max={:.2f}, nulls={}".format(
        valid_roce.min(), valid_roce.max(), roce["roce_pct"].isna().sum()))

    cagr = compute_revenue_cagr_5yr(pl)
    valid_cagr = cagr["revenue_cagr_5yr_pct"].dropna()
    print("Revenue CAGR (5yr) stats: min={:.2f}, max={:.2f}, nulls={}".format(
        valid_cagr.min(), valid_cagr.max(), cagr["revenue_cagr_5yr_pct"].isna().sum()))

    print()
    print("Sample CAGR values:")
    print(cagr.dropna().head(10).to_string(index=False))
