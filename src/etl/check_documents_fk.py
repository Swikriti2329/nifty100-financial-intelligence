import pandas as pd
from normalize import normalize_ticker

RAW_DIR = "../../data/raw"

companies = pd.read_excel(f"{RAW_DIR}/companies.xlsx", header=1)
valid_tickers = set(companies["id"].apply(normalize_ticker))

documents = pd.read_excel(f"{RAW_DIR}/documents.xlsx", header=1)
documents["company_id"] = documents["company_id"].apply(normalize_ticker)

doc_tickers = set(documents["company_id"])

invalid_tickers = doc_tickers - valid_tickers

print("Valid companies in companies.xlsx:", len(valid_tickers))
print("Unique tickers in documents.xlsx:", len(doc_tickers))
print("Tickers in documents.xlsx with NO match in companies.xlsx:")
print(sorted(invalid_tickers))
print()
print("How many rows have these invalid tickers:")
print(documents[documents["company_id"].isin(invalid_tickers)]["company_id"].value_counts())
