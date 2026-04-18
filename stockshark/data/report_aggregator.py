"""研报聚合器 - 聚合洞见研报 + 慧博投研 + 巨潮公告，按股票统一查询

优化: 内存缓存(TTL 1周) + 三源并行查询
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List

from stockshark.data.research_report import get_reports as djyanbao_search
from stockshark.data.hibor_report import get_hibor_reports
from stockshark.data.announcement import get_announcements

logger = logging.getLogger(__name__)

# 缓存: key -> {"data": ..., "ts": timestamp}
_cache: Dict[str, dict] = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 7 * 24 * 3600  # 1周


def _cache_key(stock_code: str, stock_name: str, days: int) -> str:
    return f"{stock_code}|{stock_name}|{days}"


def _get_cached(key: str):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and time.time() - entry["ts"] < _CACHE_TTL:
            return entry["data"]
        if entry:
            del _cache[key]
    return None


def _set_cache(key: str, data: dict):
    with _cache_lock:
        _cache[key] = {"data": data, "ts": time.time()}


def _fetch_djyanbao(keyword: str, cutoff: str) -> List[Dict]:
    """洞见研报"""
    try:
        dj = djyanbao_search(keyword, limit=30)
        return [
            {
                "title": r["title"], "org": r.get("org", ""),
                "date": r.get("date", ""), "summary": r["title"],
                "detail_url": r.get("detail_url", ""),
                "source": "djyanbao", "category": r.get("category", ""),
            }
            for r in dj.get("reports", []) if r.get("date", "") >= cutoff
        ]
    except Exception as e:
        logger.warning("洞见研报查询失败: %s", e)
        return []


def _fetch_hibor(keyword: str, stock_code: str, stock_name: str, days: int) -> List[Dict]:
    """慧博投研（名称+代码双搜）"""
    reports = []
    seen = set()
    for kw in dict.fromkeys([keyword, stock_code]):  # 去重保序
        if not kw:
            continue
        try:
            hb = get_hibor_reports(kw, days=days, max_pages=2)
            for r in hb.get("reports", []):
                url = r.get("detail_url", "")
                if url in seen:
                    continue
                seen.add(url)
                reports.append({
                    "title": r["title"], "org": r.get("org", ""),
                    "date": r.get("date", ""), "summary": r.get("summary", r["title"]),
                    "detail_url": url, "source": "hibor", "category": "公司调研",
                })
        except Exception as e:
            logger.warning("慧博研报查询失败(%s): %s", kw, e)
    return reports


def _fetch_announcements(stock_code: str, days: int) -> List[Dict]:
    """巨潮公告"""
    try:
        ann = get_announcements(stock_code, days=days, page_size=20)
        return [
            {
                "title": a["title"], "date": a.get("date", ""),
                "detail_url": a.get("detail_url", ""), "source": "cninfo",
            }
            for a in ann.get("announcements", [])
        ]
    except Exception as e:
        logger.warning("巨潮公告查询失败: %s", e)
        return []


def get_stock_reports(
    stock_code: str,
    stock_name: str = "",
    days: int = 7,
) -> Dict:
    """获取指定股票研报（三源并行 + 1周缓存）"""
    key = _cache_key(stock_code, stock_name, days)
    cached = _get_cached(key)
    if cached:
        logger.info("缓存命中: %s", key)
        return cached

    keyword = stock_name or stock_code
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # 三源并行
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_dj = pool.submit(_fetch_djyanbao, keyword, cutoff)
        f_hb = pool.submit(_fetch_hibor, keyword, stock_code, stock_name, days)
        f_ann = pool.submit(_fetch_announcements, stock_code, days)

        dj_reports = f_dj.result(timeout=30)
        hb_reports = f_hb.result(timeout=30)
        announcements = f_ann.result(timeout=30)

    # 合并去重排序
    all_reports = dj_reports + hb_reports
    seen_urls = set()
    unique = []
    for r in all_reports:
        url = r.get("detail_url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        unique.append(r)
    unique.sort(key=lambda x: x.get("date", ""), reverse=True)

    src_count = {}
    for r in unique:
        s = r["source"]
        src_count[s] = src_count.get(s, 0) + 1

    result = {
        "stock_code": stock_code,
        "stock_name": stock_name,
        "period_days": days,
        "reports": unique,
        "announcements": announcements,
        "sources_summary": {
            "djyanbao": src_count.get("djyanbao", 0),
            "hibor": src_count.get("hibor", 0),
            "cninfo": len(announcements),
        },
    }

    _set_cache(key, result)
    return result
