"""回测引擎 — 基于历史指标数据模拟策略信号并计算收益

核心流程：
1. 从 indicators_daily + stock_data_daily 加载历史数据
2. 加载大盘指数数据（index_daily）作为基准
3. 按日期遍历，应用策略条件生成买卖信号
4. 模拟持仓，计算收益曲线和统计指标
5. 计算超额收益、Alpha、Beta 等相对基准指标

数据源：共享 DB（stock_analysis_system），与 Compass 共用
"""

import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any

from stockshark.utils.database import get_mysql_connection

logger = logging.getLogger(__name__)

# 指数代码 → 名称映射
INDEX_NAMES = {
    "000300": "沪深300",
    "000001": "上证指数",
    "399006": "创业板指",
    "399001": "深证成指",
    "000905": "中证500",
}


class BacktestEngine:
    """历史回测引擎（含大盘基准对比）"""

    def __init__(self):
        self._indicator_cache: Dict[str, List[dict]] = {}
        self._price_cache: Dict[str, List[dict]] = {}
        self._index_cache: Dict[str, Dict[str, float]] = {}  # {code: {date: close}}

    # ------------------------------------------------------------------
    # 核心回测
    # ------------------------------------------------------------------

    def run(self, config: dict) -> dict:
        """执行回测

        Args:
            config: 回测配置
                {
                    "name": "策略名称",
                    "start_date": "2024-01-01",
                    "end_date": "2026-05-27",
                    "initial_capital": 1000000,
                    "max_positions": 10,
                    "position_size_pct": 0.10,
                    "entry_conditions": [...],
                    "exit_conditions": [...],
                    "signal_logic": "AND",
                    "scoring_threshold": 2,
                    "stop_loss_pct": -0.08,
                    "take_profit_pct": 0.20,
                    "max_holding_days": 20,
                    "stock_pool": [],
                    "benchmark": "000300"     ← 新增：大盘基准指数代码
                }

        Returns:
            回测结果 dict
        """
        name = config.get("name", "unnamed")
        start_date = config.get("start_date", "2024-01-01")
        end_date = config.get("end_date", "2026-05-27")
        initial_capital = config.get("initial_capital", 1000000)
        max_positions = config.get("max_positions", 10)
        position_size_pct = config.get("position_size_pct", 0.10)
        entry_conditions = config.get("entry_conditions", [])
        exit_conditions = config.get("exit_conditions", [])
        signal_logic = config.get("signal_logic", "AND")
        scoring_threshold = config.get("scoring_threshold")
        stop_loss_pct = config.get("stop_loss_pct", -0.08)
        take_profit_pct = config.get("take_profit_pct", 0.20)
        max_holding_days = config.get("max_holding_days", 20)
        stock_pool = config.get("stock_pool", [])
        benchmark = config.get("benchmark", "000300")

        logger.info("回测开始: %s (%s ~ %s), 基准: %s", name, start_date, end_date, benchmark)

        # 1. 确定股票池
        if not stock_pool:
            stock_pool = self._get_stock_pool(start_date)
        logger.info("股票池: %d 只", len(stock_pool))

        # 2. 加载历史数据
        self._load_data(stock_pool, start_date, end_date)

        # 3. 加载大盘基准
        self._load_index(benchmark, start_date, end_date)

        # 4. 获取交易日历
        trade_dates = self._get_trade_dates(start_date, end_date)
        if not trade_dates:
            return {"error": "无交易日期数据"}

        # 5. 模拟交易
        capital = float(initial_capital)
        positions: Dict[str, dict] = {}
        trades: List[dict] = []
        equity_curve: List[dict] = []
        benchmark_curve: List[dict] = []

        # 基准起始价
        benchmark_start_price = self._get_index_price(benchmark, str(trade_dates[0]))
        benchmark_init_capital = float(initial_capital)  # 虚拟：同样资金买入基准

        for td in trade_dates:
            td_str = str(td)

            # a. 检查退出条件（先卖后买）
            exits_today = []
            for code, pos in list(positions.items()):
                should_exit = False
                exit_reason = ""

                cur_price = self._get_price(code, td_str)
                if cur_price and pos["entry_price"] > 0:
                    pnl_pct = (cur_price - pos["entry_price"]) / pos["entry_price"]
                    if stop_loss_pct and pnl_pct <= stop_loss_pct:
                        should_exit = True
                        exit_reason = f"止损({pnl_pct:.1%})"
                    if take_profit_pct and pnl_pct >= take_profit_pct:
                        should_exit = True
                        exit_reason = f"止盈({pnl_pct:.1%})"

                holding_days = self._calc_days(pos["entry_date"], td_str)
                if max_holding_days and holding_days >= max_holding_days:
                    should_exit = True
                    exit_reason = f"持仓{holding_days}天到期"

                if exit_conditions:
                    ind = self._get_indicators(code, td_str)
                    if ind and self._match_conditions(ind, exit_conditions, signal_logic, scoring_threshold):
                        should_exit = True
                        exit_reason = "信号退出"

                if should_exit:
                    exits_today.append((code, exit_reason, cur_price))

            # 执行卖出
            for code, reason, price in exits_today:
                if code in positions:
                    pos = positions.pop(code)
                    sell_price = price or pos["entry_price"]
                    proceeds = sell_price * pos["shares"]
                    pnl = (sell_price - pos["entry_price"]) * pos["shares"]
                    pnl_pct = (sell_price - pos["entry_price"]) / pos["entry_price"] if pos["entry_price"] > 0 else 0
                    capital += proceeds
                    trades.append({
                        "stock_code": code,
                        "action": "sell",
                        "date": td_str,
                        "price": round(sell_price, 2),
                        "shares": pos["shares"],
                        "pnl": round(pnl, 2),
                        "pnl_pct": round(pnl_pct, 4),
                        "reason": reason,
                        "holding_days": self._calc_days(pos["entry_date"], td_str),
                    })

            # b. 检查买入条件
            if len(positions) < max_positions and entry_conditions:
                candidates = []
                for code in stock_pool:
                    if code in positions:
                        continue
                    ind = self._get_indicators(code, td_str)
                    if ind and self._match_conditions(ind, entry_conditions, signal_logic, scoring_threshold):
                        price = self._get_price(code, td_str)
                        if price and price > 0:
                            candidates.append({"code": code, "price": price, "indicators": ind})

                candidates.sort(key=lambda x: x["indicators"].get("rsi_6", 50))
                available_slots = max_positions - len(positions)
                for c in candidates[:available_slots]:
                    code = c["code"]
                    price = c["price"]
                    position_value = capital * position_size_pct
                    shares = int(position_value / price)
                    if shares > 0 and capital >= shares * price:
                        cost = shares * price
                        capital -= cost
                        positions[code] = {
                            "entry_price": price,
                            "entry_date": td_str,
                            "shares": shares,
                        }
                        trades.append({
                            "stock_code": code,
                            "action": "buy",
                            "date": td_str,
                            "price": round(price, 2),
                            "shares": shares,
                            "pnl": 0,
                            "pnl_pct": 0,
                            "reason": "信号买入",
                        })

            # c. 记录权益曲线
            market_value = sum(
                pos["shares"] * (self._get_price(code, td_str) or pos["entry_price"])
                for code, pos in positions.items()
            )
            total_equity = capital + market_value
            equity_curve.append({
                "date": td_str,
                "equity": round(total_equity, 2),
                "capital": round(capital, 2),
                "market_value": round(market_value, 2),
                "positions": len(positions),
            })

            # d. 记录基准曲线
            idx_price = self._get_index_price(benchmark, td_str)
            if idx_price and benchmark_start_price and benchmark_start_price > 0:
                benchmark_equity = benchmark_init_capital * (idx_price / benchmark_start_price)
            else:
                benchmark_equity = benchmark_init_capital
            benchmark_curve.append({
                "date": td_str,
                "index_price": round(idx_price, 2) if idx_price else None,
                "benchmark_equity": round(benchmark_equity, 2),
            })

        # 6. 清算剩余持仓
        for code, pos in list(positions.items()):
            last_price = self._get_price(code, trade_dates[-1]) or pos["entry_price"]
            pnl = (last_price - pos["entry_price"]) * pos["shares"]
            capital += last_price * pos["shares"]
            trades.append({
                "stock_code": code,
                "action": "sell",
                "date": trade_dates[-1],
                "price": round(last_price, 2),
                "shares": pos["shares"],
                "pnl": round(pnl, 2),
                "pnl_pct": round((last_price - pos["entry_price"]) / pos["entry_price"], 4) if pos["entry_price"] > 0 else 0,
                "reason": "回测结束清算",
            })

        # 7. 计算统计指标（含基准对比）
        stats = self._calc_stats(equity_curve, benchmark_curve, trades, float(initial_capital))

        return {
            "name": name,
            "benchmark": benchmark,
            "benchmark_name": INDEX_NAMES.get(benchmark, benchmark),
            "config": config,
            "stats": stats,
            "trades": trades,
            "equity_curve": equity_curve,
            "benchmark_curve": benchmark_curve,
        }

    # ------------------------------------------------------------------
    # 条件匹配（复用 Scanner 逻辑）
    # ------------------------------------------------------------------

    def _match_conditions(self, indicator_values: dict, conditions: list,
                          signal_logic: str, scoring_threshold: Optional[int]) -> bool:
        if signal_logic == "AND":
            return all(self._eval_condition(indicator_values, c) for c in conditions)
        elif signal_logic == "OR":
            return any(self._eval_condition(indicator_values, c) for c in conditions)
        elif signal_logic == "SCORING":
            score = sum(1 for c in conditions if self._eval_condition(indicator_values, c))
            threshold = scoring_threshold or len(conditions)
            return score >= threshold
        return False

    @staticmethod
    def _eval_condition(indicator_values: dict, condition: dict) -> bool:
        indicator = condition.get("indicator", "")
        operator = condition.get("operator", "")
        threshold = condition.get("value")
        current = indicator_values.get(indicator)
        if current is None:
            return False
        try:
            current = float(current)
            threshold = float(threshold)
        except (TypeError, ValueError):
            return False
        if operator == ">":
            return current > threshold
        elif operator == "<":
            return current < threshold
        elif operator == ">=":
            return current >= threshold
        elif operator == "<=":
            return current <= threshold
        elif operator == "==":
            return abs(current - threshold) < 1e-9
        elif operator == "cross_above":
            return current > threshold
        elif operator == "cross_below":
            return current < threshold
        return False

    # ------------------------------------------------------------------
    # 统计计算（含基准对比）
    # ------------------------------------------------------------------

    @staticmethod
    def _calc_stats(equity_curve: list, benchmark_curve: list,
                    trades: list, initial_capital: float) -> dict:
        if not equity_curve:
            return {}

        final_equity = equity_curve[-1]["equity"]
        total_return = (final_equity - initial_capital) / initial_capital

        # 最大回撤
        peak = initial_capital
        max_drawdown = 0.0
        for ec in equity_curve:
            if ec["equity"] > peak:
                peak = ec["equity"]
            dd = (peak - ec["equity"]) / peak if peak > 0 else 0
            if dd > max_drawdown:
                max_drawdown = dd

        # 交易统计
        buy_trades = [t for t in trades if t["action"] == "buy"]
        sell_trades = [t for t in trades if t["action"] == "sell"]
        win_trades = [t for t in sell_trades if t["pnl"] > 0]
        lose_trades = [t for t in sell_trades if t["pnl"] < 0]
        total_pnl = sum(t["pnl"] for t in sell_trades)
        avg_pnl = total_pnl / len(sell_trades) if sell_trades else 0
        win_rate = len(win_trades) / len(sell_trades) if sell_trades else 0
        avg_holding = (sum(t.get("holding_days", 0) for t in sell_trades) / len(sell_trades)) if sell_trades else 0

        # 年化收益
        days = len(equity_curve)
        years = days / 252 if days > 0 else 1
        annualized_return = ((final_equity / initial_capital) ** (1 / years) - 1) if years > 0 else 0

        # Sharpe
        daily_returns = []
        for i in range(1, len(equity_curve)):
            prev = equity_curve[i - 1]["equity"]
            curr = equity_curve[i]["equity"]
            if prev > 0:
                daily_returns.append((curr - prev) / prev)
        avg_daily = sum(daily_returns) / len(daily_returns) if daily_returns else 0
        std_daily = (sum((r - avg_daily) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5 if len(daily_returns) > 1 else 0
        sharpe = (avg_daily / std_daily) * (252 ** 0.5) if std_daily > 0 else 0

        # ========== 基准对比 ==========
        benchmark_stats = {}
        if benchmark_curve:
            benchmark_final = benchmark_curve[-1]["benchmark_equity"]
            benchmark_return = (benchmark_final - initial_capital) / initial_capital if initial_capital > 0 else 0

            # 基准年化
            benchmark_annualized = ((benchmark_final / initial_capital) ** (1 / years) - 1) if years > 0 and initial_capital > 0 else 0

            # 基准最大回撤
            bm_peak = initial_capital
            bm_max_dd = 0.0
            for bc in benchmark_curve:
                if bc["benchmark_equity"] > bm_peak:
                    bm_peak = bc["benchmark_equity"]
                bm_dd = (bm_peak - bc["benchmark_equity"]) / bm_peak if bm_peak > 0 else 0
                if bm_dd > bm_max_dd:
                    bm_max_dd = bm_dd

            # 超额收益
            excess_return = total_return - benchmark_return
            excess_annualized = annualized_return - benchmark_annualized

            # Beta: cov(strategy, benchmark) / var(benchmark)
            benchmark_daily_returns = []
            for i in range(1, len(benchmark_curve)):
                prev = benchmark_curve[i - 1]["benchmark_equity"]
                curr = benchmark_curve[i]["benchmark_equity"]
                if prev > 0:
                    benchmark_daily_returns.append((curr - prev) / prev)

            # 对齐日收益序列
            min_len = min(len(daily_returns), len(benchmark_daily_returns))
            if min_len > 1:
                s_ret = daily_returns[:min_len]
                b_ret = benchmark_daily_returns[:min_len]

                avg_s = sum(s_ret) / min_len
                avg_b = sum(b_ret) / min_len
                cov_sb = sum((s - avg_s) * (b - avg_b) for s, b in zip(s_ret, b_ret)) / min_len
                var_b = sum((b - avg_b) ** 2 for b in b_ret) / min_len
                beta = cov_sb / var_b if var_b > 0 else 0

                # Alpha (Jensen's): 年化超额 = 年化策略 - [rf + beta * (年化基准 - rf)]
                # 简化 rf = 0
                alpha = annualized_return - beta * benchmark_annualized if beta else 0
            else:
                beta = 0
                alpha = 0

            # 信息比率
            excess_daily = [s - b for s, b in zip(daily_returns[:min_len], benchmark_daily_returns[:min_len])]
            avg_excess_daily = sum(excess_daily) / len(excess_daily) if excess_daily else 0
            std_excess = (sum((e - avg_excess_daily) ** 2 for e in excess_daily) / len(excess_daily)) ** 0.5 if len(excess_daily) > 1 else 0
            information_ratio = (avg_excess_daily / std_excess) * (252 ** 0.5) if std_excess > 0 else 0

            benchmark_stats = {
                "benchmark_return": round(benchmark_return, 4),
                "benchmark_annualized": round(benchmark_annualized, 4),
                "benchmark_max_drawdown": round(bm_max_dd, 4),
                "excess_return": round(excess_return, 4),
                "excess_annualized": round(excess_annualized, 4),
                "alpha": round(alpha, 4),
                "beta": round(beta, 4),
                "information_ratio": round(information_ratio, 2),
            }

        stats = {
            "initial_capital": initial_capital,
            "final_equity": round(final_equity, 2),
            "total_return": round(total_return, 4),
            "annualized_return": round(annualized_return, 4),
            "max_drawdown": round(max_drawdown, 4),
            "sharpe_ratio": round(sharpe, 2),
            "total_trades": len(buy_trades),
            "win_trades": len(win_trades),
            "lose_trades": len(lose_trades),
            "win_rate": round(win_rate, 4),
            "total_pnl": round(total_pnl, 2),
            "avg_pnl_per_trade": round(avg_pnl, 2),
            "avg_holding_days": round(avg_holding, 1),
            "trade_dates": len(equity_curve),
        }

        # 合并基准统计
        if benchmark_stats:
            stats.update(benchmark_stats)

        return stats

    # ------------------------------------------------------------------
    # 数据加载
    # ------------------------------------------------------------------

    def _get_stock_pool(self, start_date: str) -> list:
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT stock_code FROM indicators_daily WHERE date >= %s",
                (start_date,)
            )
            import random; codes=[r["stock_code"] for r in cursor.fetchall()]; return random.sample(codes, min(500, len(codes)))
        finally:
            conn.close()

    def _get_trade_dates(self, start_date: str, end_date: str) -> list:
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT date FROM indicators_daily "
                "WHERE date BETWEEN %s AND %s ORDER BY date",
                (start_date, end_date)
            )
            return [r["date"] for r in cursor.fetchall()]
        finally:
            conn.close()

    def _load_data(self, stock_pool: list, start_date: str, end_date: str):
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            for batch_start in range(0, len(stock_pool), 500):
                batch = stock_pool[batch_start:batch_start + 500]
                ph = ",".join(["%s"] * len(batch))
                cursor.execute(
                    f"SELECT stock_code, date, ma5, ma10, ma20, ma60, "
                    f"macd_dif, macd_dea, macd_macd, kdj_k, kdj_d, kdj_j, "
                    f"rsi_6, rsi_12, rsi_24, boll_up, boll_mid, boll_low, "
                    f"volume_ratio, amplitude, change_pct, turnover_rate "
                    f"FROM indicators_daily "
                    f"WHERE stock_code IN ({ph}) AND date BETWEEN %s AND %s "
                    f"ORDER BY stock_code, date",
                    tuple(batch) + (start_date, end_date)
                )
                for r in cursor.fetchall():
                    code = r["stock_code"]
                    if code not in self._indicator_cache:
                        self._indicator_cache[code] = {}
                    self._indicator_cache[code][str(r["date"])] = r

            for batch_start in range(0, len(stock_pool), 500):
                batch = stock_pool[batch_start:batch_start + 500]
                ph = ",".join(["%s"] * len(batch))
                cursor.execute(
                    f"SELECT stock_code, date, open, close, high, low, volume, "
                    f"change_percentage as change_pct "
                    f"FROM stock_data_daily "
                    f"WHERE stock_code IN ({ph}) AND date BETWEEN %s AND %s "
                    f"ORDER BY stock_code, date",
                    tuple(batch) + (start_date, end_date)
                )
                for r in cursor.fetchall():
                    code = r["stock_code"]
                    if code not in self._price_cache:
                        self._price_cache[code] = {}
                    self._price_cache[code][str(r["date"])] = r
        finally:
            conn.close()

        logger.info("个股数据加载: indicators=%d, prices=%d",
                     sum(len(v) for v in self._indicator_cache.values()),
                     sum(len(v) for v in self._price_cache.values()))

    def _load_index(self, index_code: str, start_date: str, end_date: str):
        """加载大盘指数数据"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT date, close FROM index_daily "
                "WHERE stock_code = %s AND date BETWEEN %s AND %s ORDER BY date",
                (index_code, start_date, end_date)
            )
            rows = cursor.fetchall()
            self._index_cache[index_code] = {str(r["date"]): float(r["close"]) for r in rows}
            logger.info("基准指数 %s 加载: %d 天", index_code, len(rows))
        finally:
            conn.close()

    def _get_indicators(self, code: str, date_str: str) -> Optional[dict]:
        return self._indicator_cache.get(code, {}).get(date_str)

    def _get_price(self, code: str, date_str: str) -> Optional[float]:
        row = self._price_cache.get(code, {}).get(date_str)
        if row and row.get("close"):
            return float(row["close"])
        return None

    def _get_index_price(self, index_code: str, date_str: str) -> Optional[float]:
        return self._index_cache.get(index_code, {}).get(date_str)

    @staticmethod
    def _calc_days(d1: str, d2: str) -> int:
        try:
            if isinstance(d1, (date, datetime)):
                d1 = str(d1)
            if isinstance(d2, (date, datetime)):
                d2 = str(d2)
            dt1 = datetime.strptime(d1[:10], "%Y-%m-%d")
            dt2 = datetime.strptime(d2[:10], "%Y-%m-%d")
            return (dt2 - dt1).days
        except Exception:
            return 0
