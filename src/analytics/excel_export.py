import sqlite3
import pathlib
import pandas as pd
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src" / "analytics"))

from screener import get_latest_ratios, add_valuation_data
from health_score import compute_health_score
from growth_ratios import compute_roce, compute_revenue_cagr_5yr
from more_ratios import compute_opm, compute_interest_coverage
from capital_allocation import classify_capital_allocation
from ratios import load_table

DB_PATH = str(PROJECT_ROOT / "data" / "processed" / "nifty100.db")
OUTPUT_PATH = str(PROJECT_ROOT / "output" / "nifty100_full_universe.xlsx")

def build_full_universe():
    conn = sqlite3.connect(DB_PATH)
    pl = load_table("profitandloss", conn)
    bs = load_table("balancesheet", conn)
    sectors = load_table("sectors", conn)
    cf = load_table("cashflow", conn)
    conn.close()

    latest = get_latest_ratios()
    latest = add_valuation_data(latest)
    scores = compute_health_score(latest)

    latest_opm = compute_opm(pl).sort_values("year").groupby("company_id").last().reset_index()[["company_id", "opm_pct"]]
    latest_icr = compute_interest_coverage(pl).sort_values("year").groupby("company_id").last().reset_index()[["company_id", "interest_coverage"]]
    latest_cap = classify_capital_allocation(cf).sort_values("year").groupby("company_id").last().reset_index()[["company_id", "capital_allocation_pattern"]]

    result = latest.merge(scores[["company_id", "health_score", "health_band"]], on="company_id", how="left")
    result = result.merge(latest_opm, on="company_id", how="left")
    result = result.merge(latest_icr, on="company_id", how="left")
    result = result.merge(latest_cap, on="company_id", how="left")

    return result

def apply_conditional_formatting(worksheet, df, workbook):
    green_format = workbook.add_format({"bg_color": "#c6efce", "font_color": "#276221"})
    red_format = workbook.add_format({"bg_color": "#ffc7ce", "font_color": "#9c0006"})
    header_format = workbook.add_format({
        "bold": True, "bg_color": "#1f3b57", "font_color": "white",
        "border": 1, "align": "center"
    })

    for col_num, col_name in enumerate(df.columns):
        worksheet.write(0, col_num, col_name, header_format)

    roe_col = df.columns.get_loc("roe_pct")
    for row_num in range(1, len(df) + 1):
        val = df["roe_pct"].iloc[row_num - 1]
        if pd.notna(val):
            fmt = green_format if val >= 15 else red_format
            worksheet.write(row_num, roe_col, val, fmt)

    health_col = df.columns.get_loc("health_score")
    for row_num in range(1, len(df) + 1):
        val = df["health_score"].iloc[row_num - 1]
        if pd.notna(val):
            fmt = green_format if val >= 65 else (red_format if val < 50 else None)
            if fmt:
                worksheet.write(row_num, health_col, val, fmt)

if __name__ == "__main__":
    import pathlib
    pathlib.Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

    print("Building full universe dataset...")
    data = build_full_universe()

    display_cols = [
        "company_id", "company_name", "broad_sector",
        "roe_pct", "opm_pct", "net_profit_margin_pct",
        "debt_to_equity", "interest_coverage", "free_cash_flow_cr",
        "pe_ratio", "pb_ratio", "dividend_yield_pct",
        "health_score", "health_band", "capital_allocation_pattern"
    ]
    available_cols = [c for c in display_cols if c in data.columns]
    export_data = data[available_cols].sort_values("health_score", ascending=False, na_position="last")

    print("Writing Excel file with conditional formatting...")
    writer = pd.ExcelWriter(OUTPUT_PATH, engine="xlsxwriter")
    export_data.to_excel(writer, sheet_name="Full Universe", index=False)

    workbook = writer.book
    worksheet = writer.sheets["Full Universe"]
    apply_conditional_formatting(worksheet, export_data, workbook)

    worksheet.set_column(0, 0, 14)
    worksheet.set_column(1, 1, 35)
    worksheet.set_column(2, 2, 22)
    worksheet.set_column(3, len(available_cols) - 1, 16)

    writer.close()
    print("Done. Excel file saved to:", OUTPUT_PATH)
    print("Rows:", len(export_data), "| Columns:", len(available_cols))
