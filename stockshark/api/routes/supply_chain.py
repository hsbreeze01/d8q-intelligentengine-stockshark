"""
供应链分析相关API路由
"""

from flask import Blueprint, request, jsonify
from stockshark.data.akshare_data import AkShareData
from stockshark.analysis.supply_chain_analyzer import SupplyChainAnalyzer

supply_chain_bp = Blueprint('supply_chain', __name__)

# 初始化供应链分析器
akshare_data = AkShareData()
supply_chain_analyzer = SupplyChainAnalyzer(akshare_data)


@supply_chain_bp.route('/analyze-scenario', methods=['POST'])
def analyze_scenario():
    """
    分析场景，识别相关供应链企业
    请求体:
    {
        "scenario": "场景描述文本"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'scenario' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: scenario'
            }), 400
        
        scenario = data['scenario']
        
        if not scenario or not isinstance(scenario, str):
            return jsonify({
                'success': False,
                'error': 'scenario参数必须是非空字符串'
            }), 400
        
        # 分析场景
        result = supply_chain_analyzer.analyze_scenario(scenario)
        
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


@supply_chain_bp.route('/company/supply-chain', methods=['GET'])
def get_company_supply_chain():
    """
    获取指定公司的供应链信息
    参数:
    - company_name: 公司名称
    """
    try:
        company_name = request.args.get('company_name')
        
        if not company_name:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: company_name'
            }), 400
        
        # 获取供应链信息
        result = supply_chain_analyzer.get_company_supply_chain(company_name)
        
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


@supply_chain_bp.route('/supplier/search', methods=['GET'])
def search_supplier():
    """
    按关键词搜索供应商
    参数:
    - keyword: 搜索关键词
    """
    try:
        keyword = request.args.get('keyword')
        
        if not keyword:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: keyword'
            }), 400
        
        # 搜索供应商
        result = supply_chain_analyzer.search_supplier_by_keyword(keyword)
        
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


@supply_chain_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查
    """
    return jsonify({
        'success': True,
        'message': '供应链分析API服务正常'
    })
