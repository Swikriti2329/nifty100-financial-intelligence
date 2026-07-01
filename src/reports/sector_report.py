import sys
import pathlib
import sqlite3
import pandas as pd

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src" / "analytics"))

from ratios import load_table
from screener import get_latest_ratios, add_valuation_data
from health_score import compute_health_score
from growth_ratios import compute_roce, compute_revenue_cagr_5yr
from more_ratios import compute_opm

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

DB_PATH = str(PROJECT_ROOT / "data" / "processed" / "nifty100.db")
OUTPUT_DIR = PROJECT_ROOT / "reports" / "sector"

def fmt(value, suffix=""):
    if value is None or pd.isna(value):
        return "N/A"
    return "{:.2f}{}".format(value, suffix)

def load_sector_data():
    conn = sqlite3.connect(DB_PATH)
    pl = load_table("profitandloss", conn)
    bs = load_table("balancesheet", conn)
    sectors = load_table("sectors", conn)
    conn.close()

    latest = get_latest_ratios()
    latest = add_valuation_data(latest)
    scores = compute_health_score(latest)
    opm = compute_opm(pl)
    latest_opm = opm.sort_values("year").groupby("company_id").last().reset_index()[["company_id", "opm_pct"]]

    latest = latest.merge(scores[["company_id", "health_score", "health_band"]], on="company_id", how="left")
    latest = latest.merge(latest_opm, on="company_id", how="left")

    return latest

def generate_sector_report(sector_name, companies_df, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sector_name.replace("/", "_").replace(" ", "_")
    file_path = output_dir / "{}_sector_report.pdf".format(safe_name)

    doc = SimpleDocTemplate(str(file_path), pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm,
                             leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=18, spaceAfter=6)
    sub_style = ParagraphStyle("SubStyle", parent=styles["Normal"], fontSize=10, textColor=colors.grey)

    story = []
    story.append(Paragraph("{} Sector Report".format(sector_name), title_style))
    story.append(Paragraph(
        "{} companies | Nifty 100 Financial Intelligence Platform".format(len(companies_df)),
        sub_style
    ))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Sector Median KPIs", styles["Heading2"]))
    medians = companies_df[["roe_pct", "net_profit_margin_pct", "opm_pct", "free_cash_flow_cr"]].median()
    median_data = [
        ["Metric", "Sector Median"],
        ["Return on Equity (ROE)", fmt(medians["roe_pct"], "%")],
        ["Net Profit Margin", fmt(medians["net_profit_margin_pct"], "%")],
        ["Operating Profit Margin", fmt(medians["opm_pct"], "%")],
        ["Free Cash Flow (Cr)", fmt(medians["free_cash_flow_cr"])],
    ]
    median_table = Table(median_data, colWidths=[10*cm, 6*cm])
    median_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b57")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(median_table)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Company Rankings by ROE", styles["Heading2"]))
    ranked = companies_df.sort_values("roe_pct", ascending=False)
    company_data = [["Rank", "Company", "ROE", "NPM", "Health Score", "Health Band"]]
    for i, (_, row) in enumerate(ranked.iterrows(), 1):
        company_data.append([
            str(i),
            str(row["company_name"])[:35],
            fmt(row["roe_pct"], "%"),
            fmt(row["net_profit_margin_pct"], "%"),
            fmt(row["health_score"]),
            str(row["health_band"]),
        ])

    company_table = Table(company_data, colWidths=[1.2*cm, 6.5*cm, 2*cm, 2*cm, 2.5*cm, 3*cm])
    company_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b57")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(company_table)

    doc.build(story)
    return file_path

if __name__ == "__main__":
    data = load_sector_data()

    sectors = data["broad_sector"].dropna().unique()
    print("Generating sector reports for {} sectors...".format(len(sectors)))

    for sector in sorted(sectors):
        sector_companies = data[data["broad_sector"] == sector]
        path = generate_sector_report(sector, sector_companies, OUTPUT_DIR)
        print("Generated: {}".format(path.name))

    print()
    print("Done. {} sector reports generated.".format(len(sectors)))
