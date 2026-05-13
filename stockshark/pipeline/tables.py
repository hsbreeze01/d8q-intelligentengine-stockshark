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
    date DATE         NOT NULL COMMENT '交易日期',
    `open`    DECIMAL(10,3) DEFAULT NULL COMMENT '开盘价',
    high      DECIMAL(10,3) DEFAULT NULL COMMENT '最高价',
    low       DECIMAL(10,3) DEFAULT NULL COMMENT '最低价',
    `close`   DECIMAL(10,3) DEFAULT NULL COMMENT '收盘价',
    volume    BIGINT        DEFAULT NULL COMMENT '成交量',
    amount    DECIMAL(20,3) DEFAULT NULL COMMENT '成交额',
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_code_date (stock_code, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='日K线数据表'
"""

INDICATORS_DAILY_DDL = """
CREATE TABLE IF NOT EXISTS indicators_daily (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    stock_code   VARCHAR(10)  NOT NULL,
    date   DATE         NOT NULL,
    ma5          DECIMAL(10,3) DEFAULT NULL,
    ma10         DECIMAL(10,3) DEFAULT NULL,
    ma20         DECIMAL(10,3) DEFAULT NULL,
    ma30         DECIMAL(10,3) DEFAULT NULL,
    ma60         DECIMAL(10,3) DEFAULT NULL,
    macd_dif     DECIMAL(10,4) DEFAULT NULL,
    macd_dea     DECIMAL(10,4) DEFAULT NULL,
    macd_macd     DECIMAL(10,4) DEFAULT NULL,
    kdj_k        DECIMAL(10,3) DEFAULT NULL,
    kdj_d        DECIMAL(10,3) DEFAULT NULL,
    kdj_j        DECIMAL(10,3) DEFAULT NULL,
    rsi_6         DECIMAL(10,3) DEFAULT NULL,
    rsi_12        DECIMAL(10,3) DEFAULT NULL,
    rsi_24        DECIMAL(10,3) DEFAULT NULL,
    boll_up   DECIMAL(10,3) DEFAULT NULL,
    boll_mid  DECIMAL(10,3) DEFAULT NULL,
    boll_low   DECIMAL(10,3) DEFAULT NULL,
    created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_code_date (stock_code, date)
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
              stock_code, date, open, high, low, close, volume, amount
    """
    if not rows:
        return
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        sql = """
        INSERT INTO stock_data_daily
            (stock_code, date, `open`, high, low, `close`, volume, turnover)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            `open`=VALUES(`open`), high=VALUES(high), low=VALUES(low),
            `close`=VALUES(`close`), volume=VALUES(volume), turnover=VALUES(turnover)
        """
        params = [
            (
                r["stock_code"], r["date"],
                r.get("open"), r.get("high"), r.get("low"), r.get("close"),
                r.get("volume"), r.get("turnover"),
            )
            for r in rows
        ]
        cursor.executemany(sql, params)
        conn.commit()
    finally:
        conn.close()


def query_latest_date(stock_code):
    """
    返回 stock_data_daily 中该股票最新 date（date 对象），
    无记录时返回 None。
    """
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MAX(date) AS max_date "
            "FROM stock_data_daily WHERE stock_code = %s",
            (stock_code,),
        )
        row = cursor.fetchone()
        return row["max_date"] if row and row["max_date"] else None
    finally:
        conn.close()


def query_kline_range(stock_code, start_date=None, end_date=None, limit=None):
    """
    查询 K 线数据，按 date 升序。

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
            conditions.append("date >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("date <= %s")
            params.append(end_date)

        where = " AND ".join(conditions)
        sql = f"SELECT * FROM stock_data_daily WHERE {where} ORDER BY date ASC"
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
            (stock_code, date,
             ma5, ma10, ma20, ma30, ma60,
             macd_dif, macd_dea, macd_macd,
             kdj_k, kdj_d, kdj_j,
             rsi_6, rsi_12, rsi_24,
             boll_up, boll_mid, boll_low)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            ma5=VALUES(ma5), ma10=VALUES(ma10), ma20=VALUES(ma20), ma30=VALUES(ma30), ma60=VALUES(ma60),
            macd_dif=VALUES(macd_dif), macd_dea=VALUES(macd_dea), macd_macd=VALUES(macd_macd),
            kdj_k=VALUES(kdj_k), kdj_d=VALUES(kdj_d), kdj_j=VALUES(kdj_j),
            rsi_6=VALUES(rsi_6), rsi_12=VALUES(rsi_12), rsi_24=VALUES(rsi_24),
            boll_up=VALUES(boll_up), boll_mid=VALUES(boll_mid),
            boll_low=VALUES(boll_low)
        """
        params = [
            (
                r["stock_code"], r["date"],
                r.get("ma5"), r.get("ma10"), r.get("ma20"), r.get("ma30"), r.get("ma60"),
                r.get("macd_dif"), r.get("macd_dea"), r.get("macd_macd"),
                r.get("kdj_k"), r.get("kdj_d"), r.get("kdj_j"),
                r.get("rsi_6"), r.get("rsi_12"), r.get("rsi_24"),
                r.get("boll_up"), r.get("boll_mid"), r.get("boll_low"),
            )
            for r in rows
        ]
        cursor.executemany(sql, params)
        conn.commit()
    finally:
        conn.close()


def query_latest_indicator_date(stock_code):
    """返回 indicators_daily 中该股票最新 date，无记录返回 None"""
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MAX(date) AS max_date "
            "FROM indicators_daily WHERE stock_code = %s",
            (stock_code,),
        )
        row = cursor.fetchone()
        return row["max_date"] if row and row["max_date"] else None
    finally:
        conn.close()


def query_indicators_range(stock_code, start_date=None, end_date=None, limit=None):
    """查询指标数据，按 date 升序"""
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        conditions = ["stock_code = %s"]
        params = [stock_code]
        if start_date:
            conditions.append("date >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("date <= %s")
            params.append(end_date)

        where = " AND ".join(conditions)
        sql = f"SELECT * FROM indicators_daily WHERE {where} ORDER BY date ASC"
        if limit:
            sql += f" LIMIT {int(limit)}"

        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        conn.close()


def query_kline_for_calc(stock_code, limit=120):
    """
    查询最近 N 条 K 线数据，用于技术指标计算。
    返回按 date 升序排列的列表。
    """
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT stock_code, date, `open`, high, low, `close`, volume "
            "FROM stock_data_daily WHERE stock_code = %s "
            "ORDER BY date ASC LIMIT %s",
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
