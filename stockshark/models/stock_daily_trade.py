"""股票每日交易信息模型"""
from datetime import datetime, date
from stockshark.utils.database import get_mysql_connection


class StockDailyTrade:
    """股票每日交易信息模型"""
    
    def __init__(self, symbol, trade_date, open_price, high_price, low_price, 
                 close_price, volume, amount, change_pct=None, turnover_rate=None):
        self.symbol = symbol
        self.trade_date = trade_date
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.amount = amount
        self.change_pct = change_pct
        self.turnover_rate = turnover_rate
        self.created_at = datetime.now()
    
    @staticmethod
    def create_table():
        """创建股票每日交易信息表"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_daily_trade (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL COMMENT '股票代码',
                    trade_date DATE NOT NULL COMMENT '交易日期',
                    open_price DECIMAL(10, 2) DEFAULT NULL COMMENT '开盘价',
                    high_price DECIMAL(10, 2) DEFAULT NULL COMMENT '最高价',
                    low_price DECIMAL(10, 2) DEFAULT NULL COMMENT '最低价',
                    close_price DECIMAL(10, 2) DEFAULT NULL COMMENT '收盘价',
                    volume BIGINT DEFAULT NULL COMMENT '成交量（手）',
                    amount DECIMAL(20, 2) DEFAULT NULL COMMENT '成交额（元）',
                    change_pct DECIMAL(10, 4) DEFAULT NULL COMMENT '涨跌幅（%）',
                    turnover_rate DECIMAL(10, 4) DEFAULT NULL COMMENT '换手率（%）',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    UNIQUE KEY uk_symbol_date (symbol, trade_date),
                    INDEX idx_symbol (symbol),
                    INDEX idx_trade_date (trade_date),
                    INDEX idx_symbol_date (symbol, trade_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票每日交易信息表'
            """)
            conn.commit()
        finally:
            conn.close()
    
    def save(self):
        """保存或更新股票每日交易信息"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO stock_daily_trade 
                (symbol, trade_date, open_price, high_price, low_price, close_price, 
                 volume, amount, change_pct, turnover_rate, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                open_price = VALUES(open_price),
                high_price = VALUES(high_price),
                low_price = VALUES(low_price),
                close_price = VALUES(close_price),
                volume = VALUES(volume),
                amount = VALUES(amount),
                change_pct = VALUES(change_pct),
                turnover_rate = VALUES(turnover_rate)
            """, (
                self.symbol, self.trade_date, self.open_price, self.high_price, self.low_price,
                self.close_price, self.volume, self.amount, self.change_pct, 
                self.turnover_rate, self.created_at
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"保存股票每日交易信息失败: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_by_symbol_and_date(symbol, trade_date):
        """根据股票代码和交易日期获取交易信息"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM stock_daily_trade 
                WHERE symbol = %s AND trade_date = %s
            """, (symbol, trade_date))
            result = cursor.fetchone()
            return result
        except Exception as e:
            print(f"获取股票交易信息失败: {e}")
            return None
        finally:
            conn.close()
    
    @staticmethod
    def get_history_by_symbol(symbol, start_date=None, end_date=None, limit=100):
        """获取股票历史交易数据"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            
            query = "SELECT * FROM stock_daily_trade WHERE symbol = %s"
            params = [symbol]
            
            if start_date:
                query += " AND trade_date >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND trade_date <= %s"
                params.append(end_date)
            
            query += " ORDER BY trade_date DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"获取股票历史数据失败: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def get_latest_trade_date(symbol):
        """获取股票最新交易日期"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(trade_date) as max_date FROM stock_daily_trade WHERE symbol = %s
            """, (symbol,))
            result = cursor.fetchone()
            return result['max_date'] if result and result['max_date'] else None
        except Exception as e:
            print(f"获取最新交易日期失败: {e}")
            return None
        finally:
            conn.close()
    
    @staticmethod
    def batch_save(trade_records):
        """批量保存股票交易信息"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            created_at = datetime.now()
            
            for record in trade_records:
                cursor.execute("""
                    INSERT INTO stock_daily_trade 
                    (symbol, trade_date, open_price, high_price, low_price, close_price, 
                     volume, amount, change_pct, turnover_rate, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    open_price = VALUES(open_price),
                    high_price = VALUES(high_price),
                    low_price = VALUES(low_price),
                    close_price = VALUES(close_price),
                    volume = VALUES(volume),
                    amount = VALUES(amount),
                    change_pct = VALUES(change_pct),
                    turnover_rate = VALUES(turnover_rate)
                """, (
                    record['symbol'], record['trade_date'], record['open_price'], 
                    record['high_price'], record['low_price'], record['close_price'],
                    record['volume'], record['amount'], record.get('change_pct'),
                    record.get('turnover_rate'), created_at
                ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"批量保存股票交易信息失败: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_all_symbols():
        """获取所有有交易数据的股票代码"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT symbol FROM stock_daily_trade")
            results = cursor.fetchall()
            return [row['symbol'] for row in results]
        except Exception as e:
            print(f"获取所有股票代码失败: {e}")
            return []
        finally:
            conn.close()
