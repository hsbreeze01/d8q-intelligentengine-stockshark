"""
股票分析相关API路由
"""

from flask import Blueprint, request, jsonify
from stockshark.data.akshare_data import AkShareData
from stockshark.data.data_processor import DataProcessor
from stockshark.analysis.stock_analyzer import StockAnalyzer

analysis_bp = Blueprint('analysis', __name__)

stock_analyzer = StockAnalyzer()


@analysis_bp.route('/stock/analyze', methods=['POST'])
def analyze_stock():
    """
    分析单只股票
    请求体:
    {
        "symbol": "股票代码"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'symbol' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: symbol'
            }), 400
        
        symbol = data['symbol']
        
        # 分析股票
        result = stock_analyzer.analyze_stock(symbol)
        
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


@analysis_bp.route('/stock/analyze/batch', methods=['POST'])
def analyze_stocks_batch():
    """
    批量分析股票
    请求体:
    {
        "symbols": ["股票代码1", "股票代码2", ...]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'symbols' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: symbols'
            }), 400
        
        symbols = data['symbols']
        
        if not isinstance(symbols, list):
            return jsonify({
                'success': False,
                'error': 'symbols参数必须是数组'
            }), 400
        
        results = []
        for symbol in symbols:
            result = stock_analyzer.analyze_stock(symbol)
            results.append(result)
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analysis_bp.route('/stock/valuation', methods=['GET'])
def get_stock_valuation():
    """
    获取股票估值数据
    参数:
    - symbol: 股票代码
    """
    try:
        symbol = request.args.get('symbol')
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: symbol'
            }), 400
        
        # 获取估值数据
        valuation_data = stock_analyzer.ak_data.get_stock_valuation_data(symbol)
        
        return jsonify({
            'success': True,
            'data': valuation_data.to_dict('records') if valuation_data is not None else []
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analysis_bp.route('/stock/financial', methods=['GET'])
def get_stock_financial():
    """
    获取股票财务数据
    参数:
    - symbol: 股票代码
    - report_type: 报告类型 (annual/quarterly)
    """
    try:
        symbol = request.args.get('symbol')
        report_type = request.args.get('report_type', 'annual')
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: symbol'
            }), 400
        
        # 获取财务数据
        financial_data = stock_analyzer.ak_data.get_stock_financial_data(symbol, report_type)
        
        return jsonify({
            'success': True,
            'data': financial_data.to_dict('records') if financial_data is not None else []
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analysis_bp.route('/stock/quote', methods=['GET'])
def get_stock_quote():
    """
    获取股票实时行情
    参数:
    - symbol: 股票代码
    """
    try:
        symbol = request.args.get('symbol')
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: symbol'
            }), 400
        
        # 获取实时行情
        quote_data = stock_analyzer.ak_data.get_stock_quote(symbol)
        
        if quote_data is None:
            return jsonify({
                'success': False,
                'error': '获取股票行情失败'
            }), 500
        
        return jsonify({
            'success': True,
            'data': quote_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analysis_bp.route('/stock/basic', methods=['GET'])
def get_stock_basic():
    """
    获取股票基本信息
    参数:
    - symbol: 股票代码
    """
    try:
        symbol = request.args.get('symbol')
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: symbol'
            }), 400
        
        # 获取基本信息
        basic_info = stock_analyzer.ak_data.get_stock_basic_info(symbol)
        
        if basic_info is None:
            return jsonify({
                'success': False,
                'error': '获取股票基本信息失败'
            }), 500
        
        return jsonify({
            'success': True,
            'data': basic_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analysis_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查
    """
    return jsonify({
        'success': True,
        'message': '股票分析API服务正常'
    })
