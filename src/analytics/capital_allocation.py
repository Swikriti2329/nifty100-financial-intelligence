import sqlite3
import pandas as pd
from ratios import load_table

DB_PATH = "../../data/processed/nifty100.db"

def classify_capital_allocation(cf):
    """Classify each company-year into one of 8 capital allocation patterns
    based on the sign of CFO, CFI, and CFF, exactly matching the project
    spec's capital allocation matrix definition."""
    cf = cf.copy()

    def sign(val):
        if pd.isna(val):
            return None
        return "+" if val >= 0 else "-"

    def classify(row):
        cfo = sign(row["operating_activity"])
        cfi = sign(row["investing_activity"])
        cff = sign(row["financing_activity"])

        if None in [cfo, cfi, cff]:
            return "Unknown"

        pattern = (cfo, cfi, cff)

        patterns = {
            ("+", "-", "-"): "Reinvestor",
            ("+", "-", "+"): "Aggressive Growth",
            ("+", "+", "-"): "Shareholder Returns",
            ("+", "+", "+"): "Cash Accumulator",
            ("-", "-", "+"): "Distress Signal",
            ("-", "+", "+"): "Asset Seller",
            ("-", "-", "-"): "Cash Burn",
            ("-", "+", "-"): "Restructuring",
        }

        return patterns.get(pattern, "Unknown")

    cf["cfo_sign"] = cf["operating_activity"].apply(lambda x: "+" if pd.notna(x) and x >= 0 else "-")
    cf["cfi_sign"] = cf["investing_activity"].apply(lambda x: "+" if pd.notna(x) and x >= 0 else "-")
    cf["cff_sign"] = cf["financing_activity"].apply(lambda x: "+" if pd.notna(x) and x >= 0 else "-")
    cf["capital_allocation_pattern"] = cf.apply(classify, axis=1)

    return cf[["company_id", "year", "cfo_sign", "cfi_sign", "cff_sign", "capital_allocation_pattern"]]

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    cf = load_table("cashflow", conn)
    conn.close()

    result = classify_capital_allocation(cf)

    print("Capital allocation pattern distribution (latest year):")
    latest = result.sort_values("year").groupby("company_id").last().reset_index()
    print(latest["capital_allocation_pattern"].value_counts())

    print()
    print("Sample companies and their latest pattern:")
    sample = latest[latest["company_id"].isin(["TCS", "RELIANCE", "INDIGO", "TATASTEEL", "ITC"])]
    print(sample[["company_id", "cfo_sign", "cfi_sign", "cff_sign", "capital_allocation_pattern"]].to_string(index=False))
