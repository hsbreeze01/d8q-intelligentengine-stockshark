"""Pipeline API 单元测试 — mock 服务层和 DB"""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from stockshark.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# GET /api/v1/pipeline/kline
# ---------------------------------------------------------------------------


class TestKlineEndpoint:

    @patch("stockshark.api.routes.pipeline.tables")
    def test_kline_missing_stock_code(self, mock_tables, client):
        resp = client.get("/api/v1/pipeline/kline")
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert data["success"] is False
        assert "stock_code" in data["error"]

    @patch("stockshark.api.routes.pipeline.tables")
    def test_kline_returns_data(self, mock_tables, client):
        mock_tables.query_kline_range.return_value = [
            {
                "trade_date": date(2025, 1, 13),
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.3,
                "volume": 100000,
            },
        ]
        resp = client.get("/api/v1/pipeline/kline?stock_code=600000&limit=60")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["trade_date"] == "2025-01-13"

    @patch("stockshark.api.routes.pipeline.tables")
    def test_kline_no_data_returns_empty(self, mock_tables, client):
        mock_tables.query_kline_range.return_value = []
        resp = client.get("/api/v1/pipeline/kline?stock_code=688999")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["data"] == []


# ---------------------------------------------------------------------------
# GET /api/v1/pipeline/indicators
# ---------------------------------------------------------------------------


class TestIndicatorsEndpoint:

    @patch("stockshark.api.routes.pipeline.tables")
    def test_indicators_missing_stock_code(self, mock_tables, client):
        resp = client.get("/api/v1/pipeline/indicators")
        assert resp.status_code == 400

    @patch("stockshark.api.routes.pipeline.tables")
    def test_indicators_returns_data(self, mock_tables, client):
        mock_tables.query_indicators_range.return_value = [
            {
                "trade_date": date(2025, 1, 13),
                "ma5": 10.1,
                "ma10": None,
                "ma20": None,
                "ma60": None,
                "macd_dif": 0.1,
                "macd_dea": 0.05,
                "macd_bar": 0.1,
                "kdj_k": 50.0,
                "kdj_d": 48.0,
                "kdj_j": 54.0,
                "rsi6": 55.0,
                "rsi12": None,
                "rsi24": None,
                "boll_upper": None,
                "boll_middle": None,
                "boll_lower": None,
            },
        ]
        resp = client.get(
            "/api/v1/pipeline/indicators?stock_code=600000&limit=60"
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["success"] is True
        assert data["data"][0]["ma5"] == 10.1


# ---------------------------------------------------------------------------
# GET /api/v1/pipeline/stock-data
# ---------------------------------------------------------------------------


class TestStockDataEndpoint:

    @patch("stockshark.api.routes.pipeline.tables")
    def test_stock_data_missing_stock_code(self, mock_tables, client):
        resp = client.get("/api/v1/pipeline/stock-data")
        assert resp.status_code == 400

    @patch("stockshark.api.routes.pipeline.tables")
    def test_stock_data_merges_kline_and_indicators(self, mock_tables, client):
        mock_tables.query_kline_range.return_value = [
            {
                "trade_date": date(2025, 1, 13),
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.3,
                "volume": 100000,
            },
        ]
        mock_tables.query_indicators_range.return_value = [
            {
                "trade_date": date(2025, 1, 13),
                "ma5": 10.1,
                "ma10": None,
                "ma20": None,
                "ma60": None,
                "macd_dif": None,
                "macd_dea": None,
                "macd_bar": None,
                "kdj_k": None,
                "kdj_d": None,
                "kdj_j": None,
                "rsi6": None,
                "rsi12": None,
                "rsi24": None,
                "boll_upper": None,
                "boll_middle": None,
                "boll_lower": None,
            },
        ]
        resp = client.get(
            "/api/v1/pipeline/stock-data?stock_code=600000&limit=60"
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        item = data["data"][0]
        assert item["open"] == 10.0
        assert item["ma5"] == 10.1


# ---------------------------------------------------------------------------
# POST /api/v1/pipeline/collect
# ---------------------------------------------------------------------------


class TestTriggerCollect:

    @patch("stockshark.api.routes.pipeline.pipeline_daemon")
    def test_trigger_collect_success(self, mock_daemon, client):
        mock_daemon.trigger_collect.return_value = {
            "total": 5,
            "success": 4,
            "failed": 1,
            "failed_codes": ["603009"],
        }
        resp = client.post("/api/v1/pipeline/collect")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["success"] is True
        assert data["data"]["success"] == 4

    @patch("stockshark.api.routes.pipeline.pipeline_daemon")
    def test_trigger_collect_error(self, mock_daemon, client):
        mock_daemon.trigger_collect.return_value = {"error": "db error"}
        resp = client.post("/api/v1/pipeline/collect")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/v1/pipeline/run-indicators
# ---------------------------------------------------------------------------


class TestTriggerIndicators:

    @patch("stockshark.api.routes.pipeline.pipeline_daemon")
    def test_trigger_indicators_success(self, mock_daemon, client):
        mock_daemon.trigger_indicators.return_value = {
            "total": 5,
            "success": 5,
            "failed": 0,
            "failed_codes": [],
        }
        resp = client.post("/api/v1/pipeline/run-indicators")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["success"] is True


# ---------------------------------------------------------------------------
# GET /api/v1/pipeline/status
# ---------------------------------------------------------------------------


class TestStatusEndpoint:

    @patch("stockshark.api.routes.pipeline.pipeline_daemon")
    def test_status_returns_info(self, mock_daemon, client):
        mock_daemon.status.return_value = {
            "daemon_enabled": False,
            "scheduler_running": False,
            "last_collect_time": None,
            "last_indicator_time": None,
            "tracked_stock_count": 10,
        }
        resp = client.get("/api/v1/pipeline/status")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["success"] is True
        assert data["data"]["tracked_stock_count"] == 10
