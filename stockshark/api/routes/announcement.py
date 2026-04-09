"""公告查询 API 路由"""

from flask import Blueprint, request, jsonify
from stockshark.data.announcement import get_announcements

announcement_bp = Blueprint('announcement', __name__)


@announcement_bp.route('/stock/<stock_code>', methods=['GET'])
def stock_announcements(stock_code):
    """获取指定股票的公告列表

    GET /api/announcement/stock/603009?days=15&category=
    """
    days = request.args.get('days', 15, type=int)
    page_size = request.args.get('page_size', 30, type=int)
    category = request.args.get('category', '')

    result = get_announcements(stock_code, days=days, page_size=page_size, category=category)

    if result.get('error'):
        return jsonify(result), 404

    return jsonify(result), 200
