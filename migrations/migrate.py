"""数据库迁移脚本"""
import sys
import os
import pymysql
from pymysql.cursors import DictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stockshark.utils.database import get_mysql_connection, test_mysql_connection
from stockshark.utils.logger import get_logger
from stockshark.models.stock_basic_info import StockBasicInfo
from stockshark.models.stock_daily_trade import StockDailyTrade
from stockshark.config import get_config

logger = get_logger(__name__)


def init_database():
    """
    初始化数据库，创建所有必要的表
    """
    logger.info("开始初始化数据库...")
    
    try:
        config = get_config()
        
        # 先连接到MySQL服务器（不指定数据库）
        conn = pymysql.connect(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        
        try:
            cursor = conn.cursor()
            
            # 检查并创建数据库
            cursor.execute("SHOW DATABASES LIKE %s", (config.MYSQL_DATABASE,))
            if not cursor.fetchone():
                logger.info(f"数据库 {config.MYSQL_DATABASE} 不存在，创建数据库...")
                cursor.execute(f"CREATE DATABASE {config.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                logger.info("数据库创建成功")
            
            conn.commit()
        finally:
            conn.close()
        
        # 现在测试连接到新创建的数据库
        if not test_mysql_connection():
            logger.error("MySQL数据库连接失败，请检查配置")
            return False
        
        logger.info("MySQL数据库连接成功")
        
        logger.info("创建股票基本信息表...")
        StockBasicInfo.create_table()
        logger.info("股票基本信息表创建成功")
        
        logger.info("创建股票每日交易信息表...")
        StockDailyTrade.create_table()
        logger.info("股票每日交易信息表创建成功")
        
        logger.info("数据库初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


def drop_tables():
    """
    删除所有表（仅用于开发测试）
    """
    logger.warning("开始删除所有表...")
    
    try:
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            
            tables = ['stock_daily_trade', 'stock_basic_info']
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                logger.info(f"表 {table} 已删除")
            
            conn.commit()
            logger.info("所有表删除完成")
            return True
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"删除表失败: {e}")
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库迁移工具')
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    parser.add_argument('--drop', action='store_true', help='删除所有表')
    
    args = parser.parse_args()
    
    if args.init:
        init_database()
    elif args.drop:
        drop_tables()
    else:
        parser.print_help()
