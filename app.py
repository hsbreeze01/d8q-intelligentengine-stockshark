from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from database import init_database, get_mysql_connection, get_mongodb_connection

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 配置CORS
CORS(app)

# 初始化数据库
init_database()

# 数据库连接
mysql_conn = get_mysql_connection()
mongodb_conn = get_mongodb_connection()

# 健康检查接口
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'Stock Analysis System is running',
        'timestamp': request.args.get('timestamp')
    }), 200

# 主入口
if __name__ == '__main__':
    # 启动Flask应用
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )
