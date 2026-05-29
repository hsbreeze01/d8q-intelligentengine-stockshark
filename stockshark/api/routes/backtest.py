"""回测 API 路由（含大盘基准对比）"""

from flask import Blueprint, request, jsonify

backtest_bp = Blueprint('backtest', __name__)


@backtest_bp.route('/run', methods=['POST'])
def run_backtest():
    """
    执行回测

    POST /api/backtest/run
    Body: {
        "name": "RSI超卖反弹",
        "start_date": "2025-01-01",
        "end_date": "2026-05-27",
        "initial_capital": 1000000,
        "max_positions": 10,
        "position_size_pct": 0.10,
        "entry_conditions": [
            {"indicator": "rsi_6", "operator": "<", "value": 30}
        ],
        "exit_conditions": [
            {"indicator": "rsi_6", "operator": ">", "value": 70}
        ],
        "signal_logic": "AND",
        "stop_loss_pct": -0.08,
        "take_profit_pct": 0.20,
        "max_holding_days": 20,
        "stock_pool": [],
        "benchmark": "000300"          ← 大盘基准，可选: 000300/000001/399006/399001/000905
    }
    """
    from stockshark.analysis.backtest_engine import BacktestEngine

    data = request.get_json() or {}
    if not data.get("entry_conditions"):
        return jsonify({"success": False, "error": "entry_conditions 必填"}), 400

    try:
        engine = BacktestEngine()
        result = engine.run(data)

        # 采样权益曲线和基准曲线（每5天一个点）
        equity_sample = result.get("equity_curve", [])[::5]
        benchmark_sample = result.get("benchmark_curve", [])[::5]

        return jsonify({
            "success": True,
            "data": {
                "name": result.get("name"),
                "benchmark": result.get("benchmark"),
                "benchmark_name": result.get("benchmark_name"),
                "stats": result.get("stats"),
                "total_trades": len(result.get("trades", [])),
                "curve_points": len(result.get("equity_curve", [])),
                "trades": result.get("trades", [])[:50],
                "equity_curve_sample": equity_sample,
                "benchmark_curve_sample": benchmark_sample,
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@backtest_bp.route('/presets', methods=['GET'])
def get_presets():
    """获取预设策略配置"""
    presets = [
        {
            "name": "RSI超卖反弹",
            "description": "RSI<30 + KDJ_K<20 买入，RSI>70 卖出",
            "config": {
                "entry_conditions": [
                    {"indicator": "rsi_6", "operator": "<", "value": 30},
                    {"indicator": "kdj_k", "operator": "<", "value": 20}
                ],
                "exit_conditions": [
                    {"indicator": "rsi_6", "operator": ">", "value": 70}
                ],
                "signal_logic": "AND",
                "stop_loss_pct": -0.08,
                "take_profit_pct": 0.20,
                "max_holding_days": 20,
                "benchmark": "000300",
            }
        },
        {
            "name": "底部共振",
            "description": "RSI<15 + KDJ_K<15（SCORING模式，全部满足）",
            "config": {
                "entry_conditions": [
                    {"indicator": "rsi_6", "operator": "<", "value": 15},
                    {"indicator": "kdj_k", "operator": "<", "value": 15}
                ],
                "exit_conditions": [
                    {"indicator": "kdj_k", "operator": ">", "value": 80}
                ],
                "signal_logic": "SCORING",
                "scoring_threshold": 2,
                "stop_loss_pct": -0.10,
                "take_profit_pct": 0.30,
                "max_holding_days": 30,
                "benchmark": "000300",
            }
        },
        {
            "name": "放量突破",
            "description": "量比>2 + KDJ_K>0",
            "config": {
                "entry_conditions": [
                    {"indicator": "volume_ratio", "operator": ">", "value": 2.0},
                    {"indicator": "kdj_k", "operator": ">", "value": 0},
                ],
                "exit_conditions": [
                    {"indicator": "volume_ratio", "operator": "<", "value": 0.5}
                ],
                "signal_logic": "AND",
                "stop_loss_pct": -0.05,
                "take_profit_pct": 0.15,
                "max_holding_days": 10,
                "benchmark": "000300",
            }
        },
        {
            "name": "均线多头",
            "description": "MA5>MA20（趋势跟踪）",
            "config": {
                "entry_conditions": [
                    {"indicator": "ma5", "operator": ">", "value": 0},
                ],
                "exit_conditions": [],
                "signal_logic": "AND",
                "stop_loss_pct": -0.06,
                "take_profit_pct": 0.25,
                "max_holding_days": 15,
                "benchmark": "000300",
            }
        }
    ]
    return jsonify({"success": True, "data": presets}), 200


@backtest_bp.route('/benchmarks', methods=['GET'])
def get_benchmarks():
    """获取可用的大盘基准指数列表"""
    from stockshark.analysis.backtest_engine import INDEX_NAMES
    benchmarks = [
        {"code": code, "name": name, "default": code == "000300"}
        for code, name in INDEX_NAMES.items()
    ]
    return jsonify({"success": True, "data": benchmarks}), 200
