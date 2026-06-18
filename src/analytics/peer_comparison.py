import sqlite3
import pandas as pd
from screener import get_latest_ratios

DB_PATH = "../../data/processed/nifty100.db"

def load_peer_groups():
    conn = sqlite3.connect(DB_PATH)
    peer_groups = pd.read_sql("SELECT * FROM peer_groups", conn)
    conn.close()
    return peer_groups

def compute_peer_rank(latest, peer_groups, metric="roe_pct"):
    """For each company, rank it within its specific peer group (not broad sector)."""
    merged = peer_groups.merge(latest, on="company_id", how="left")
    merged = merged.dropna(subset=[metric])

    merged["peer_rank"] = merged.groupby("peer_group_name")[metric].rank(ascending=False, method="min").astype(int)
    merged["peer_group_size"] = merged.groupby("peer_group_name")[metric].transform("count").astype(int)

    return merged[["company_id", "company_name", "peer_group_name", metric, "peer_rank",
                   "peer_group_size", "is_benchmark"]].sort_values(["peer_group_name", "peer_rank"])

def show_one_group(ranked, group_name):
    return ranked[ranked["peer_group_name"] == group_name]

if __name__ == "__main__":
    latest = get_latest_ratios()
    peer_groups = load_peer_groups()

    ranked = compute_peer_rank(latest, peer_groups, metric="roe_pct")

    print("How many peer groups have data:", ranked["peer_group_name"].nunique())
    print()

    print("=== Private Banks peer group, ranked by ROE ===")
    print(show_one_group(ranked, "Private Banks").to_string(index=False))

    print()
    print("=== IT Services peer group, ranked by ROE ===")
    print(show_one_group(ranked, "IT Services").to_string(index=False))
