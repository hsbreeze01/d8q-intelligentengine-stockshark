from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from database import init_database
from api.routes.analysis import analysis_bp
from api.routes.search import search_bp
from api.routes.supply_chain import supply_chain_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    init_database()

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
