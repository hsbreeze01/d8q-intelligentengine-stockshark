from flask import Flask, request, jsonify
from flask_cors import CORS
from stockshark.config import Config
from stockshark.data.database import DatabaseManager
from stockshark.api.routes.analysis import analysis_bp
from stockshark.api.routes.search import search_bp
from stockshark.api.routes.supply_chain import supply_chain_bp


def create_app(config=None):
    """
    创建并配置 Flask 应用
    
    Args:
        config: 配置对象，如果为 None 则使用默认配置
    
    Returns:
        Flask 应用实例
    """
    app = Flask(__name__)
    
    if config:
        app.config.from_object(config)
    else:
        app.config.from_object(Config)
    
    CORS(app)
    
    DatabaseManager.init_database()
    
    app.register_blueprint(analysis_bp, url_prefix=f'{Config.API_PREFIX}/analysis')
    app.register_blueprint(search_bp, url_prefix=f'{Config.API_PREFIX}/search')
    app.register_blueprint(supply_chain_bp, url_prefix=f'{Config.API_PREFIX}/supply-chain')
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'ok',
            'message': 'Stock Analysis System API is running',
            'timestamp': request.args.get('timestamp')
        }), 200
    
    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'name': 'Stock Analysis System API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'analysis': f'{Config.API_PREFIX}/analysis',
                'search': f'{Config.API_PREFIX}/search',
                'supply_chain': f'{Config.API_PREFIX}/supply-chain'
            }
        }), 200
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )
