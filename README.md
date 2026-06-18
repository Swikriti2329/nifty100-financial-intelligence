# Nifty 100 Financial Intelligence Platform

A financial analytics platform analyzing 92 Nifty 100 companies, built from raw financial statement data through to an interactive dashboard.

## What this project does

- Cleans and loads 12 raw datasets (P&L, balance sheet, cash flow, sectors, market cap, peer groups, and more) into a single SQLite database
- Computes 6 financial ratios from scratch: Net Profit Margin, ROE, ROCE, Debt-to-Equity, Free Cash Flow, and 5-Year Revenue CAGR
- Runs 6 preset investment screeners
- Calculates a composite Financial Health Score (0-100) for every company
- Provides Sector Analytics and Peer Group comparison
- Generates PDF tearsheet reports per company
- Includes a 3-page interactive Streamlit dashboard

## Setup

1. Clone this repository
2. Create a virtual environment: python3 -m venv .venv
3. Activate it: source .venv/bin/activate
4. Install dependencies: pip install pandas numpy openpyxl streamlit plotly matplotlib reportlab pytest

## How to run

Build the database (run this first, once):

cd src/etl
python3 build_database.py

Launch the dashboard:

cd src/dashboard
streamlit run app.py

Generate PDF reports:

cd src/reports
python3 tearsheet.py

## Data quality notes

During development, several real data quality issues were identified and handled deliberately rather than ignored:

- Non-standard year labels (TTM, partial-year periods like "Mar 2016 9m") were parsed and normalized; one genuinely unparseable value was logged to reports/parse_failures.csv rather than guessed at.
- 8 companies referenced in documents.xlsx fall outside the project's 92-company universe and were excluded, logged to reports/documents_out_of_scope.csv.
- Financial sector companies (banks, NBFCs, insurers) are excluded from Debt-to-Equity, ROCE, and the Financial Health Score, since their "borrowings" field represents customer deposits or policyholder liabilities rather than conventional debt.
- Extreme ratio outliers (holding companies with minimal sales, companies with near-zero equity bases) are capped and flagged rather than displayed as misleading values. Cases were individually investigated; some (Reliance's negative FCF during its Jio and retail expansion, Adani Power's high D/E during sector-wide financial stress) were confirmed as real and meaningful rather than errors.

## Project structure

data/raw/          original 7 core Excel files, read-only
data/supporting/   5 supplementary Excel files
data/processed/    generated SQLite database
src/etl/           data loading and cleaning
src/analytics/     ratios, screener, health score, sector and peer analysis
src/dashboard/     Streamlit app
src/reports/       PDF report generator
reports/           data quality logs and generated PDF tearsheets

## Known limitations and future work

- Only 6 of the spec's 50+ KPIs are implemented; these 6 cover the most decision-relevant metrics across profitability, leverage, cash quality, and growth.
- Turnaround Watch screener uses a simplified proxy (low NPM plus positive FCF) rather than full multi-year trend detection.
- NLP-based pros/cons generation, statistical clustering, and a REST API layer described in the original specification were not built in this version, in favor of depth and correctness on the core analytics.
