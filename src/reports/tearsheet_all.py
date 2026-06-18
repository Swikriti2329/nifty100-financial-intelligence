import sys
import os
import pathlib
import sqlite3
import pandas as pd

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src" / "analytics"))

from ratios import load_table
from screener import get_latest_ratios, add_valuation_data
from health_score import compute_health_score
from growth_ratios import compute_roce, compute_revenue_cagr_5yr

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

DB_PATH = str(PROJECT_ROOT / "data" / "processed" / "nifty100.db")
OUTPUT_DIR = PROJECT_ROOT / "reports" / "tearsheets"

def fmt(value, suffix=""):
    if value is None or pd.isna(value):
        return "N/A"
    return "{:.2f}{}".format(value, suffix)

def load_full_dataset():
    conn = sqlite3.connect(DB_PATH)
    pl = load_table("profitandloss", conn)
    bs = load_table("balancesheet", conn)
    sectors = load_table("sectors", conn)
    conn.close()

    latest = get_latest_ratios()
    latest = add_valuation_data(latest)
    scores = compute_health_score(latest)
    roce = compute_roce(pl, bs, sectors)
    cagr = compute_revenue_cagr_5yr(pl)

    latest = latest.merge(scores[["company_id", "health_score", "health_band"]], on="company_id", how="left")
    latest_roce = roce.dropna(subset=["roce_pct"]).sort_values("year").groupby("company_id").last().reset_index()
    latest = latest.merge(latest_roce[["company_id", "roce_pct"]], on="company_id", how="left")
    latest = latest.merge(cagr, on="company_id", how="left")

    return latest

def generate_tearsheet(row, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / "{}_tearsheet.pdf".format(row["company_id"])

    doc = SimpleDocTemplate(str(file_path), pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm,
                             leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=20, spaceAfter=6)
    sub_style = ParagraphStyle("SubStyle", parent=styles["Normal"], fontSize=11, textColor=colors.grey)

    story = []
    story.append(Paragraph(str(row["company_name"]), title_style))
    story.append(Paragraph(
        "Ticker: {}  |  Sector: {}  |  Health Band: {}".format(
            row["company_id"], row["broad_sector"], row["health_band"]
        ), sub_style
    ))
    story.append(Spacer(1, 0.6*cm))

    score_text = fmt(row["health_score"])
    story.append(Paragraph("Financial Health Score: {} / 100".format(score_text), styles["Heading2"]))
    story.append(Spacer(1, 0.4*cm))

    table_data = [
        ["Metric", "Value"],
        ["Return on Equity (ROE)", fmt(row["roe_pct"], "%")],
        ["Return on Capital Employed (ROCE)", fmt(row["roce_pct"], "%")],
        ["Net Profit Margin", fmt(row["net_profit_margin_pct"], "%")],
        ["Debt-to-Equity", fmt(row["debt_to_equity"])],
        ["Free Cash Flow (Cr)", fmt(row["free_cash_flow_cr"])],
        ["5-Year Revenue CAGR", fmt(row["revenue_cagr_5yr_pct"], "%")],
        ["P/E Ratio", fmt(row["pe_ratio"])],
        ["Dividend Yield", fmt(row["dividend_yield_pct"], "%")],
    ]

    table = Table(table_data, colWidths=[10*cm, 6*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b57")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)

    doc.build(story)
    return file_path

if __name__ == "__main__":
    data = load_full_dataset()

    sample_companies = data["company_id"].tolist()  # all 92 companies
    generated = []

    for ticker in sample_companies:
        matches = data[data["company_id"] == ticker]
        if len(matches) == 0:
            print("Skipping {} - not found".format(ticker))
            continue
        row = matches.iloc[0]
        path = generate_tearsheet(row, OUTPUT_DIR)
        generated.append(path)
        print("Generated:", path)

    print()
    print("Done. {} tearsheets generated in {}".format(len(generated), OUTPUT_DIR))
