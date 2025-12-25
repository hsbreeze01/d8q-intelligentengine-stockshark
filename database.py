import pymysql
from pymongo import MongoClient
from config import Config

# MySQL数据库连接
def get_mysql_connection():
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"MySQL connection error: {e}")
        return None

# MongoDB数据库连接
def get_mongodb_connection():
    try:
        client = MongoClient(
            host=Config.MONGODB_HOST,
            port=Config.MONGODB_PORT
        )
        db = client[Config.MONGODB_DATABASE]
        return db
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        return None

# 初始化数据库
def init_database():
    # 初始化MySQL
    mysql_conn = get_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                # 创建股票基本信息表
                cursor.execute('''
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
                ''')
                
                # 创建股票财务数据表
                cursor.execute('''
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
                ''')
                
                # 创建主题表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS theme (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(50) NOT NULL UNIQUE,
                        description TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                ''')
                
                # 创建股票主题关联表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS stock_theme (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        stock_id INT NOT NULL,
                        theme_id INT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (stock_id) REFERENCES stock_basic(id),
                        FOREIGN KEY (theme_id) REFERENCES theme(id),
                        UNIQUE KEY (stock_id, theme_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                ''')
                
                # 创建公司信息表
                cursor.execute('''
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
                ''')
                
                # 创建供应链关系表
                cursor.execute('''
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
                
                mysql_conn.commit()
                print("MySQL tables created successfully.")
        except Exception as e:
            print(f"MySQL table creation error: {e}")
        finally:
            mysql_conn.close()
    
    # 初始化MongoDB
    mongodb_conn = get_mongodb_connection()
    if mongodb_conn is not None:
        try:
            # 检查集合是否存在，不存在则创建
            collections = ['news', 'analysis_results', 'scenario_analysis']
            for coll_name in collections:
                if coll_name not in mongodb_conn.list_collection_names():
                    mongodb_conn.create_collection(coll_name)
                    print(f"MongoDB collection {coll_name} created successfully.")
        except Exception as e:
            print(f"MongoDB collection creation error: {e}")
