"""技术指标计算 — 基于 pandas-ta"""

import pandas as pd
from stockshark.pipeline import tables
from stockshark.utils.logger import get_logger

logger = get_logger(__name__)

# 计算指标所需的最少 K 线条数（BOLL 60 + 几余）
MIN_ROWS_FOR_FULL = 65


class IndicatorCalculator:
    """技术指标计算器"""

    def calculate_one(self, stock_code, force_recalculate=False):
        """
        对单只股票执行增量指标计算。

        策略：读取最近 ~120 条 K 线（用于提供足够的窗口），
        默认只将 indicators_daily 中不存在的日期行写入；
        force_recalculate=True 时重算最近窗口并通过 upsert 回填已有行。

        Returns:
            dict: {"stock_code": str, "success": bool,
                   "rows": int, "error": str|None}
        """
        try:
            klines = tables.query_kline_for_calc(stock_code, limit=120)

            if not klines:
                logger.warning("股票 %s 无 K 线数据，跳过指标计算", stock_code)
                return {
                    "stock_code": stock_code,
                    "success": True,
                    "rows": 0,
                    "error": None,
                }

            df = pd.DataFrame(klines)
            df["date"] = pd.to_datetime(df["date"])
            for col in [
                "open", "high", "low", "close", "volume",
                "amplitude", "change_percentage", "turnover_rate",
            ]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.sort_values("date").reset_index(drop=True)

            # 确定已计算到的最新日期
            latest_indicator = tables.query_latest_indicator_date(stock_code)

            # 计算指标
            indicators_df = self._compute(df)

            if indicators_df is None or indicators_df.empty:
                return {
                    "stock_code": stock_code,
                    "success": True,
                    "rows": 0,
                    "error": None,
                }

            # 增量过滤：只保留 latest_indicator 之后的新日期
            if latest_indicator is not None and not force_recalculate:
                latest_ts = pd.Timestamp(latest_indicator)
                indicators_df = indicators_df[
                    indicators_df["date"] > latest_ts
                ]

            if indicators_df.empty:
                return {
                    "stock_code": stock_code,
                    "success": True,
                    "rows": 0,
                    "error": None,
                }

            rows = self._df_to_rows(stock_code, indicators_df)
            tables.upsert_indicator_rows(rows)

            return {
                "stock_code": stock_code,
                "success": True,
                "rows": len(rows),
                "error": None,
            }
        except Exception as e:
            logger.error("calculate_one failed for %s: %s", stock_code, e)
            return {
                "stock_code": stock_code,
                "success": False,
                "rows": 0,
                "error": str(e),
            }

    def calculate_all(self, force_recalculate=False):
        """
        对 tracked_stock 全部股票执行增量指标计算。

        Returns:
            dict: {"total": int, "success": int, "failed": int,
                   "failed_codes": list}
        """
        codes = self._get_tracked_codes()
        total = len(codes)
        success = 0
        failed_codes = []

        for code in codes:
            result = self.calculate_one(code, force_recalculate=force_recalculate)
            if result["success"]:
                success += 1
            else:
                failed_codes.append(code)

        return {
            "total": total,
            "success": success,
            "failed": len(failed_codes),
            "failed_codes": failed_codes,
        }

    # ------------------------------------------------------------------
    # 指标计算核心
    # ------------------------------------------------------------------

    def _compute(self, df):
        """
        对 DataFrame 计算 MA/MACD/KDJ/RSI/BOLL。
        数据不足时降级（跳过需要长窗口的指标）。

        Args:
            df: DataFrame, 必须有 date, close, high, low, volume

        Returns:
            DataFrame with indicator columns, 或 None
        """
        n = len(df)
        result = pd.DataFrame()
        result["date"] = df["date"]
        result["stock_code"] = df.get("stock_code", "")
        result["close"] = df["close"]

        skipped = []

        # MA
        for period in [5, 10, 20, 30, 60]:
            if n >= period:
                result[f"ma{period}"] = df["close"].rolling(window=period).mean()
            else:
                result[f"ma{period}"] = None
                if period >= 20:
                    skipped.append(f"MA{period}")

        # MACD
        try:
            macd_df = self._calc_macd(df["close"])
            result = pd.concat([result, macd_df], axis=1)
        except Exception as e:
            logger.warning("MACD 计算失败: %s", e)
            result["macd_dif"] = None
            result["macd_dea"] = None
            result["macd_macd"] = None

        # KDJ
        try:
            kdj_df = self._calc_kdj(df)
            result = pd.concat([result, kdj_df], axis=1)
        except Exception as e:
            logger.warning("KDJ 计算失败: %s", e)
            result["kdj_k"] = None
            result["kdj_d"] = None
            result["kdj_j"] = None

        # RSI
        for period in [6, 12, 24]:
            try:
                result[f"rsi_{period}"] = self._calc_rsi(df["close"], period)
            except Exception:
                result[f"rsi_{period}"] = None

        # stock2 策略依赖的行情派生字段。
        # volume_ratio 使用前 5 日均量作为基准，避免把当日成交量纳入分母。
        prev_close = df["close"].shift(1)
        prev_volume_avg = df["volume"].shift(1).rolling(window=5).mean()
        result["volume_ratio"] = df["volume"] / prev_volume_avg
        if "amplitude" in df.columns:
            result["amplitude"] = df["amplitude"]
        else:
            result["amplitude"] = (df["high"] - df["low"]) / prev_close * 100
        if "change_percentage" in df.columns:
            result["change_pct"] = df["change_percentage"]
        else:
            result["change_pct"] = df["close"].pct_change() * 100
        if "turnover_rate" in df.columns:
            result["turnover_rate"] = df["turnover_rate"]
        else:
            result["turnover_rate"] = None

        # BOLL
        if n >= 20:
            try:
                boll_df = self._calc_boll(df["close"])
                result = pd.concat([result, boll_df], axis=1)
            except Exception as e:
                logger.warning("BOLL 计算失败: %s", e)
                result["boll_up"] = None
                result["boll_mid"] = None
                result["boll_low"] = None
        else:
            skipped.append("BOLL")
            result["boll_up"] = None
            result["boll_mid"] = None
            result["boll_low"] = None

        if skipped:
            logger.warning(
                "数据不足(%d条)，跳过指标: %s", n, ", ".join(skipped)
            )

        return result

    # ------------------------------------------------------------------
    # 各指标计算
    # ------------------------------------------------------------------

    @staticmethod
    def _calc_macd(close, fast=12, slow=26, signal=9):
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal, adjust=False).mean()
        bar = (dif - dea) * 2
        return pd.DataFrame({
            "macd_dif": dif,
            "macd_dea": dea,
            "macd_macd": bar,
        })

    @staticmethod
    def _calc_kdj(df, n=9, m1=3, m2=3):
        low_n = df["low"].rolling(window=n).min()
        high_n = df["high"].rolling(window=n).max()
        rsv = (df["close"] - low_n) / (high_n - low_n) * 100
        k = rsv.ewm(com=m1 - 1, adjust=False).mean()
        d = k.ewm(com=m2 - 1, adjust=False).mean()
        j = 3 * k - 2 * d
        return pd.DataFrame({
            "kdj_k": k,
            "kdj_d": d,
            "kdj_j": j,
        })

    @staticmethod
    def _calc_rsi(close, period=14):
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def _calc_boll(close, period=20, std_dev=2):
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        return pd.DataFrame({
            "boll_up": upper,
            "boll_mid": middle,
            "boll_low": lower,
        })

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _get_tracked_codes():
        from stockshark.utils.database import get_mysql_connection

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
        rows = []
        for _, r in df.iterrows():
            rows.append({
                "stock_code": stock_code,
                "date": (
                    r["date"].date()
                    if hasattr(r["date"], "date")
                    else r["date"]
                ),
                "ma5": _safe(r.get("ma5")),
                "ma10": _safe(r.get("ma10")),
                "ma20": _safe(r.get("ma20")),
                "ma30": _safe(r.get("ma30")),
                "ma60": _safe(r.get("ma60")),
                "macd_dif": _safe(r.get("macd_dif")),
                "macd_dea": _safe(r.get("macd_dea")),
                "macd_macd": _safe(r.get("macd_macd")),
                "kdj_k": _safe(r.get("kdj_k")),
                "kdj_d": _safe(r.get("kdj_d")),
                "kdj_j": _safe(r.get("kdj_j")),
                "rsi_6": _safe(r.get("rsi_6")),
                "rsi_12": _safe(r.get("rsi_12")),
                "rsi_24": _safe(r.get("rsi_24")),
                "boll_up": _safe(r.get("boll_up")),
                "boll_mid": _safe(r.get("boll_mid")),
                "boll_low": _safe(r.get("boll_low")),
                "volume_ratio": _safe(r.get("volume_ratio")),
                "amplitude": _safe(r.get("amplitude")),
                "change_pct": _safe(r.get("change_pct")),
                "turnover_rate": _safe(r.get("turnover_rate")),
            })
        return rows


def _safe(val):
    if val is None:
        return None
    try:
        import math
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else round(f, 4)
    except (ValueError, TypeError):
        return None
