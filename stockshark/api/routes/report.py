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
