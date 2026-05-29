"""Pipeline API 路由 — K线/指标查询 + 手动触发 + 状态"""

from flask import Blueprint, request, jsonify

from stockshark.pipeline import tables
from stockshark.pipeline.daemon import pipeline_daemon

pipeline_bp = Blueprint("pipeline", __name__)


# ---------------------------------------------------------------------------
# K 线数据查询
# ---------------------------------------------------------------------------


@pipeline_bp.route("/kline", methods=["GET"])
def get_kline():
    """
    GET /api/v1/pipeline/kline?stock_code=600000&limit=60
    """
    stock_code = request.args.get("stock_code")
    if not stock_code:
        return jsonify({"success": False, "error": "缺少必要参数: stock_code"}), 400

    limit = request.args.get("limit")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    rows = tables.query_kline_range(
        stock_code,
        start_date=start_date,
        end_date=end_date,
        limit=int(limit) if limit else None,
    )

    data = [_row_to_dict(r) for r in rows]
    return jsonify({"success": True, "data": data}), 200


# ---------------------------------------------------------------------------
# 技术指标查询
# ---------------------------------------------------------------------------


@pipeline_bp.route("/indicators", methods=["GET"])
def get_indicators():
    """
    GET /api/v1/pipeline/indicators?stock_code=600000&limit=60
    """
    stock_code = request.args.get("stock_code")
    if not stock_code:
        return jsonify({"success": False, "error": "缺少必要参数: stock_code"}), 400

    limit = request.args.get("limit")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    rows = tables.query_indicators_range(
        stock_code,
        start_date=start_date,
        end_date=end_date,
        limit=int(limit) if limit else None,
    )

    data = [_indicator_row_to_dict(r) for r in rows]
    return jsonify({"success": True, "data": data}), 200


# ---------------------------------------------------------------------------
# K 线 + 指标合并查询
# ---------------------------------------------------------------------------


@pipeline_bp.route("/stock-data", methods=["GET"])
def get_stock_data():
    """
    GET /api/v1/pipeline/stock-data?stock_code=600000&limit=120
    """
    stock_code = request.args.get("stock_code")
    if not stock_code:
        return jsonify({"success": False, "error": "缺少必要参数: stock_code"}), 400

    limit = request.args.get("limit")

    klines = tables.query_kline_range(
        stock_code, limit=int(limit) if limit else None
    )
    indicators = tables.query_indicators_range(
        stock_code, limit=int(limit) if limit else None
    )

    # 以 date 为 key 合并
    ind_map = {}
    for row in indicators:
        td = str(row["date"])
        ind_map[td] = row

    data = []
    for krow in klines:
        td = str(krow["date"])
        item = _row_to_dict(krow)
        ind = ind_map.get(td, {})
        item.update({
            "ma5": _to_float(ind.get("ma5")),
            "ma10": _to_float(ind.get("ma10")),
            "ma20": _to_float(ind.get("ma20")),
            "ma60": _to_float(ind.get("ma60")),
            "macd_dif": _to_float(ind.get("macd_dif")),
            "macd_dea": _to_float(ind.get("macd_dea")),
            "macd_bar": _to_float(ind.get("macd_bar")),
            "kdj_k": _to_float(ind.get("kdj_k")),
            "kdj_d": _to_float(ind.get("kdj_d")),
            "kdj_j": _to_float(ind.get("kdj_j")),
            "rsi6": _to_float(ind.get("rsi_6")),
            "rsi12": _to_float(ind.get("rsi_12")),
            "rsi24": _to_float(ind.get("rsi_24")),
            "boll_upper": _to_float(ind.get("boll_up")),
            "boll_middle": _to_float(ind.get("boll_mid")),
            "boll_lower": _to_float(ind.get("boll_low")),
        })
        data.append(item)

    return jsonify({"success": True, "data": data}), 200


# ---------------------------------------------------------------------------
# 手动触发
# ---------------------------------------------------------------------------


@pipeline_bp.route("/collect", methods=["POST"])
def trigger_collect():
    """POST /api/v1/pipeline/collect — 手动触发增量采集"""
    result = pipeline_daemon.trigger_collect()
    if "error" in result:
        return jsonify({"success": False, "error": result["error"]}), 500
    return jsonify({"success": True, "data": result}), 200


@pipeline_bp.route("/run-indicators", methods=["POST"])
def trigger_indicators():
    """POST /api/v1/pipeline/run-indicators — 手动触发指标计算"""
    result = pipeline_daemon.trigger_indicators()
    if "error" in result:
        return jsonify({"success": False, "error": result["error"]}), 500
    return jsonify({"success": True, "data": result}), 200


# ---------------------------------------------------------------------------
# Daemon 状态查询
# ---------------------------------------------------------------------------


@pipeline_bp.route("/status", methods=["GET"])
def get_status():
    """GET /api/v1/pipeline/status"""
    return jsonify({"success": True, "data": pipeline_daemon.status()}), 200


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def _row_to_dict(row):
    return {
        "date": str(row["date"]),
        "open": _to_float(row.get("open")),
        "high": _to_float(row.get("high")),
        "low": _to_float(row.get("low")),
        "close": _to_float(row.get("close")),
        "volume": _to_int(row.get("volume")),
    }


def _indicator_row_to_dict(row):
    return {
        "date": str(row["date"]),
        "ma5": _to_float(row.get("ma5")),
        "ma10": _to_float(row.get("ma10")),
        "ma20": _to_float(row.get("ma20")),
        "ma60": _to_float(row.get("ma60")),
        "macd_dif": _to_float(row.get("macd_dif")),
        "macd_dea": _to_float(row.get("macd_dea")),
        "macd_bar": _to_float(row.get("macd_bar")),
        "kdj_k": _to_float(row.get("kdj_k")),
        "kdj_d": _to_float(row.get("kdj_d")),
        "kdj_j": _to_float(row.get("kdj_j")),
        "rsi6": _to_float(row.get("rsi_6")),
        "rsi12": _to_float(row.get("rsi_12")),
        "rsi24": _to_float(row.get("rsi_24")),
        "boll_upper": _to_float(row.get("boll_up")),
        "boll_middle": _to_float(row.get("boll_mid")),
        "boll_lower": _to_float(row.get("boll_low")),
    }


def _to_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _to_int(val):
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
