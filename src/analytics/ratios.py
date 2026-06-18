import sqlite3
import pandas as pd

DB_PATH = "../../data/processed/nifty100.db"

def load_table(table_name, conn):
    return pd.read_sql(f"SELECT * FROM {table_name}", conn)

def compute_net_profit_margin(pl):
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
    merged = pd.merge(
        pl[["company_id", "year", "net_profit"]],
        bs[["company_id", "year", "equity_capital", "reserves"]],
        on=["company_id", "year"], how="inner"
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

def compute_debt_to_equity(bs, sectors):
    bs = bs.copy()
    bs["total_equity"] = bs["equity_capital"] + bs["reserves"]
    bs = bs.merge(sectors[["company_id", "broad_sector"]], on="company_id", how="left")
    def calc(row):
        if row["broad_sector"] == "Financials":
            return None
        equity = row["total_equity"]
        borrowings = row["borrowings"]
        if pd.isna(equity) or equity <= 0:
            return None
        if pd.isna(borrowings):
            return None
        return borrowings / equity
    bs["debt_to_equity"] = bs.apply(calc, axis=1)
    return bs[["company_id", "year", "debt_to_equity"]]

def compute_free_cash_flow(cf):
    cf = cf.copy()
    cf["free_cash_flow_cr"] = cf["operating_activity"] + cf["investing_activity"]
    return cf[["company_id", "year", "free_cash_flow_cr"]]

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    pl = load_table("profitandloss", conn)
    bs = load_table("balancesheet", conn)
    cf = load_table("cashflow", conn)
    sectors = load_table("sectors", conn)
    conn.close()

    npm = compute_net_profit_margin(pl)
    print("NPM stats: min={:.2f}, max={:.2f}, nulls={}".format(
        npm["net_profit_margin_pct"].min(), npm["net_profit_margin_pct"].max(),
        npm["net_profit_margin_pct"].isna().sum()))

    roe = compute_roe(pl, bs)
    print("ROE stats: min={:.2f}, max={:.2f}, nulls={}".format(
        roe["roe_pct"].min(), roe["roe_pct"].max(), roe["roe_pct"].isna().sum()))

    de = compute_debt_to_equity(bs, sectors)
    valid_de = de["debt_to_equity"].dropna()
    print("D/E stats: min={:.2f}, max={:.2f}, nulls={}, debt-free count={}".format(
        valid_de.min(), valid_de.max(), de["debt_to_equity"].isna().sum(),
        (de["debt_to_equity"] == 0).sum()))

    fcf = compute_free_cash_flow(cf)
    print("FCF stats (Cr): min={:.2f}, max={:.2f}, nulls={}, negative count={}".format(
        fcf["free_cash_flow_cr"].min(), fcf["free_cash_flow_cr"].max(),
        fcf["free_cash_flow_cr"].isna().sum(), (fcf["free_cash_flow_cr"] < 0).sum()))
