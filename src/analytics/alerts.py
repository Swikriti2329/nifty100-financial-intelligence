import sqlite3
import pathlib
import pandas as pd
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src" / "analytics"))

from screener import get_latest_ratios, add_valuation_data
from health_score import compute_health_score

DB_PATH = str(PROJECT_ROOT / "data" / "processed" / "nifty100.db")
OUTPUT_PATH = str(PROJECT_ROOT / "reports" / "alerts.csv")

def generate_alerts(data):
    alerts = []

    for _, row in data.iterrows():
        company = row["company_id"]
        name = row["company_name"]
        sector = row["broad_sector"]

        if pd.notna(row.get("roe_pct")) and row["roe_pct"] < 5:
            alerts.append({
                "company_id": company,
                "company_name": name,
                "broad_sector": sector,
                "alert_type": "Low ROE",
                "metric": "roe_pct",
                "value": row["roe_pct"],
                "threshold": 5,
                "severity": "WARNING"
            })

        if pd.notna(row.get("debt_to_equity")) and row["debt_to_equity"] > 3:
            alerts.append({
                "company_id": company,
                "company_name": name,
                "broad_sector": sector,
                "alert_type": "High Debt",
                "metric": "debt_to_equity",
                "value": row["debt_to_equity"],
                "threshold": 3,
                "severity": "WARNING"
            })

        if pd.notna(row.get("free_cash_flow_cr")) and row["free_cash_flow_cr"] < 0:
            alerts.append({
                "company_id": company,
                "company_name": name,
                "broad_sector": sector,
                "alert_type": "Negative FCF",
                "metric": "free_cash_flow_cr",
                "value": row["free_cash_flow_cr"],
                "threshold": 0,
                "severity": "CAUTION"
            })

        if pd.notna(row.get("health_score")) and row["health_score"] < 35:
            alerts.append({
                "company_id": company,
                "company_name": name,
                "broad_sector": sector,
                "alert_type": "Poor Health Score",
                "metric": "health_score",
                "value": row["health_score"],
                "threshold": 35,
                "severity": "CRITICAL"
            })

    return pd.DataFrame(alerts)

if __name__ == "__main__":
    latest = get_latest_ratios()
    latest = add_valuation_data(latest)
    scores = compute_health_score(latest)
    data = latest.merge(scores[["company_id", "health_score", "health_band"]], on="company_id", how="left")

    alerts = generate_alerts(data)
    alerts.to_csv(OUTPUT_PATH, index=False)

    print("Alert summary:")
    print(alerts["alert_type"].value_counts())
    print()
    print("CRITICAL alerts:")
    print(alerts[alerts["severity"] == "CRITICAL"][["company_id", "company_name", "alert_type", "value"]].to_string(index=False))
    print()
    print("Total alerts generated:", len(alerts))
    print("Saved to:", OUTPUT_PATH)
