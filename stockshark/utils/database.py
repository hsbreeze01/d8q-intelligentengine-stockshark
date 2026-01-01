"""数据库连接工具"""
import pymysql
from pymysql.cursors import DictCursor
from pymongo import MongoClient
from stockshark.config import get_config


def get_mysql_connection():
    """
    获取MySQL数据库连接
    
    Returns:
        MySQL连接对象
    """
    config = get_config()
    try:
        conn = pymysql.connect(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        return conn
    except Exception as e:
        print(f"连接MySQL数据库失败: {e}")
        raise


def get_mongodb_connection():
    """
    获取MongoDB数据库连接
    
    Returns:
        MongoDB数据库对象
    """
    config = get_config()
    try:
        client = MongoClient(
            host=config.MONGODB_HOST,
            port=config.MONGODB_PORT
        )
        db = client[config.MONGODB_DATABASE]
        return db
    except Exception as e:
        print(f"连接MongoDB数据库失败: {e}")
        raise


def test_mysql_connection():
    """
    测试MySQL数据库连接
    
    Returns:
        bool: 连接是否成功
    """
    try:
        conn = get_mysql_connection()
        conn.close()
        return True
    except Exception as e:
        print(f"MySQL连接测试失败: {e}")
        return False


def test_mongodb_connection():
    """
    测试MongoDB数据库连接
    
    Returns:
        bool: 连接是否成功
    """
    try:
        db = get_mongodb_connection()
        db.list_collection_names()
        return True
    except Exception as e:
        print(f"MongoDB连接测试失败: {e}")
        return False
