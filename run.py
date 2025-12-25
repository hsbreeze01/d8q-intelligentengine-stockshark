#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
StockShark 股票分析系统主入口
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stockshark.api.app import create_app
from stockshark.config import config

if __name__ == '__main__':
    env = os.environ.get('FLASK_ENV', 'development')
    app_config = config.get(env, config['default'])
    
    app = create_app(app_config)
    
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"Starting StockShark API Server in {env} mode...")
    print(f"Server running at http://{host}:{port}")
    
    app.run(host=host, port=port, debug=app_config.DEBUG)
