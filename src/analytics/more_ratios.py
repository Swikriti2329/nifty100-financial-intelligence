import sqlite3
import pandas as pd
from ratios import load_table

DB_PATH = "../../data/processed/nifty100.db"

def compute_opm(pl):
    pl = pl.copy()
    def calc(row):
        sales = row["sales"]
        op_profit = row["operating_profit"]
        if pd.isna(sales) or sales == 0:
            return None
        ratio = op_profit / sales * 100
        if abs(ratio) > 100:
            return None
        return ratio
    pl["opm_pct"] = pl.apply(calc, axis=1)
    return pl[["company_id", "year", "opm_pct"]]

def compute_interest_coverage(pl):
    pl = pl.copy()
    def calc(row):
        interest = row["interest"]
        if pd.isna(interest) or interest == 0:
            return None
        numerator = row["operating_profit"] + (row["other_income"] if pd.notna(row["other_income"]) else 0)
        icr = numerator / interest
        if abs(icr) > 50:
            return None
        return icr
    pl["interest_coverage"] = pl.apply(calc, axis=1)
    return pl[["company_id", "year", "interest_coverage"]]

def compute_pb_ratio(market_cap, bs):
    bs = bs.copy()
    bs["total_equity"] = bs["equity_capital"] + bs["reserves"]
    valid_years = ~bs["year"].isin(["PARSE_ERROR", "TTM"])
    bs = bs[valid_years].copy()
    bs["calendar_year"] = bs["year"].str[:4].astype(int)
    market_cap = market_cap.copy()
    market_cap["calendar_year"] = market_cap["year"].astype(int)
    merged = market_cap.merge(
        bs[["company_id", "calendar_year", "total_equity"]],
        on=["company_id", "calendar_year"], how="inner"
    )
    def calc(row):
        equity = row["total_equity"]
        if pd.isna(equity) or equity <= 0:
            return None
        pb = row["market_cap_crore"] / equity
        if pb > 50:
            return None
        return pb
    merged["pb_ratio"] = merged.apply(calc, axis=1)
    return merged[["company_id", "calendar_year", "pb_ratio"]]

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    pl = load_table("profitandloss", conn)
    bs = load_table("balancesheet", conn)
    market_cap = load_table("market_cap", conn)
    conn.close()

    opm = compute_opm(pl)
    valid_opm = opm["opm_pct"].dropna()
    print("OPM stats: min={:.2f}, max={:.2f}, nulls={}".format(
        valid_opm.min(), valid_opm.max(), opm["opm_pct"].isna().sum()))

    icr = compute_interest_coverage(pl)
    valid_icr = icr["interest_coverage"].dropna()
    print("ICR stats: min={:.2f}, max={:.2f}, nulls={} (nulls include debt-free companies)".format(
        valid_icr.min(), valid_icr.max(), icr["interest_coverage"].isna().sum()))

    pb = compute_pb_ratio(market_cap, bs)
    valid_pb = pb["pb_ratio"].dropna()
    print("P/B stats: min={:.2f}, max={:.2f}, nulls={}".format(
        valid_pb.min(), valid_pb.max(), pb["pb_ratio"].isna().sum()))
