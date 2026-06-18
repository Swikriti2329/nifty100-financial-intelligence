import pandas as pd
from normalize import normalize_year

RAW_DIR = "../../data/raw"

def log_unparseable_years(filename):
    df = pd.read_excel(f"{RAW_DIR}/{filename}", header=1)
    df["year_clean"] = df["year"].apply(normalize_year)
    bad_rows = df[df["year_clean"] == "PARSE_ERROR"][["company_id", "year"]]
    bad_rows = bad_rows.copy()
    bad_rows["source_file"] = filename
    return bad_rows

all_bad = pd.concat([
    log_unparseable_years("profitandloss.xlsx"),
    log_unparseable_years("balancesheet.xlsx"),
    log_unparseable_years("cashflow.xlsx"),
])

all_bad.to_csv("../../reports/parse_failures.csv", index=False)
print("Logged", len(all_bad), "unparseable year values to reports/parse_failures.csv")
print(all_bad)
