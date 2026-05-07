"""关注股票 API 路由"""

from flask import Blueprint, request, jsonify
from stockshark.services.tracked_stock_service import TrackedStockService

tracked_stocks_bp = Blueprint("tracked_stocks", __name__)

service = TrackedStockService()


@tracked_stocks_bp.route("", methods=["GET"])
def list_tracked_stocks():
    """
    查询关注股票列表
    可选参数: group_name — 按分组过滤
    """
    try:
        group_name = request.args.get("group_name")
        data = service.list_all(group_name=group_name)
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@tracked_stocks_bp.route("", methods=["POST"])
def add_tracked_stock():
    """
    添加单条关注股票
    JSON body: stock_code (必填), stock_name, group_name, sort_order, notes (可选)
    """
    try:
        body = request.get_json(silent=True) or {}
        stock_code = body.get("stock_code")
        if not stock_code:
            return jsonify({"success": False, "error": "缺少必要参数: stock_code"}), 400

        record = service.add(
            stock_code=stock_code,
            stock_name=body.get("stock_name"),
            group_name=body.get("group_name"),
            sort_order=body.get("sort_order", 0),
            notes=body.get("notes"),
        )
        return jsonify({"success": True, "data": record}), 201
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 409
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@tracked_stocks_bp.route("/batch", methods=["POST"])
def batch_add_tracked_stocks():
    """
    批量添加关注股票
    JSON body: { "stocks": [ { "stock_code": "...", ... }, ... ] }
    """
    try:
        body = request.get_json(silent=True) or {}
        stocks = body.get("stocks")
        if not stocks or not isinstance(stocks, list):
            return jsonify({"success": False, "error": "缺少必要参数: stocks"}), 400

        result = service.batch_add(stocks)
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@tracked_stocks_bp.route("/groups", methods=["GET"])
def get_groups():
    """获取所有不重复的分组名称"""
    try:
        groups = service.get_groups()
        return jsonify({"success": True, "data": groups}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@tracked_stocks_bp.route("/<int:stock_id>", methods=["PUT"])
def update_tracked_stock(stock_id):
    """
    更新关注股票
    JSON body: 任意子集 stock_name, group_name, sort_order, notes
    """
    try:
        body = request.get_json(silent=True) or {}
        record = service.update(stock_id, **body)
        return jsonify({"success": True, "data": record}), 200
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@tracked_stocks_bp.route("/<int:stock_id>", methods=["DELETE"])
def delete_tracked_stock(stock_id):
    """删除关注股票"""
    try:
        service.delete(stock_id)
        return jsonify({"success": True, "message": "删除成功"}), 200
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
