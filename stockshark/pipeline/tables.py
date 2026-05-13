"""stock_data_daily / indicators_daily 建表和 DAO 操作"""

from stockshark.utils.database import get_mysql_connection
from stockshark.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# stock_data_daily
# ---------------------------------------------------------------------------

STOCK_DATA_DAILY_DDL = """
CREATE TABLE IF NOT EXISTS stock_data_daily (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(10)  NOT NULL COMMENT '股票代码',
    trade_date DATE         NOT NULL COMMENT '交易日期',
    `open`    DECIMAL(10,3) DEFAULT NULL COMMENT '开盘价',
    high      DECIMAL(10,3) DEFAULT NULL COMMENT '最高价',
    low       DECIMAL(10,3) DEFAULT NULL COMMENT '最低价',
    `close`   DECIMAL(10,3) DEFAULT NULL COMMENT '收盘价',
    volume    BIGINT        DEFAULT NULL COMMENT '成交量',
    amount    DECIMAL(20,3) DEFAULT NULL COMMENT '成交额',
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_code_date (stock_code, trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='日K线数据表'
"""

INDICATORS_DAILY_DDL = """
CREATE TABLE IF NOT EXISTS indicators_daily (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    stock_code   VARCHAR(10)  NOT NULL,
    trade_date   DATE         NOT NULL,
    ma5          DECIMAL(10,3) DEFAULT NULL,
    ma10         DECIMAL(10,3) DEFAULT NULL,
    ma20         DECIMAL(10,3) DEFAULT NULL,
    ma60         DECIMAL(10,3) DEFAULT NULL,
    macd_dif     DECIMAL(10,4) DEFAULT NULL,
    macd_dea     DECIMAL(10,4) DEFAULT NULL,
    macd_bar     DECIMAL(10,4) DEFAULT NULL,
    kdj_k        DECIMAL(10,3) DEFAULT NULL,
    kdj_d        DECIMAL(10,3) DEFAULT NULL,
    kdj_j        DECIMAL(10,3) DEFAULT NULL,
    rsi6         DECIMAL(10,3) DEFAULT NULL,
    rsi12        DECIMAL(10,3) DEFAULT NULL,
    rsi24        DECIMAL(10,3) DEFAULT NULL,
    boll_upper   DECIMAL(10,3) DEFAULT NULL,
    boll_middle  DECIMAL(10,3) DEFAULT NULL,
    boll_lower   DECIMAL(10,3) DEFAULT NULL,
    created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_code_date (stock_code, trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='技术指标日表'
"""


def ensure_tables():
    """建表（幂等）"""
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(STOCK_DATA_DAILY_DDL)
        cursor.execute(INDICATORS_DAILY_DDL)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# stock_data_daily DAO
# ---------------------------------------------------------------------------

def upsert_kline_rows(rows):
    """
    批量写入 K 线数据（ON DUPLICATE KEY UPDATE）

    Args:
        rows: list of dict, 每个包含
              stock_code, trade_date, open, high, low, close, volume, amount
    """
    if not rows:
        return
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        sql = """
        INSERT INTO stock_data_daily
            (stock_code, trade_date, `open`, high, low, `close`, volume, amount)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            `open`=VALUES(`open`), high=VALUES(high), low=VALUES(low),
            `close`=VALUES(`close`), volume=VALUES(volume), amount=VALUES(amount)
        """
        params = [
            (
                r["stock_code"], r["trade_date"],
                r.get("open"), r.get("high"), r.get("low"), r.get("close"),
                r.get("volume"), r.get("amount"),
            )
            for r in rows
        ]
        cursor.executemany(sql, params)
        conn.commit()
    finally:
        conn.close()


def query_latest_date(stock_code):
    """
    返回 stock_data_daily 中该股票最新 trade_date（date 对象），
    无记录时返回 None。
    """
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MAX(trade_date) AS max_date "
            "FROM stock_data_daily WHERE stock_code = %s",
            (stock_code,),
        )
        row = cursor.fetchone()
        return row["max_date"] if row and row["max_date"] else None
    finally:
        conn.close()


def query_kline_range(stock_code, start_date=None, end_date=None, limit=None):
    """
    查询 K 线数据，按 trade_date 升序。

    Args:
        stock_code: 股票代码（必填）
        start_date: 起始日期（可选）
        end_date: 结束日期（可选）
        limit: 返回条数（可选）

    Returns:
        list[dict]
    """
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        conditions = ["stock_code = %s"]
        params = [stock_code]
        if start_date:
            conditions.append("trade_date >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("trade_date <= %s")
            params.append(end_date)

        where = " AND ".join(conditions)
        sql = f"SELECT * FROM stock_data_daily WHERE {where} ORDER BY trade_date ASC"
        if limit:
            sql += f" LIMIT {int(limit)}"

        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# indicators_daily DAO
# ---------------------------------------------------------------------------

def upsert_indicator_rows(rows):
    """
    批量写入指标数据（ON DUPLICATE KEY UPDATE）

    Args:
        rows: list of dict
    """
    if not rows:
        return
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        sql = """
        INSERT INTO indicators_daily
            (stock_code, trade_date,
             ma5, ma10, ma20, ma60,
             macd_dif, macd_dea, macd_bar,
             kdj_k, kdj_d, kdj_j,
             rsi6, rsi12, rsi24,
             boll_upper, boll_middle, boll_lower)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            ma5=VALUES(ma5), ma10=VALUES(ma10), ma20=VALUES(ma20), ma60=VALUES(ma60),
            macd_dif=VALUES(macd_dif), macd_dea=VALUES(macd_dea), macd_bar=VALUES(macd_bar),
            kdj_k=VALUES(kdj_k), kdj_d=VALUES(kdj_d), kdj_j=VALUES(kdj_j),
            rsi6=VALUES(rsi6), rsi12=VALUES(rsi12), rsi24=VALUES(rsi24),
            boll_upper=VALUES(boll_upper), boll_middle=VALUES(boll_middle),
            boll_lower=VALUES(boll_lower)
        """
        params = [
            (
                r["stock_code"], r["trade_date"],
                r.get("ma5"), r.get("ma10"), r.get("ma20"), r.get("ma60"),
                r.get("macd_dif"), r.get("macd_dea"), r.get("macd_bar"),
                r.get("kdj_k"), r.get("kdj_d"), r.get("kdj_j"),
                r.get("rsi6"), r.get("rsi12"), r.get("rsi24"),
                r.get("boll_upper"), r.get("boll_middle"), r.get("boll_lower"),
            )
            for r in rows
        ]
        cursor.executemany(sql, params)
        conn.commit()
    finally:
        conn.close()


def query_latest_indicator_date(stock_code):
    """返回 indicators_daily 中该股票最新 trade_date，无记录返回 None"""
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MAX(trade_date) AS max_date "
            "FROM indicators_daily WHERE stock_code = %s",
            (stock_code,),
        )
        row = cursor.fetchone()
        return row["max_date"] if row and row["max_date"] else None
    finally:
        conn.close()


def query_indicators_range(stock_code, start_date=None, end_date=None, limit=None):
    """查询指标数据，按 trade_date 升序"""
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        conditions = ["stock_code = %s"]
        params = [stock_code]
        if start_date:
            conditions.append("trade_date >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("trade_date <= %s")
            params.append(end_date)

        where = " AND ".join(conditions)
        sql = f"SELECT * FROM indicators_daily WHERE {where} ORDER BY trade_date ASC"
        if limit:
            sql += f" LIMIT {int(limit)}"

        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        conn.close()


def query_kline_for_calc(stock_code, limit=120):
    """
    查询最近 N 条 K 线数据，用于技术指标计算。
    返回按 trade_date 升序排列的列表。
    """
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT stock_code, trade_date, `open`, high, low, `close`, volume, amount "
            "FROM stock_data_daily WHERE stock_code = %s "
            "ORDER BY trade_date ASC LIMIT %s",
            (stock_code, limit),
        )
        return cursor.fetchall()
    finally:
        conn.close()


def count_tracked_stocks():
    """返回 tracked_stock 表中的股票数量"""
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM tracked_stock")
        row = cursor.fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()
