"""股票基本信息模型"""
from datetime import datetime
from stockshark.utils.database import get_mysql_connection


class StockBasicInfo:
    """股票基本信息模型"""
    
    def __init__(self, symbol, name, full_name='', industry='', concept='', 
                 region='', market='', list_date=None):
        self.symbol = symbol
        self.name = name
        self.full_name = full_name
        self.industry = industry
        self.concept = concept
        self.region = region
        self.market = market
        self.list_date = list_date
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    @staticmethod
    def create_table():
        """创建股票基本信息表"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_basic_info (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL UNIQUE COMMENT '股票代码',
                    name VARCHAR(50) NOT NULL COMMENT '股票名称',
                    full_name VARCHAR(100) DEFAULT '' COMMENT '股票全称',
                    industry VARCHAR(100) DEFAULT '' COMMENT '所属行业',
                    concept TEXT COMMENT '所属概念，JSON格式',
                    region VARCHAR(50) DEFAULT '' COMMENT '所属地区',
                    market VARCHAR(20) DEFAULT '' COMMENT '所属市场（沪市/深市）',
                    list_date DATE DEFAULT NULL COMMENT '上市日期',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_symbol (symbol),
                    INDEX idx_industry (industry),
                    INDEX idx_market (market)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票基本信息表'
            """)
            conn.commit()
        finally:
            conn.close()
    
    def save(self):
        """保存或更新股票基本信息"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            self.updated_at = datetime.now()
            
            cursor.execute("""
                INSERT INTO stock_basic_info 
                (symbol, name, full_name, industry, concept, region, market, list_date, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                full_name = VALUES(full_name),
                industry = VALUES(industry),
                concept = VALUES(concept),
                region = VALUES(region),
                market = VALUES(market),
                list_date = VALUES(list_date),
                updated_at = VALUES(updated_at)
            """, (
                self.symbol, self.name, self.full_name, self.industry, self.concept,
                self.region, self.market, self.list_date, self.created_at, self.updated_at
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"保存股票基本信息失败: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_by_symbol(symbol):
        """根据股票代码获取基本信息"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM stock_basic_info WHERE symbol = %s
            """, (symbol,))
            result = cursor.fetchone()
            return result
        except Exception as e:
            print(f"获取股票基本信息失败: {e}")
            return None
        finally:
            conn.close()
    
    @staticmethod
    def get_all_symbols():
        """获取所有股票代码"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT symbol FROM stock_basic_info")
            results = cursor.fetchall()
            symbols = [row['symbol'] for row in results]
            print(f"从数据库获取到 {len(symbols)} 个股票代码")
            return symbols
        except Exception as e:
            print(f"获取所有股票代码失败: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def batch_save(stock_infos):
        """批量保存股票基本信息"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            updated_at = datetime.now()
            
            for stock_info in stock_infos:
                cursor.execute("""
                    INSERT INTO stock_basic_info 
                    (symbol, name, full_name, industry, concept, region, market, list_date, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    full_name = VALUES(full_name),
                    industry = VALUES(industry),
                    concept = VALUES(concept),
                    region = VALUES(region),
                    market = VALUES(market),
                    list_date = VALUES(list_date),
                    updated_at = VALUES(updated_at)
                """, (
                    stock_info['symbol'], stock_info['name'], stock_info.get('full_name', ''),
                    stock_info.get('industry', ''), stock_info.get('concept', ''),
                    stock_info.get('region', ''), stock_info.get('market', ''),
                    stock_info.get('list_date'), stock_info.get('created_at', datetime.now()),
                    updated_at
                ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"批量保存股票基本信息失败: {e}")
            return False
        finally:
            conn.close()
