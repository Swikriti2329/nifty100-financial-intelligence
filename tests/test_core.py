import sys
import os
import pytest
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "etl"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "analytics"))

from normalize import normalize_ticker, normalize_year
from ratios import compute_net_profit_margin, compute_roe, compute_debt_to_equity, compute_free_cash_flow

class TestNormalizeTicker:
    def test_uppercase(self):
        assert normalize_ticker("tcs") == "TCS"

    def test_strips_whitespace(self):
        assert normalize_ticker("  TCS  ") == "TCS"

    def test_strips_newline(self):
        assert normalize_ticker("TCS\n") == "TCS"

    def test_hyphen_preserved(self):
        assert normalize_ticker("bajaj-auto") == "BAJAJ-AUTO"

    def test_ampersand_preserved(self):
        assert normalize_ticker("m&m") == "M&M"

class TestNormalizeYear:
    def test_mar_23(self):
        assert normalize_year("Mar-23") == "2023-03"

    def test_fy24(self):
        assert normalize_year("FY24") == "2024-03"

    def test_plain_year(self):
        assert normalize_year("2023") == "2023-03"

    def test_dec_22(self):
        assert normalize_year("Dec-22") == "2022-12"

    def test_already_normalized(self):
        assert normalize_year("2023-03") == "2023-03"

    def test_ttm_returns_ttm(self):
        assert normalize_year("TTM") == "TTM"

    def test_garbage_returns_parse_error(self):
        assert normalize_year("garbage") == "PARSE_ERROR"

class TestNetProfitMargin:
    def make_pl(self, sales, net_profit):
        return pd.DataFrame([{"company_id": "TEST", "year": "2023-03",
                               "sales": sales, "net_profit": net_profit}])

    def test_normal_case(self):
        pl = self.make_pl(100, 10)
        result = compute_net_profit_margin(pl)
        assert abs(result["net_profit_margin_pct"].iloc[0] - 10.0) < 0.01

    def test_zero_sales_returns_none(self):
        pl = self.make_pl(0, 10)
        result = compute_net_profit_margin(pl)
        assert pd.isna(result["net_profit_margin_pct"].iloc[0])

    def test_extreme_ratio_returns_none(self):
        pl = self.make_pl(1, 500)
        result = compute_net_profit_margin(pl)
        assert pd.isna(result["net_profit_margin_pct"].iloc[0])

class TestROE:
    def make_data(self, net_profit, equity, reserves):
        pl = pd.DataFrame([{"company_id": "TEST", "year": "2023-03", "net_profit": net_profit}])
        bs = pd.DataFrame([{"company_id": "TEST", "year": "2023-03",
                             "equity_capital": equity, "reserves": reserves}])
        return pl, bs

    def test_normal_case(self):
        pl, bs = self.make_data(20, 50, 50)
        result = compute_roe(pl, bs)
        assert abs(result["roe_pct"].iloc[0] - 20.0) < 0.01

    def test_negative_equity_returns_none(self):
        pl, bs = self.make_data(20, 10, -50)
        result = compute_roe(pl, bs)
        assert pd.isna(result["roe_pct"].iloc[0])

class TestDebtToEquity:
    def make_bs(self, borrowings, equity, reserves, sector="IT"):
        bs = pd.DataFrame([{"company_id": "TEST", "year": "2023-03",
                             "borrowings": borrowings, "equity_capital": equity,
                             "reserves": reserves}])
        sectors = pd.DataFrame([{"company_id": "TEST", "broad_sector": sector}])
        return bs, sectors

    def test_debt_free(self):
        bs, sectors = self.make_bs(0, 100, 100)
        result = compute_debt_to_equity(bs, sectors)
        assert result["debt_to_equity"].iloc[0] == 0.0

    def test_normal_case(self):
        bs, sectors = self.make_bs(50, 50, 50)
        result = compute_debt_to_equity(bs, sectors)
        assert abs(result["debt_to_equity"].iloc[0] - 0.5) < 0.01

    def test_financials_excluded(self):
        bs, sectors = self.make_bs(1000, 50, 50, sector="Financials")
        result = compute_debt_to_equity(bs, sectors)
        assert pd.isna(result["debt_to_equity"].iloc[0])

class TestFreeCashFlow:
    def test_positive_fcf(self):
        cf = pd.DataFrame([{"company_id": "TEST", "year": "2023-03",
                             "operating_activity": 100, "investing_activity": -30}])
        result = compute_free_cash_flow(cf)
        assert result["free_cash_flow_cr"].iloc[0] == 70

    def test_negative_fcf_allowed(self):
        cf = pd.DataFrame([{"company_id": "TEST", "year": "2023-03",
                             "operating_activity": 50, "investing_activity": -200}])
        result = compute_free_cash_flow(cf)
        assert result["free_cash_flow_cr"].iloc[0] == -150
