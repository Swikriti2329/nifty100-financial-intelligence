import pandas as pd
from screener import get_latest_ratios

def compute_sector_medians(latest):
    """Median value of each key ratio, per broad sector."""
    metrics = ["roe_pct", "net_profit_margin_pct", "debt_to_equity", "free_cash_flow_cr"]
    medians = latest.groupby("broad_sector")[metrics].median().round(2)
    medians = medians.rename(columns={
        "roe_pct": "median_roe_pct",
        "net_profit_margin_pct": "median_npm_pct",
        "debt_to_equity": "median_debt_to_equity",
        "free_cash_flow_cr": "median_fcf_cr",
    })
    counts = latest.groupby("broad_sector").size().rename("company_count")
    return medians.join(counts).sort_values("median_roe_pct", ascending=False)

def compute_sector_rank(latest, metric="roe_pct"):
    """Rank each company within its own sector (1 = best in sector) for a given metric."""
    df = latest.copy()
    df = df.dropna(subset=[metric])
    df["sector_rank"] = df.groupby("broad_sector")[metric].rank(ascending=False, method="min").astype(int)
    df["sector_size"] = df.groupby("broad_sector")[metric].transform("count").astype(int)
    return df[["company_id", "company_name", "broad_sector", metric, "sector_rank", "sector_size"]].sort_values(
        ["broad_sector", "sector_rank"]
    )

if __name__ == "__main__":
    latest = get_latest_ratios()

    print("=== Sector Medians (sorted by median ROE) ===")
    medians = compute_sector_medians(latest)
    print(medians.to_string())

    print()
    print("=== Sector Ranking by ROE (Information Technology sector) ===")
    ranked = compute_sector_rank(latest, metric="roe_pct")
    it_sector = ranked[ranked["broad_sector"] == "Information Technology"]
    print(it_sector.to_string(index=False))
