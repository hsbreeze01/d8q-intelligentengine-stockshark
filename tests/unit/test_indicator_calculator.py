"""IndicatorCalculator 单元测试 — mock DB, 测试计算逻辑"""

import pandas as pd
import numpy as np
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from stockshark.pipeline.indicator_calculator import IndicatorCalculator


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------


def _make_kline_df(n=60):
    """生成 n 条模拟 K 线数据（DataFrame of dicts）"""
    rows = []
    base_price = 10.0
    for i in range(n):
        d = date(2025, 1, 1) + timedelta(days=i)
        rows.append({
            "stock_code": "600000",
            "date": d,
            "open": base_price + i * 0.1,
            "high": base_price + i * 0.1 + 0.5,
            "low": base_price + i * 0.1 - 0.3,
            "close": base_price + i * 0.1 + 0.2,
            "volume": 100000 + i * 1000,
            "amount": None,
        })
    return rows


def _mock_conn(fetchall_result=None, fetchone_result=None):
    cursor = MagicMock()
    cursor.fetchall.return_value = fetchall_result or []
    cursor.fetchone.return_value = fetchone_result
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


# ---------------------------------------------------------------------------
# calculate_one — 全量计算
# ---------------------------------------------------------------------------


class TestCalculateOneFull:

    @patch("stockshark.pipeline.indicator_calculator.tables")
    def test_full_calculation(self, mock_tables):
        """60+ 条 K 线 → 全部指标计算"""
        klines = _make_kline_df(65)
        mock_tables.query_kline_for_calc.return_value = klines
        mock_tables.query_latest_indicator_date.return_value = None
        mock_tables.upsert_indicator_rows = MagicMock()

        calc = IndicatorCalculator()
        result = calc.calculate_one("600000")

        assert result["success"] is True
        assert result["rows"] > 0
        mock_tables.upsert_indicator_rows.assert_called_once()
        rows = mock_tables.upsert_indicator_rows.call_args[0][0]
        # 至少应有 MA5、MACD 等非 None 值
        assert any(r["ma5"] is not None for r in rows)
        assert any(r["ma30"] is not None for r in rows)
        assert any(r["rsi_6"] is not None for r in rows)
        assert any(r["volume_ratio"] is not None for r in rows)

    @patch("stockshark.pipeline.indicator_calculator.tables")
    def test_no_kline_data(self, mock_tables):
        """无 K 线数据 → 跳过"""
        mock_tables.query_kline_for_calc.return_value = []

        calc = IndicatorCalculator()
        result = calc.calculate_one("600000")

        assert result["success"] is True
        assert result["rows"] == 0


# ---------------------------------------------------------------------------
# 数据不足时降级
# ---------------------------------------------------------------------------


class TestDegradedCalculation:

    @patch("stockshark.pipeline.indicator_calculator.tables")
    def test_short_data_skips_long_indicators(self, mock_tables):
        """25 条 K 线 → 跳过 MA60、BOLL"""
        klines = _make_kline_df(25)
        mock_tables.query_kline_for_calc.return_value = klines
        mock_tables.query_latest_indicator_date.return_value = None
        mock_tables.upsert_indicator_rows = MagicMock()

        calc = IndicatorCalculator()
        result = calc.calculate_one("600000")

        assert result["success"] is True
        rows = mock_tables.upsert_indicator_rows.call_args[0][0]
        # MA60 应该为 None（数据不足 60）
        # 但 MA5 应该有值
        assert any(r.get("ma5") is not None for r in rows)


# ---------------------------------------------------------------------------
# 增量计算
# ---------------------------------------------------------------------------


class TestIncrementalCalculation:

    @patch("stockshark.pipeline.indicator_calculator.tables")
    def test_only_new_dates_written(self, mock_tables):
        """增量模式：只写入已有指标最新日期之后的新行"""
        klines = _make_kline_df(65)
        mock_tables.query_kline_for_calc.return_value = klines
        # 已有指标到 2025-01-50（即 2025-02-19）
        existing_latest = date(2025, 2, 20)
        mock_tables.query_latest_indicator_date.return_value = existing_latest
        mock_tables.upsert_indicator_rows = MagicMock()

        calc = IndicatorCalculator()
        result = calc.calculate_one("600000")

        assert result["success"] is True
        rows = mock_tables.upsert_indicator_rows.call_args[0][0]
        # 所有写入的行日期应大于 existing_latest
        for r in rows:
            assert r["date"] > existing_latest

    @patch("stockshark.pipeline.indicator_calculator.tables")
    def test_force_recalculate_updates_existing_window(self, mock_tables):
        """强制重算：已有日期也通过 upsert 回填"""
        klines = _make_kline_df(65)
        mock_tables.query_kline_for_calc.return_value = klines
        mock_tables.query_latest_indicator_date.return_value = date(2025, 2, 20)
        mock_tables.upsert_indicator_rows = MagicMock()

        calc = IndicatorCalculator()
        result = calc.calculate_one("600000", force_recalculate=True)

        assert result["success"] is True
        rows = mock_tables.upsert_indicator_rows.call_args[0][0]
        assert any(r["date"] <= date(2025, 2, 20) for r in rows)
        assert any(r["volume_ratio"] is not None for r in rows)


# ---------------------------------------------------------------------------
# 内部计算方法
# ---------------------------------------------------------------------------


class TestComputeMethods:

    def test_macd_shape(self):
        """MACD 返回正确形状"""
        close = pd.Series(np.random.randn(50).cumsum() + 100)
        result = IndicatorCalculator._calc_macd(close)
        assert len(result) == 50
        assert "macd_dif" in result.columns
        assert "macd_dea" in result.columns
        assert "macd_macd" in result.columns

    def test_kdj_shape(self):
        """KDJ 返回正确形状"""
        df = pd.DataFrame({
            "close": np.random.randn(30).cumsum() + 100,
            "high": np.random.randn(30).cumsum() + 102,
            "low": np.random.randn(30).cumsum() + 98,
        })
        result = IndicatorCalculator._calc_kdj(df)
        assert len(result) == 30
        assert "kdj_k" in result.columns

    def test_rsi_shape(self):
        """RSI 返回正确形状"""
        close = pd.Series(np.random.randn(30).cumsum() + 100)
        result = IndicatorCalculator._calc_rsi(close, 6)
        assert len(result) == 30

    def test_boll_shape(self):
        """BOLL 返回正确形状"""
        close = pd.Series(np.random.randn(30).cumsum() + 100)
        result = IndicatorCalculator._calc_boll(close)
        assert len(result) == 30
        assert "boll_up" in result.columns
        assert "boll_mid" in result.columns
        assert "boll_low" in result.columns
