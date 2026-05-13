"""K 线增量采集 — 读取关注列表，东财→Sina 降级，批量汇总"""

from datetime import datetime, timedelta

from stockshark.pipeline.kline_fetcher import (
    AkshareEastmoneyFetcher,
    AkshareSinaFetcher,
)
from stockshark.pipeline import tables
from stockshark.utils.database import get_mysql_connection
from stockshark.utils.logger import get_logger
from stockshark.config import Config

logger = get_logger(__name__)


class KLineCollector:
    """K 线增量采集器"""

    def __init__(self):
        self.em_fetcher = AkshareEastmoneyFetcher()
        self.sina_fetcher = AkshareSinaFetcher()

    # ------------------------------------------------------------------
    # 单只股票采集
    # ------------------------------------------------------------------

    def collect_one(self, stock_code):
        """
        对单只股票执行增量 K 线采集。

        Returns:
            dict: {"stock_code": ..., "success": bool, "rows": int,
                   "error": str|None}
        """
        try:
            latest = tables.query_latest_date(stock_code)
            end_date = datetime.now().strftime("%Y%m%d")

            if latest is None:
                # 首次采集：取近 N 个交易日
                start = datetime.now() - timedelta(days=Config.INITIAL_KLINE_DAYS)
                start_date = start.strftime("%Y%m%d")
            else:
                # 增量：从最新日期的下一天开始
                next_day = latest + timedelta(days=1)
                start_date = next_day.strftime("%Y%m%d")

            df = self._fetch_with_fallback(stock_code, start_date, end_date)

            if df is None or df.empty:
                return {
                    "stock_code": stock_code,
                    "success": True,
                    "rows": 0,
                    "error": None,
                }

            rows = self._df_to_rows(stock_code, df)
            tables.upsert_kline_rows(rows)

            return {
                "stock_code": stock_code,
                "success": True,
                "rows": len(rows),
                "error": None,
            }
        except Exception as e:
            logger.error("collect_one failed for %s: %s", stock_code, e)
            return {
                "stock_code": stock_code,
                "success": False,
                "rows": 0,
                "error": str(e),
            }

    # ------------------------------------------------------------------
    # 批量采集
    # ------------------------------------------------------------------

    def collect_all(self):
        """
        从 tracked_stock 表读取全部股票，依次执行增量采集。

        Returns:
            dict: {"total": int, "success": int, "failed": int,
                   "failed_codes": list[str]}
        """
        codes = self._get_tracked_codes()
        total = len(codes)
        success = 0
        failed_codes = []

        for code in codes:
            result = self.collect_one(code)
            if result["success"]:
                success += 1
            else:
                failed_codes.append(code)
                logger.warning("采集 %s 失败: %s", code, result.get("error"))

        return {
            "total": total,
            "success": success,
            "failed": len(failed_codes),
            "failed_codes": failed_codes,
        }

    # ------------------------------------------------------------------
    # 降级逻辑
    # ------------------------------------------------------------------

    def _fetch_with_fallback(self, stock_code, start_date, end_date):
        """
        先东财，失败则降级 Sina。

        Returns:
            pd.DataFrame 或 None
        """
        try:
            df = self.em_fetcher.fetch(stock_code, start_date, end_date)
            if df is not None and not df.empty:
                return df
        except Exception as em_err:
            logger.warning(
                "东财采集 %s 失败，尝试 Sina 降级: %s", stock_code, em_err
            )
            try:
                df = self.sina_fetcher.fetch(stock_code, start_date, end_date)
                if df is not None and not df.empty:
                    logger.warning("已降级到 Sina 数据源采集 %s", stock_code)
                    return df
            except Exception as sina_err:
                logger.error(
                    "Sina 采集 %s 也失败: %s", stock_code, sina_err
                )
                raise RuntimeError(
                    f"东财失败: {em_err}; Sina 失败: {sina_err}"
                )
        return None

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def _get_tracked_codes(self):
        """从 stock_basic 表获取全部股票代码（兼容 tracked_stock）"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT stock_code FROM tracked_stock")
            codes = [row["stock_code"] for row in cursor.fetchall()]
            if codes:
                return codes
            cursor.execute("SELECT code AS stock_code FROM stock_basic ORDER BY code")
            return [row["stock_code"] for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def _df_to_rows(stock_code, df):
        """DataFrame → list[dict] 用于 upsert"""
        rows = []
        for _, r in df.iterrows():
            rows.append({
                "stock_code": stock_code,
                "date": r["date"].date() if hasattr(r["date"], "date") else r["date"],
                "open": float(r["open"]) if _not_nan(r.get("open")) else None,
                "high": float(r["high"]) if _not_nan(r.get("high")) else None,
                "low": float(r["low"]) if _not_nan(r.get("low")) else None,
                "close": float(r["close"]) if _not_nan(r.get("close")) else None,
                "volume": int(r["volume"]) if _not_nan(r.get("volume")) else None,
                "turnover": None,
            })
        return rows


def _not_nan(val):
    if val is None:
        return False
    try:
        import math
        return not math.isnan(float(val))
    except (ValueError, TypeError):
        return True
