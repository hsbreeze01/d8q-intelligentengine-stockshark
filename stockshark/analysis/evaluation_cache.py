"""股票评估结论缓存与智能重新评估触发检测

设计文档: docs/evaluation_cache_design.md
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from stockshark.data.database import DatabaseManager

logger = logging.getLogger(__name__)

# 重大公告关键词
_MAJOR_KEYWORDS = (
    "重组", "并购", "增持", "减持", "业绩预告", "业绩快报",
    "停牌", "复牌", "分红", "回购", "诉讼", "处罚",
    "定增", "配股", "可转债", "股权激励", "解禁",
)

# scope -> 过期天数
_EXPIRY_DAYS = {"short": 3, "mid": 7, "long": 30, "all": 7}

# 触发阈值
PRICE_CHANGE_THRESHOLD = 0.08      # 相对缓存价格变化 8%
DAILY_CHANGE_THRESHOLD = 5.0       # 日涨跌幅 5%
VALUATION_CHANGE_THRESHOLD = 0.15  # PE/PB 变化 15%


def _get_collection():
    """获取 stock_evaluations 集合"""
    db = DatabaseManager.get_mongodb_connection()
    if db is None:
        return None
    return db["stock_evaluations"]


def get_cached_evaluation(stock_code: str, scope: str) -> Optional[Dict]:
    """查询缓存的评估结论"""
    coll = _get_collection()
    if coll is None:
        return None
    return coll.find_one(
        {"stock_code": stock_code, "scope": scope},
        {"_id": 0},
    )


def save_evaluation(stock_code: str, scope: str, result: Dict,
                    fingerprint: Dict, trigger_reason: str):
    """保存评估结论（upsert）"""
    coll = _get_collection()
    if coll is None:
        logger.warning("MongoDB 不可用，评估结论未持久化")
        return
    doc = {
        "stock_code": stock_code,
        "scope": scope,
        "result": result,
        "data_fingerprint": fingerprint,
        "evaluated_at": datetime.now().isoformat(),
        "trigger_reason": trigger_reason,
    }
    coll.update_one(
        {"stock_code": stock_code, "scope": scope},
        {"$set": doc},
        upsert=True,
    )
    logger.info("评估结论已保存: %s scope=%s reason=%s",
                stock_code, scope, trigger_reason)


def build_fingerprint(quote: Dict, valuation: Dict,
                      announcements: list, reports: list) -> Dict:
    """从采集数据中提取关键指纹"""
    fp: Dict[str, Any] = {}
    if quote and "error" not in str(quote):
        fp["price"] = quote.get("最新价") or quote.get("price")
        fp["change_pct"] = quote.get("涨跌幅") or quote.get("change_pct")
    if valuation and "error" not in str(valuation):
        fp["pe_ttm"] = valuation.get("pe_ttm")
        fp["pb"] = valuation.get("pb")
    if announcements:
        fp["announcement_count"] = len(announcements)
        fp["latest_announcement_date"] = announcements[0].get("date", "") if announcements else ""
    if reports:
        fp["report_count"] = len(reports)
        fp["latest_report_date"] = reports[0].get("date", "") if reports else ""
    return fp


def check_triggers(cached: Dict, stock_code: str) -> Tuple[bool, str]:
    """轻量级触发检测，返回 (should_refresh, reason)

    只做必要的数据获取，不调用 LLM。
    """
    evaluated_at = cached.get("evaluated_at", "")
    scope = cached.get("scope", "all")
    old_fp = cached.get("data_fingerprint", {})

    # 1. 时间过期
    try:
        eval_time = datetime.fromisoformat(evaluated_at)
        expiry = timedelta(days=_EXPIRY_DAYS.get(scope, 7))
        if datetime.now() - eval_time > expiry:
            return True, "time_expired"
    except (ValueError, TypeError):
        return True, "invalid_eval_time"

    # 2. 行情变化（价格 + 日涨跌幅）
    try:
        from stockshark.data.akshare_data import AkShareData
        ak = AkShareData()
        quote = ak.get_stock_quote(stock_code)
        if quote:
            cur_price = float(quote.get("最新价") or quote.get("price") or 0)
            old_price = float(old_fp.get("price") or 0)
            if old_price > 0 and cur_price > 0:
                if abs(cur_price - old_price) / old_price >= PRICE_CHANGE_THRESHOLD:
                    return True, f"price_change({old_price}->{cur_price})"

            daily_chg = float(quote.get("涨跌幅") or quote.get("change_pct") or 0)
            if abs(daily_chg) >= DAILY_CHANGE_THRESHOLD:
                return True, f"daily_volatility({daily_chg}%)"
    except Exception as e:
        logger.debug("行情触发检测异常: %s", e)

    # 3. 重大公告
    try:
        from stockshark.data.announcement import get_announcements
        ann = get_announcements(stock_code, days=7, page_size=10)
        new_anns = ann.get("announcements", [])
        old_latest = old_fp.get("latest_announcement_date", "")
        for a in new_anns:
            if a["date"] > old_latest:
                if any(kw in a["title"] for kw in _MAJOR_KEYWORDS):
                    return True, f"major_announcement({a['title'][:30]})"
    except Exception as e:
        logger.debug("公告触发检测异常: %s", e)

    # 4. 新研报
    try:
        from stockshark.data.research_report import get_reports
        old_report_date = old_fp.get("latest_report_date", "")
        if old_report_date:
            keyword = cached.get("result", {}).get("stock_name", stock_code)
            rpt = get_reports(keyword, limit=5)
            for r in rpt.get("reports", []):
                if r["date"] > old_report_date:
                    return True, f"new_report({r['title'][:30]})"
    except Exception as e:
        logger.debug("研报触发检测异常: %s", e)

    # 5. 估值异动
    try:
        valuation = ak.get_stock_valuation_data(stock_code) if 'ak' in dir() else None
        if valuation and "error" not in str(valuation):
            for key in ("pe_ttm", "pb"):
                cur_val = float(valuation.get(key) or 0)
                old_val = float(old_fp.get(key) or 0)
                if old_val > 0 and cur_val > 0:
                    if abs(cur_val - old_val) / old_val >= VALUATION_CHANGE_THRESHOLD:
                        return True, f"valuation_change({key}: {old_val}->{cur_val})"
    except Exception as e:
        logger.debug("估值触发检测异常: %s", e)

    return False, ""


def ensure_index():
    """确保 MongoDB 索引存在"""
    coll = _get_collection()
    if coll is not None:
        coll.create_index(
            [("stock_code", 1), ("scope", 1)],
            unique=True,
            name="idx_stock_scope",
        )
