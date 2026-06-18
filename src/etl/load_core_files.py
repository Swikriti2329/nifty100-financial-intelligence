import pandas as pd
from normalize import normalize_ticker, normalize_year

RAW_DIR = "../../data/raw"

def load_companies():
    df = pd.read_excel(f"{RAW_DIR}/companies.xlsx", header=1)
    df["id"] = df["id"].apply(normalize_ticker)
    return df

def load_timeseries_file(filename, id_col="company_id"):
    df = pd.read_excel(f"{RAW_DIR}/{filename}", header=1)
    df[id_col] = df[id_col].apply(normalize_ticker)
    df["year"] = df["year"].apply(normalize_year)
    return df

if __name__ == "__main__":
    companies = load_companies()
    print("companies.xlsx ->", companies.shape)

    pl = load_timeseries_file("profitandloss.xlsx")
    print("profitandloss.xlsx ->", pl.shape)
    print("  sample years:", pl["year"].head(5).tolist())

    bs = load_timeseries_file("balancesheet.xlsx")
    print("balancesheet.xlsx ->", bs.shape)
    print("  sample years:", bs["year"].head(5).tolist())

    cf = load_timeseries_file("cashflow.xlsx")
    print("cashflow.xlsx ->", cf.shape)
    print("  sample years:", cf["year"].head(5).tolist())

    print()
    print("Any PARSE_ERROR years in P&L?", (pl["year"] == "PARSE_ERROR").sum())
    print("Any PARSE_ERROR years in BS?", (bs["year"] == "PARSE_ERROR").sum())
    print("Any PARSE_ERROR years in CF?", (cf["year"] == "PARSE_ERROR").sum())
