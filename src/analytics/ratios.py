import sqlite3
import pandas as pd

DB_PATH = "../../data/processed/nifty100.db"

def load_table(table_name, conn):
    return pd.read_sql(f"SELECT * FROM {table_name}", conn)

def compute_net_profit_margin(pl):
    """NPM = net_profit / sales * 100.
    None if sales is 0/missing, or if the resulting ratio is implausibly
    extreme (common for holding companies, or data quality issues)."""
    pl = pl.copy()

    def calc(row):
        sales = row["sales"]
        profit = row["net_profit"]
        if pd.isna(sales) or sales == 0:
            return None
        ratio = profit / sales * 100
        if abs(ratio) > 200:
            return None
        return ratio

    pl["net_profit_margin_pct"] = pl.apply(calc, axis=1)
    return pl[["company_id", "year", "net_profit_margin_pct"]]

def compute_roe(pl, bs):
    """ROE = net_profit / (equity_capital + reserves) * 100.
    None if equity <= 0, or if the resulting ratio is implausibly extreme
    (usually indicates a near-zero equity base or a data quality issue)."""
    merged = pd.merge(
        pl[["company_id", "year", "net_profit"]],
        bs[["company_id", "year", "equity_capital", "reserves"]],
        on=["company_id", "year"],
        how="inner"
    )
    merged["total_equity"] = merged["equity_capital"] + merged["reserves"]

    def calc(row):
        equity = row["total_equity"]
        if pd.isna(equity) or equity <= 0:
            return None
        ratio = row["net_profit"] / equity * 100
        if abs(ratio) > 200:
            return None
        return ratio

    merged["roe_pct"] = merged.apply(calc, axis=1)
    return merged[["company_id", "year", "roe_pct"]]

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    pl = load_table("profitandloss", conn)
    bs = load_table("balancesheet", conn)
    conn.close()

    npm = compute_net_profit_margin(pl)
    print("NPM stats: min={:.2f}, max={:.2f}, nulls={}".format(
        npm["net_profit_margin_pct"].min(),
        npm["net_profit_margin_pct"].max(),
        npm["net_profit_margin_pct"].isna().sum()
    ))

    roe = compute_roe(pl, bs)
    print("ROE stats: min={:.2f}, max={:.2f}, nulls={}".format(
        roe["roe_pct"].min(),
        roe["roe_pct"].max(),
        roe["roe_pct"].isna().sum()
    ))
