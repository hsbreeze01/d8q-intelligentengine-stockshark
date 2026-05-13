"""KLineCollector 单元测试 — mock fetcher 和 DB"""

import pytest
import pandas as pd
from datetime import date, datetime
from unittest.mock import patch, MagicMock

from stockshark.pipeline.kline_collector import KLineCollector


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------


def _sample_df():
    """模拟 fetcher 返回的 DataFrame"""
    return pd.DataFrame({
        "date": pd.to_datetime(["2025-01-13", "2025-01-14"]),
        "open": [10.0, 10.5],
        "high": [10.5, 11.0],
        "low": [9.8, 10.2],
        "close": [10.3, 10.8],
        "volume": [100000, 120000],
    })


def _mock_conn(fetchall_result=None, fetchone_result=None):
    cursor = MagicMock()
    cursor.fetchall.return_value = fetchall_result or []
    cursor.fetchone.return_value = fetchone_result
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


# ---------------------------------------------------------------------------
# collect_one
# ---------------------------------------------------------------------------


class TestCollectOne:

    @patch("stockshark.pipeline.kline_collector.tables")
    @patch("stockshark.pipeline.kline_collector.KLineCollector._fetch_with_fallback")
    @patch("stockshark.pipeline.kline_collector.tables.query_latest_date", return_value=None)
    def test_first_time_collect(self, mock_latest, mock_fetch, mock_tables):
        """首次采集：无历史数据 → 取近 N 天"""
        mock_fetch.return_value = _sample_df()
        mock_tables.upsert_kline_rows = MagicMock()

        collector = KLineCollector()
        result = collector.collect_one("600000")

        assert result["success"] is True
        assert result["rows"] == 2
        mock_tables.upsert_kline_rows.assert_called_once()

    @patch("stockshark.pipeline.kline_collector.tables")
    @patch("stockshark.pipeline.kline_collector.KLineCollector._fetch_with_fallback")
    @patch(
        "stockshark.pipeline.kline_collector.tables.query_latest_date",
        return_value=date(2025, 1, 10),
    )
    def test_incremental_collect(self, mock_latest, mock_fetch, mock_tables):
        """增量采集：有历史数据 → 从最新日期的下一天开始"""
        mock_fetch.return_value = _sample_df()
        mock_tables.upsert_kline_rows = MagicMock()

        collector = KLineCollector()
        result = collector.collect_one("600000")

        assert result["success"] is True
        assert result["rows"] == 2

    @patch(
        "stockshark.pipeline.kline_collector.tables.query_latest_date",
        return_value=None,
    )
    @patch(
        "stockshark.pipeline.kline_collector.KLineCollector._fetch_with_fallback",
        return_value=pd.DataFrame(),
    )
    @patch("stockshark.pipeline.kline_collector.tables")
    def test_collect_empty_data(self, mock_tables, mock_fetch, mock_latest):
        """采集返回空数据"""
        collector = KLineCollector()
        result = collector.collect_one("600000")
        assert result["success"] is True
        assert result["rows"] == 0


# ---------------------------------------------------------------------------
# 降级逻辑
# ---------------------------------------------------------------------------


class TestFallback:

    @patch(
        "stockshark.pipeline.kline_collector.AkshareEastmoneyFetcher.fetch",
        side_effect=Exception("eastmoney error"),
    )
    @patch(
        "stockshark.pipeline.kline_collector.AkshareSinaFetcher.fetch",
        return_value=_sample_df(),
    )
    def test_fallback_to_sina(self, mock_sina, mock_em):
        """东财失败 → 降级到 Sina"""
        collector = KLineCollector()
        result = collector._fetch_with_fallback("600000", "20250101", "20250114")
        assert result is not None
        assert len(result) == 2
        mock_sina.assert_called_once()

    @patch(
        "stockshark.pipeline.kline_collector.AkshareEastmoneyFetcher.fetch",
        return_value=_sample_df(),
    )
    @patch(
        "stockshark.pipeline.kline_collector.AkshareSinaFetcher.fetch",
    )
    def test_no_fallback_when_em_succeeds(self, mock_sina, mock_em):
        """东财成功 → 不调用 Sina"""
        collector = KLineCollector()
        result = collector._fetch_with_fallback("600000", "20250101", "20250114")
        assert result is not None
        mock_sina.assert_not_called()

    @patch(
        "stockshark.pipeline.kline_collector.AkshareEastmoneyFetcher.fetch",
        side_effect=Exception("em error"),
    )
    @patch(
        "stockshark.pipeline.kline_collector.AkshareSinaFetcher.fetch",
        side_effect=Exception("sina error"),
    )
    def test_all_sources_fail(self, mock_sina, mock_em):
        """所有数据源都失败 → 抛出异常"""
        collector = KLineCollector()
        with pytest.raises(RuntimeError, match="东财失败"):
            collector._fetch_with_fallback("600000", "20250101", "20250114")


# ---------------------------------------------------------------------------
# collect_all（批量采集）
# ---------------------------------------------------------------------------


class TestCollectAll:

    @patch("stockshark.pipeline.kline_collector.tables")
    @patch("stockshark.pipeline.kline_collector.get_mysql_connection")
    @patch.object(KLineCollector, "collect_one")
    def test_batch_summary(self, mock_one, mock_conn, mock_tables):
        """批量采集返回汇总"""
        codes = [
            {"stock_code": "600000"},
            {"stock_code": "000001"},
            {"stock_code": "603009"},
        ]
        conn, cursor = _mock_conn(fetchall_result=codes)
        mock_conn.return_value = conn

        mock_one.side_effect = [
            {"stock_code": "600000", "success": True, "rows": 5, "error": None},
            {"stock_code": "000001", "success": True, "rows": 3, "error": None},
            {"stock_code": "603009", "success": False, "rows": 0, "error": "fail"},
        ]

        collector = KLineCollector()
        result = collector.collect_all()

        assert result["total"] == 3
        assert result["success"] == 2
        assert result["failed"] == 1
        assert result["failed_codes"] == ["603009"]
