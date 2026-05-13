"""KLineFetcher 单元测试 — mock akshare 调用"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from stockshark.pipeline.kline_fetcher import (
    AkshareEastmoneyFetcher,
    AkshareSinaFetcher,
    _to_ak_em_symbol,
)


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------


def _em_df():
    """模拟东财返回"""
    return pd.DataFrame({
        "日期": ["2025-01-13", "2025-01-14"],
        "开盘": [10.0, 10.5],
        "最高": [10.5, 11.0],
        "最低": [9.8, 10.2],
        "收盘": [10.3, 10.8],
        "成交量": [100000, 120000],
    })


def _sina_df():
    """模拟 Sina 返回"""
    return pd.DataFrame({
        "date": ["2025-01-13", "2025-01-14"],
        "open": [10.0, 10.5],
        "high": [10.5, 11.0],
        "low": [9.8, 10.2],
        "close": [10.3, 10.8],
        "volume": [100000, 120000],
    })


# ---------------------------------------------------------------------------
# AkshareEastmoneyFetcher
# ---------------------------------------------------------------------------


class TestAkshareEastmoneyFetcher:

    @patch("stockshark.pipeline.kline_fetcher._normalize_em")
    @patch("akshare.stock_zh_a_hist")
    def test_fetch_returns_normalized_df(self, mock_hist, mock_norm):
        mock_hist.return_value = _em_df()
        mock_norm.return_value = pd.DataFrame({"date": [1], "open": [2]})

        fetcher = AkshareEastmoneyFetcher()
        result = fetcher.fetch("600000", start_date="20250101", end_date="20250114")
        assert not result.empty
        mock_hist.assert_called_once()

    @patch("akshare.stock_zh_a_hist", return_value=pd.DataFrame())
    def test_fetch_empty_returns_empty(self, mock_hist):
        fetcher = AkshareEastmoneyFetcher()
        result = fetcher.fetch("600000")
        assert result.empty

    @patch("akshare.stock_zh_a_hist", side_effect=Exception("timeout"))
    def test_fetch_exception_propagates(self, mock_hist):
        fetcher = AkshareEastmoneyFetcher()
        with pytest.raises(Exception, match="timeout"):
            fetcher.fetch("600000")


# ---------------------------------------------------------------------------
# AkshareSinaFetcher
# ---------------------------------------------------------------------------


class TestAkshareSinaFetcher:

    @patch("stockshark.pipeline.kline_fetcher._normalize_sina")
    @patch("akshare.stock_zh_a_daily")
    def test_fetch_returns_normalized_df(self, mock_daily, mock_norm):
        mock_daily.return_value = _sina_df()
        mock_norm.return_value = pd.DataFrame({"date": [1], "open": [2]})

        fetcher = AkshareSinaFetcher()
        result = fetcher.fetch("600000", start_date="20250101")
        assert not result.empty

    @patch("akshare.stock_zh_a_daily", return_value=pd.DataFrame())
    def test_fetch_empty_returns_empty(self, mock_daily):
        fetcher = AkshareSinaFetcher()
        result = fetcher.fetch("600000")
        assert result.empty


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


class TestSymbolConversion:

    def test_sh_prefix(self):
        assert _to_ak_em_symbol("600000") == "sh600000"

    def test_sz_prefix(self):
        assert _to_ak_em_symbol("000001") == "sz000001"

    def test_already_prefixed(self):
        assert _to_ak_em_symbol("sh600000") == "sh600000"

    def test_9_prefix(self):
        assert _to_ak_em_symbol("900001") == "sh900001"
