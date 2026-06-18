import pandas as pd
from screener import get_latest_ratios

def percentile_score(series):
    """Convert a column of values into a 0-100 percentile rank.
    Higher raw value = higher score. NaNs are left as NaN."""
    return series.rank(pct=True, na_option="keep") * 100

def compute_health_score(latest):
    df = latest.copy()
    is_financials = df["broad_sector"] == "Financials"

    df["roe_score"] = percentile_score(df["roe_pct"])
    df["npm_score"] = percentile_score(df["net_profit_margin_pct"])
    df["fcf_score"] = percentile_score(df["free_cash_flow_cr"])
    df["de_score"] = percentile_score(-df["debt_to_equity"])  # lower debt = better

    weights = {
        "roe_score": 0.30,
        "npm_score": 0.25,
        "fcf_score": 0.25,
        "de_score": 0.20,
    }

    def weighted_average(row):
        total_weight = 0
        weighted_sum = 0
        for col, w in weights.items():
            if pd.notna(row[col]):
                weighted_sum += row[col] * w
                total_weight += w
        if total_weight == 0:
            return None
        return weighted_sum / total_weight

    df["health_score"] = df.apply(weighted_average, axis=1)

    # Standard companies get a real ratio-based score for businesses; Financials
    # (banks/NBFCs/insurers) don't fit these formulas well, so we mark them
    # as Not Applicable rather than give a misleading score - this matches
    # the project spec's own guidance to treat Financials sector-relatively.
    df.loc[is_financials, "health_score"] = None

    def band(score, is_fin):
        if is_fin:
            return "Not Applicable (Financials)"
        if pd.isna(score):
            return "No Data"
        if score >= 80:
            return "Excellent"
        elif score >= 65:
            return "Good"
        elif score >= 50:
            return "Average"
        elif score >= 35:
            return "Weak"
        else:
            return "Poor"

    df["health_band"] = [
        band(score, fin) for score, fin in zip(df["health_score"], is_financials)
    ]

    return df[["company_id", "company_name", "broad_sector", "health_score", "health_band"]].sort_values(
        "health_score", ascending=False, na_position="last"
    )

if __name__ == "__main__":
    latest = get_latest_ratios()
    scores = compute_health_score(latest)

    print("Health score distribution by band:")
    print(scores["health_band"].value_counts())
    print()
    print("Top 10 companies:")
    print(scores.head(10).to_string(index=False))
    print()
    non_financials = scores[scores["health_band"] != "Not Applicable (Financials)"]
    print("Bottom 10 companies (excluding Financials, which are marked Not Applicable):")
    print(non_financials.tail(10).to_string(index=False))
