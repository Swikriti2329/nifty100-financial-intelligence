import pandas as pd
from normalize import normalize_year

RAW_DIR = "../../data/raw"

def show_unparseable(filename):
    df = pd.read_excel(f"{RAW_DIR}/{filename}", header=1)
    raw_years = df["year"]
    cleaned = raw_years.apply(normalize_year)
    problem_rows = raw_years[cleaned == "PARSE_ERROR"]
    print(f"--- {filename} ---")
    print("Total problem rows:", len(problem_rows))
    print("Unique raw values that failed:")
    print(problem_rows.unique())
    print("Data type of these values:", problem_rows.apply(type).unique())
    print()

show_unparseable("profitandloss.xlsx")
show_unparseable("balancesheet.xlsx")
