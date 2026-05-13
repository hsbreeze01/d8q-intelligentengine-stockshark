"""K 线数据源抽象 — 东财 + Sina 策略模式"""

import pandas as pd
from stockshark.utils.logger import get_logger

logger = get_logger(__name__)


class KLineFetcherBase:
    """K 线数据源基类"""

    def fetch(self, symbol, start_date=None, end_date=None):
        """
        获取 K 线数据

        Args:
            symbol: 纯数字股票代码，如 '600000'
            start_date: 起始日期 'YYYYMMDD'（可选）
            end_date: 结束日期 'YYYYMMDD'（可选）

        Returns:
            pd.DataFrame with columns: date, open, high, low, close, volume
        """
        raise NotImplementedError


class AkshareEastmoneyFetcher(KLineFetcherBase):
    """东财数据源 — 封装 stock_zh_a_hist"""

    def fetch(self, symbol, start_date=None, end_date=None):
        import akshare as ak

        ak_symbol = _to_ak_em_symbol(symbol)
        kwargs = dict(symbol=ak_symbol, period="daily", adjust="qfq")
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date

        df = ak.stock_zh_a_hist(**kwargs)
        if df is None or df.empty:
            return pd.DataFrame()

        return _normalize_em(df)


class AkshareSinaFetcher(KLineFetcherBase):
    """Sina 数据源 — 封装 stock_zh_a_daily"""

    def fetch(self, symbol, start_date=None, end_date=None):
        import akshare as ak

        ak_symbol = _to_ak_sina_symbol(symbol)
        kwargs = dict(symbol=ak_symbol, adjust="qfq")
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date

        df = ak.stock_zh_a_daily(**kwargs)
        if df is None or df.empty:
            return pd.DataFrame()

        return _normalize_sina(df)


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------


def _to_ak_em_symbol(symbol):
    """东财接口需要带市场前缀：sh600000, sz000001"""
    if symbol.startswith(("sh", "sz", "SH", "SZ")):
        return symbol.lower()
    if symbol.startswith(("6", "9")):
        return f"sh{symbol}"
    return f"sz{symbol}"


def _to_ak_sina_symbol(symbol):
    """Sina 接口同上"""
    return _to_ak_em_symbol(symbol)


def _normalize_em(df):
    """统一东财返回的 DataFrame 列名"""
    col_map = {
        "日期": "date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
    }
    df = df.rename(columns=col_map)
    keep = ["date", "open", "high", "low", "close", "volume"]
    for c in keep:
        if c not in df.columns:
            return pd.DataFrame()
    df = df[keep].copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def _normalize_sina(df):
    """统一 Sina 返回的 DataFrame 列名"""
    col_map = {
        "date": "date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    }
    df = df.rename(columns=col_map)
    keep = ["date", "open", "high", "low", "close", "volume"]
    for c in keep:
        if c not in df.columns:
            return pd.DataFrame()
    df = df[keep].copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df
