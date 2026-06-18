import sqlite3
import pandas as pd
from normalize import normalize_ticker, normalize_year

RAW_DIR = "../../data/raw"
SUPPORTING_DIR = "../../data/supporting"
DB_PATH = "../../data/processed/nifty100.db"

def load_companies():
    df = pd.read_excel(f"{RAW_DIR}/companies.xlsx", header=1)
    df["id"] = df["id"].apply(normalize_ticker)
    df["company_name"] = df["company_name"].astype(str).str.strip()
    return df

def load_timeseries_file(filename, id_col="company_id"):
    df = pd.read_excel(f"{RAW_DIR}/{filename}", header=1)
    df[id_col] = df[id_col].apply(normalize_ticker)
    df["year"] = df["year"].apply(normalize_year)
    return df

def load_documents(valid_tickers):
    df = pd.read_excel(f"{RAW_DIR}/documents.xlsx", header=1)
    df["company_id"] = df["company_id"].apply(normalize_ticker)
    df["Year"] = df["Year"].astype(int)
    df = df[df["company_id"].isin(valid_tickers)].copy()
    return df

def load_simple_file(filename, id_col="company_id"):
    df = pd.read_excel(f"{RAW_DIR}/{filename}", header=1)
    df[id_col] = df[id_col].apply(normalize_ticker)
    return df

def load_supporting_file(filename, id_col="company_id"):
    df = pd.read_excel(f"{SUPPORTING_DIR}/{filename}", header=0)
    if id_col in df.columns:
        df[id_col] = df[id_col].apply(normalize_ticker)
    return df

def main():
    companies = load_companies()
    valid_tickers = set(companies["id"])

    profitandloss = load_timeseries_file("profitandloss.xlsx")
    balancesheet = load_timeseries_file("balancesheet.xlsx")
    cashflow = load_timeseries_file("cashflow.xlsx")
    analysis = load_simple_file("analysis.xlsx")
    documents = load_documents(valid_tickers)
    prosandcons = load_simple_file("prosandcons.xlsx")

    sectors = load_supporting_file("sectors.xlsx")
    stock_prices = load_supporting_file("stock_prices.xlsx")
    market_cap = load_supporting_file("market_cap.xlsx")
    financial_ratios = load_supporting_file("financial_ratios.xlsx")
    peer_groups = load_supporting_file("peer_groups.xlsx", id_col="member_company_id") if "member_company_id" in pd.read_excel(f"{SUPPORTING_DIR}/peer_groups.xlsx", header=0).columns else pd.read_excel(f"{SUPPORTING_DIR}/peer_groups.xlsx", header=0)

    conn = sqlite3.connect(DB_PATH)

    tables = {
        "companies": companies,
        "profitandloss": profitandloss,
        "balancesheet": balancesheet,
        "cashflow": cashflow,
        "analysis": analysis,
        "documents": documents,
        "prosandcons": prosandcons,
        "sectors": sectors,
        "stock_prices": stock_prices,
        "market_cap": market_cap,
        "financial_ratios": financial_ratios,
        "peer_groups": peer_groups,
    }

    print("Writing tables to", DB_PATH)
    for name, df in tables.items():
        df.to_sql(name, conn, if_exists="replace", index=False)
        print(f"  {name}: {len(df)} rows written")

    conn.close()
    print("Done. Database created successfully.")

if __name__ == "__main__":
    main()
