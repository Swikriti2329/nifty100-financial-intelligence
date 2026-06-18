import pandas as pd
from normalize import normalize_ticker

RAW_DIR = "../../data/raw"

def load_analysis():
    df = pd.read_excel(f"{RAW_DIR}/analysis.xlsx", header=1)
    df["company_id"] = df["company_id"].apply(normalize_ticker)
    return df

def load_documents(valid_tickers):
    df = pd.read_excel(f"{RAW_DIR}/documents.xlsx", header=1)
    df["company_id"] = df["company_id"].apply(normalize_ticker)
    df["Year"] = df["Year"].astype(int)

    before = len(df)
    out_of_scope = df[~df["company_id"].isin(valid_tickers)]
    df = df[df["company_id"].isin(valid_tickers)].copy()
    after = len(df)

    print(f"  documents.xlsx: dropped {before - after} rows for companies outside the 92-company universe")
    if len(out_of_scope) > 0:
        out_of_scope.to_csv("../../reports/documents_out_of_scope.csv", index=False)

    return df

def load_prosandcons():
    df = pd.read_excel(f"{RAW_DIR}/prosandcons.xlsx", header=1)
    df["company_id"] = df["company_id"].apply(normalize_ticker)
    return df

if __name__ == "__main__":
    companies = pd.read_excel(f"{RAW_DIR}/companies.xlsx", header=1)
    valid_tickers = set(companies["id"].apply(normalize_ticker))

    analysis = load_analysis()
    print("analysis.xlsx ->", analysis.shape)
    print("  unique companies covered:", analysis["company_id"].nunique())

    documents = load_documents(valid_tickers)
    print("documents.xlsx ->", documents.shape)
    print("  unique companies covered:", documents["company_id"].nunique())
    print("  year range:", documents["Year"].min(), "to", documents["Year"].max())

    pros = load_prosandcons()
    print("prosandcons.xlsx ->", pros.shape)
    print("  unique companies covered:", pros["company_id"].nunique())
