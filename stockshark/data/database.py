import pymysql
from pymongo import MongoClient
from stockshark.config import Config
from stockshark.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """数据库管理类"""
    
    _mysql_connection = None
    _mongodb_connection = None
    
    @classmethod
    def get_mysql_connection(cls):
        """获取 MySQL 连接"""
        if cls._mysql_connection is None:
            try:
                cls._mysql_connection = pymysql.connect(
                    host=Config.MYSQL_HOST,
                    port=Config.MYSQL_PORT,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD,
                    database=Config.MYSQL_DATABASE,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
                logger.info("MySQL connection established successfully")
            except Exception as e:
                logger.error(f"MySQL connection error: {e}")
                cls._mysql_connection = None
        return cls._mysql_connection
    
    @classmethod
    def get_mongodb_connection(cls):
        """获取 MongoDB 连接"""
        if cls._mongodb_connection is None:
            try:
                client = MongoClient(
                    host=Config.MONGODB_HOST,
                    port=Config.MONGODB_PORT
                )
                cls._mongodb_connection = client[Config.MONGODB_DATABASE]
                logger.info("MongoDB connection established successfully")
            except Exception as e:
                logger.error(f"MongoDB connection error: {e}")
                cls._mongodb_connection = None
        return cls._mongodb_connection
    
    @classmethod
    def init_database(cls):
        """初始化数据库表结构"""
        cls._init_mysql()
        cls._init_mongodb()
    
    @classmethod
    def _init_mysql(cls):
        """初始化 MySQL 表结构"""
        mysql_conn = cls.get_mysql_connection()
        if mysql_conn:
            try:
                with mysql_conn.cursor() as cursor:
                    tables = [
                        ('stock_basic', '''
                            CREATE TABLE IF NOT EXISTS stock_basic (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                code VARCHAR(20) NOT NULL UNIQUE,
                                name VARCHAR(50) NOT NULL,
                                industry VARCHAR(50),
                                market VARCHAR(20),
                                list_date DATE,
                                total_share BIGINT,
                                float_share BIGINT,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                        '''),
                        ('stock_finance', '''
                            CREATE TABLE IF NOT EXISTS stock_finance (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                stock_id INT NOT NULL,
                                report_date DATE NOT NULL,
                                pe FLOAT,
                                pb FLOAT,
                                roe FLOAT,
                                revenue BIGINT,
                                profit BIGINT,
                                debt_ratio FLOAT,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                FOREIGN KEY (stock_id) REFERENCES stock_basic(id)
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                        '''),
                        ('theme', '''
                            CREATE TABLE IF NOT EXISTS theme (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                name VARCHAR(50) NOT NULL UNIQUE,
                                description TEXT,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                        '''),
                        ('stock_theme', '''
                            CREATE TABLE IF NOT EXISTS stock_theme (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                stock_id INT NOT NULL,
                                theme_id INT NOT NULL,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (stock_id) REFERENCES stock_basic(id),
                                FOREIGN KEY (theme_id) REFERENCES theme(id),
                                UNIQUE KEY (stock_id, theme_id)
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                        '''),
                        ('company', '''
                            CREATE TABLE IF NOT EXISTS company (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                name VARCHAR(100) NOT NULL,
                                is_listed BOOLEAN DEFAULT FALSE,
                                ticker VARCHAR(20),
                                exchange VARCHAR(50),
                                industry VARCHAR(50),
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                        '''),
                        ('supply_chain', '''
                            CREATE TABLE IF NOT EXISTS supply_chain (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                upstream_company_id INT NOT NULL,
                                downstream_company_id INT NOT NULL,
                                relation_type VARCHAR(20) NOT NULL,
                                description TEXT,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (upstream_company_id) REFERENCES company(id),
                                FOREIGN KEY (downstream_company_id) REFERENCES company(id)
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                        ''')
                    ]
                    
                    for table_name, sql in tables:
                        cursor.execute(sql)
                    
                    mysql_conn.commit()
                    logger.info("MySQL tables created successfully")
            except Exception as e:
                logger.error(f"MySQL table creation error: {e}")
    
    @classmethod
    def _init_mongodb(cls):
        """初始化 MongoDB 集合"""
        mongodb_conn = cls.get_mongodb_connection()
        if mongodb_conn is not None:
            try:
                collections = ['news', 'analysis_results', 'scenario_analysis']
                for coll_name in collections:
                    if coll_name not in mongodb_conn.list_collection_names():
                        mongodb_conn.create_collection(coll_name)
                        logger.info(f"MongoDB collection {coll_name} created successfully")
            except Exception as e:
                logger.error(f"MongoDB collection creation error: {e}")
    
    @classmethod
    def close_connections(cls):
        """关闭所有数据库连接"""
        if cls._mysql_connection:
            cls._mysql_connection.close()
            cls._mysql_connection = None
            logger.info("MySQL connection closed")
        
        if cls._mongodb_connection:
            cls._mongodb_connection.client.close()
            cls._mongodb_connection = None
            logger.info("MongoDB connection closed")
