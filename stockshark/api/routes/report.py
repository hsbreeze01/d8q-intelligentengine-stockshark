"""研报查询 API 路由"""

from flask import Blueprint, request, jsonify
from stockshark.data.research_report import get_reports

report_bp = Blueprint('report', __name__)


@report_bp.route('/search', methods=['GET'])
def search_reports():
    """搜索研报/调研/公告

    GET /api/report/search?keyword=北特科技&page=1&limit=10
    """
    keyword = request.args.get('keyword', '')
    if not keyword:
        return jsonify({"error": "keyword参数必填"}), 400

    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    result = get_reports(keyword, page=page, limit=limit)

    if result.get('error'):
        return jsonify(result), 502

    return jsonify(result), 200


@report_bp.route('/stock/<stock_code>', methods=['GET'])
def stock_reports(stock_code):
    """获取指定股票的聚合研报（洞见+慧博+巨潮）

    GET /api/report/stock/603009?days=7&stock_name=北特科技
    """
    from stockshark.data.report_aggregator import get_stock_reports

    days = request.args.get('days', 7, type=int)
    stock_name = request.args.get('stock_name', '')

    result = get_stock_reports(stock_code, stock_name=stock_name, days=days)
    return jsonify(result), 200
