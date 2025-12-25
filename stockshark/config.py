import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """基础配置类"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'
    
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'password'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'stock_analysis_system'
    
    MONGODB_HOST = os.environ.get('MONGODB_HOST') or 'localhost'
    MONGODB_PORT = int(os.environ.get('MONGODB_PORT') or 27017)
    MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE') or 'stock_analysis_system'
    
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    API_PREFIX = '/api'
    
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    MYSQL_DATABASE = 'test_stock_analysis_system'
    MONGODB_DATABASE = 'test_stock_analysis_system'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """
    获取配置对象
    
    Args:
        env: 环境名称，默认从环境变量 FLASK_ENV 获取
    
    Returns:
        配置类
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
