import sqlite3
import pandas as pd
from ratios import load_table, compute_net_profit_margin, compute_roe, compute_debt_to_equity, compute_free_cash_flow

DB_PATH = "../../data/processed/nifty100.db"

def get_latest_ratios():
    """Build a single table: one row per company, using each company's
    most recent available year for every ratio."""
    conn = sqlite3.connect(DB_PATH)
    pl = load_table("profitandloss", conn)
    bs = load_table("balancesheet", conn)
    cf = load_table("cashflow", conn)
    sectors = load_table("sectors", conn)
    companies = load_table("companies", conn)
    conn.close()

    npm = compute_net_profit_margin(pl)
    roe = compute_roe(pl, bs)
    de = compute_debt_to_equity(bs, sectors)
    fcf = compute_free_cash_flow(cf)

    def latest_per_company(df, value_col):
        df = df.dropna(subset=[value_col])
        df = df.sort_values("year")
        return df.groupby("company_id").last().reset_index()[["company_id", value_col]]

    latest_npm = latest_per_company(npm, "net_profit_margin_pct")
    latest_roe = latest_per_company(roe, "roe_pct")
    latest_de = latest_per_company(de, "debt_to_equity")
    latest_fcf = latest_per_company(fcf, "free_cash_flow_cr")

    result = companies[["id", "company_name"]].rename(columns={"id": "company_id"})
    result["company_name"] = result["company_name"].astype(str).str.replace("\n", " ").str.strip()
    result["company_name"] = result["company_name"].astype(str).str.replace(chr(10), " ", regex=False).str.strip()
    result = result.merge(latest_npm, on="company_id", how="left")
    result = result.merge(latest_roe, on="company_id", how="left")
    result = result.merge(latest_de, on="company_id", how="left")
    result = result.merge(latest_fcf, on="company_id", how="left")
    result = result.merge(sectors[["company_id", "broad_sector"]], on="company_id", how="left")

    return result

def screen_quality_compounder(latest):
    """Preset: ROE > 15%, D/E < 1.0, FCF > 0"""
    mask = (
        (latest["roe_pct"] > 15) &
        (latest["debt_to_equity"] < 1.0) &
        (latest["free_cash_flow_cr"] > 0)
    )
    result = latest[mask].copy()
    result = result.sort_values("roe_pct", ascending=False)
    return result[["company_id", "company_name", "broad_sector", "roe_pct", "debt_to_equity", "free_cash_flow_cr"]]

def add_valuation_data(latest):
    """Bring in latest P/E ratio and dividend yield from market_cap table."""
    conn = sqlite3.connect(DB_PATH)
    market_cap = load_table("market_cap", conn)
    conn.close()

    market_cap = market_cap.sort_values("year")
    latest_val = market_cap.groupby("company_id").last().reset_index()
    latest_val = latest_val[["company_id", "pe_ratio", "dividend_yield_pct"]]

    return latest.merge(latest_val, on="company_id", how="left")

def screen_value_pick(latest):
    """Preset: P/E < 20, P/B not available here so using D/E < 2.0, Div Yield > 1%"""
    mask = (
        (latest["pe_ratio"] < 20) &
        (latest["debt_to_equity"] < 2.0) &
        (latest["dividend_yield_pct"] > 1)
    )
    result = latest[mask].copy().sort_values("pe_ratio")
    return result[["company_id", "company_name", "pe_ratio", "debt_to_equity", "dividend_yield_pct"]]

def screen_dividend_champion(latest):
    """Preset: Dividend Yield > 2%, FCF > 0"""
    mask = (
        (latest["dividend_yield_pct"] > 2) &
        (latest["free_cash_flow_cr"] > 0)
    )
    result = latest[mask].copy().sort_values("dividend_yield_pct", ascending=False)
    return result[["company_id", "company_name", "dividend_yield_pct", "free_cash_flow_cr"]]

def screen_debt_free_blue_chip(latest):
    """Preset: D/E < 0.05 (essentially debt-free), ROE > 12%"""
    mask = (
        (latest["debt_to_equity"] < 0.05) &
        (latest["roe_pct"] > 12)
    )
    result = latest[mask].copy().sort_values("roe_pct", ascending=False)
    return result[["company_id", "company_name", "broad_sector", "roe_pct", "debt_to_equity"]]

def screen_turnaround_watch(latest):
    """Preset: FCF > 0 (simplified - full version needs 3yr revenue CAGR, added later)"""
    mask = (latest["free_cash_flow_cr"] > 0) & (latest["net_profit_margin_pct"] < 5)
    result = latest[mask].copy().sort_values("free_cash_flow_cr", ascending=False)
    return result[["company_id", "company_name", "net_profit_margin_pct", "free_cash_flow_cr"]]

if __name__ == "__main__":
    latest = get_latest_ratios()
    latest = add_valuation_data(latest)
    print("Total companies with at least one ratio computed:", len(latest))

    quality = screen_quality_compounder(latest)
    print()
    print(f"Quality Compounder: {len(quality)} companies match")

    value = screen_value_pick(latest)
    print(f"Value Pick: {len(value)} companies match")

    dividend = screen_dividend_champion(latest)
    print(f"Dividend Champion: {len(dividend)} companies match")

    debtfree = screen_debt_free_blue_chip(latest)
    print(f"Debt-Free Blue Chip: {len(debtfree)} companies match")

    turnaround = screen_turnaround_watch(latest)
    print(f"Turnaround Watch: {len(turnaround)} companies match")
