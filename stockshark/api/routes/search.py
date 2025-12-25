"""
股票搜索相关API路由
"""

from flask import Blueprint, request, jsonify
from stockshark.analysis.search_engine import SearchEngine

search_bp = Blueprint('search', __name__)

# 初始化搜索引擎
search_engine = SearchEngine()


@search_bp.route('/stock/by-industry', methods=['GET'])
def search_by_industry():
    """
    按行业搜索股票
    参数:
    - industry_name: 行业名称
    - price_min: 价格最小值
    - price_max: 价格最大值
    - change_pct_min: 涨跌幅最小值
    - change_pct_max: 涨跌幅最大值
    - pe_min: 市盈率最小值
    - pe_max: 市盈率最大值
    - turnover_min: 换手率最小值
    - turnover_max: 换手率最大值
    - sort_by: 排序字段 (price, change_pct, pe, turnover, volume)
    - limit: 返回结果数量限制 (默认20)
    """
    try:
        industry_name = request.args.get('industry_name')
        
        if not industry_name:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: industry_name'
            }), 400
        
        # 构建筛选条件
        filters = {}
        
        try:
            price_min = request.args.get('price_min')
            if price_min is not None:
                filters['price_min'] = float(price_min)
        except (ValueError, TypeError):
            pass
        
        try:
            price_max = request.args.get('price_max')
            if price_max is not None:
                filters['price_max'] = float(price_max)
        except (ValueError, TypeError):
            pass
        
        try:
            change_pct_min = request.args.get('change_pct_min')
            if change_pct_min is not None:
                filters['change_pct_min'] = float(change_pct_min)
        except (ValueError, TypeError):
            pass
        
        try:
            change_pct_max = request.args.get('change_pct_max')
            if change_pct_max is not None:
                filters['change_pct_max'] = float(change_pct_max)
        except (ValueError, TypeError):
            pass
        
        try:
            pe_min = request.args.get('pe_min')
            if pe_min is not None:
                filters['pe_min'] = float(pe_min)
        except (ValueError, TypeError):
            pass
        
        try:
            pe_max = request.args.get('pe_max')
            if pe_max is not None:
                filters['pe_max'] = float(pe_max)
        except (ValueError, TypeError):
            pass
        
        try:
            turnover_min = request.args.get('turnover_min')
            if turnover_min is not None:
                filters['turnover_min'] = float(turnover_min)
        except (ValueError, TypeError):
            pass
        
        try:
            turnover_max = request.args.get('turnover_max')
            if turnover_max is not None:
                filters['turnover_max'] = float(turnover_max)
        except (ValueError, TypeError):
            pass
        
        sort_by = request.args.get('sort_by')
        limit = int(request.args.get('limit', 20))
        
        # 搜索
        result = search_engine.search_by_industry(
            industry_name=industry_name,
            filters=filters if filters else None,
            sort_by=sort_by,
            limit=limit
        )
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/stock/by-concept', methods=['GET'])
def search_by_concept():
    """
    按概念搜索股票
    参数:
    - concept_name: 概念名称
    - price_min: 价格最小值
    - price_max: 价格最大值
    - change_pct_min: 涨跌幅最小值
    - change_pct_max: 涨跌幅最大值
    - pe_min: 市盈率最小值
    - pe_max: 市盈率最大值
    - turnover_min: 换手率最小值
    - turnover_max: 换手率最大值
    - sort_by: 排序字段 (price, change_pct, pe, turnover, volume)
    - limit: 返回结果数量限制 (默认20)
    """
    try:
        concept_name = request.args.get('concept_name')
        
        if not concept_name:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: concept_name'
            }), 400
        
        # 构建筛选条件
        filters = {}
        
        try:
            price_min = request.args.get('price_min')
            if price_min is not None:
                filters['price_min'] = float(price_min)
        except (ValueError, TypeError):
            pass
        
        try:
            price_max = request.args.get('price_max')
            if price_max is not None:
                filters['price_max'] = float(price_max)
        except (ValueError, TypeError):
            pass
        
        try:
            change_pct_min = request.args.get('change_pct_min')
            if change_pct_min is not None:
                filters['change_pct_min'] = float(change_pct_min)
        except (ValueError, TypeError):
            pass
        
        try:
            change_pct_max = request.args.get('change_pct_max')
            if change_pct_max is not None:
                filters['change_pct_max'] = float(change_pct_max)
        except (ValueError, TypeError):
            pass
        
        try:
            pe_min = request.args.get('pe_min')
            if pe_min is not None:
                filters['pe_min'] = float(pe_min)
        except (ValueError, TypeError):
            pass
        
        try:
            pe_max = request.args.get('pe_max')
            if pe_max is not None:
                filters['pe_max'] = float(pe_max)
        except (ValueError, TypeError):
            pass
        
        try:
            turnover_min = request.args.get('turnover_min')
            if turnover_min is not None:
                filters['turnover_min'] = float(turnover_min)
        except (ValueError, TypeError):
            pass
        
        try:
            turnover_max = request.args.get('turnover_max')
            if turnover_max is not None:
                filters['turnover_max'] = float(turnover_max)
        except (ValueError, TypeError):
            pass
        
        sort_by = request.args.get('sort_by')
        limit = int(request.args.get('limit', 20))
        
        # 搜索
        result = search_engine.search_by_concept(
            concept_name=concept_name,
            filters=filters if filters else None,
            sort_by=sort_by,
            limit=limit
        )
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/stock/by-theme', methods=['GET'])
def search_by_theme():
    """
    按主题搜索股票
    参数:
    - theme_name: 主题名称
    - price_min: 价格最小值
    - price_max: 价格最大值
    - change_pct_min: 涨跌幅最小值
    - change_pct_max: 涨跌幅最大值
    - pe_min: 市盈率最小值
    - pe_max: 市盈率最大值
    - turnover_min: 换手率最小值
    - turnover_max: 换手率最大值
    - sort_by: 排序字段 (price, change_pct, pe, turnover, volume)
    - limit: 返回结果数量限制 (默认20)
    """
    try:
        theme_name = request.args.get('theme_name')
        
        if not theme_name:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: theme_name'
            }), 400
        
        # 构建筛选条件
        filters = {}
        
        try:
            price_min = request.args.get('price_min')
            if price_min is not None:
                filters['price_min'] = float(price_min)
        except (ValueError, TypeError):
            pass
        
        try:
            price_max = request.args.get('price_max')
            if price_max is not None:
                filters['price_max'] = float(price_max)
        except (ValueError, TypeError):
            pass
        
        try:
            change_pct_min = request.args.get('change_pct_min')
            if change_pct_min is not None:
                filters['change_pct_min'] = float(change_pct_min)
        except (ValueError, TypeError):
            pass
        
        try:
            change_pct_max = request.args.get('change_pct_max')
            if change_pct_max is not None:
                filters['change_pct_max'] = float(change_pct_max)
        except (ValueError, TypeError):
            pass
        
        try:
            pe_min = request.args.get('pe_min')
            if pe_min is not None:
                filters['pe_min'] = float(pe_min)
        except (ValueError, TypeError):
            pass
        
        try:
            pe_max = request.args.get('pe_max')
            if pe_max is not None:
                filters['pe_max'] = float(pe_max)
        except (ValueError, TypeError):
            pass
        
        try:
            turnover_min = request.args.get('turnover_min')
            if turnover_min is not None:
                filters['turnover_min'] = float(turnover_min)
        except (ValueError, TypeError):
            pass
        
        try:
            turnover_max = request.args.get('turnover_max')
            if turnover_max is not None:
                filters['turnover_max'] = float(turnover_max)
        except (ValueError, TypeError):
            pass
        
        sort_by = request.args.get('sort_by')
        limit = int(request.args.get('limit', 20))
        
        # 搜索
        result = search_engine.search_by_theme(
            theme=theme_name,
            filters=filters if filters else None,
            sort_by=sort_by,
            limit=limit
        )
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/stock/by-keyword', methods=['GET'])
def search_by_keyword():
    """
    按关键词搜索股票
    参数:
    - keyword: 搜索关键词
    - limit: 返回结果数量限制 (默认20)
    """
    try:
        keyword = request.args.get('keyword')
        
        if not keyword:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: keyword'
            }), 400
        
        limit = int(request.args.get('limit', 20))
        
        # 搜索
        result = search_engine.search_by_code_or_name(keyword, limit)
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/industries', methods=['GET'])
def get_industries():
    """
    获取所有行业列表
    """
    try:
        result = search_engine.get_all_industries()
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/concepts', methods=['GET'])
def get_concepts():
    """
    获取所有概念列表
    """
    try:
        result = search_engine.get_all_concepts()
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查
    """
    return jsonify({
        'success': True,
        'message': '股票搜索API服务正常'
    })
