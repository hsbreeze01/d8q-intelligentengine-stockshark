"""研报聚合器 - 聚合洞见研报 + 慧博投研 + 巨潮公告，按股票统一查询

设计文档: docs/evaluation_cache_design.md
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

from stockshark.data.research_report import get_reports as djyanbao_search
from stockshark.data.hibor_report import get_hibor_reports
from stockshark.data.announcement import get_announcements

logger = logging.getLogger(__name__)


def get_stock_reports(
    stock_code: str,
    stock_name: str = "",
    days: int = 7,
) -> Dict:
    """获取指定股票在过去一个周期内的研报分析（三源聚合）

    Args:
        stock_code: 股票代码
        stock_name: 股票名称（可选，提高匹配率）
        days: 查询天数，默认7天

    Returns:
        {
            "stock_code", "stock_name", "period_days",
            "reports": [{"title","org","date","summary","detail_url","source"}, ...],
            "announcements": [{"title","date","detail_url","source"}, ...],
            "sources_summary": {"djyanbao": n, "hibor": n, "cninfo": n}
        }
    """
    keyword = stock_name or stock_code
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    reports: List[Dict] = []

    # 1. 洞见研报
    try:
        dj = djyanbao_search(keyword, limit=30)
        for r in dj.get("reports", []):
            if r.get("date", "") >= cutoff:
                reports.append({
                    "title": r["title"],
                    "org": r.get("org", ""),
                    "date": r.get("date", ""),
                    "summary": r["title"],
                    "detail_url": r.get("detail_url", ""),
                    "source": "djyanbao",
                    "category": r.get("category", ""),
                })
    except Exception as e:
        logger.warning("洞见研报查询失败: %s", e)

    # 2. 慧博投研
    try:
        hb = get_hibor_reports(keyword, days=days, max_pages=2)
        for r in hb.get("reports", []):
            reports.append({
                "title": r["title"],
                "org": r.get("org", ""),
                "date": r.get("date", ""),
                "summary": r.get("summary", r["title"]),
                "detail_url": r.get("detail_url", ""),
                "source": "hibor",
                "category": "公司调研",
            })
    except Exception as e:
        logger.warning("慧博研报查询失败: %s", e)

    # 也用股票代码搜慧博（名称和代码都试）
    if stock_name and stock_name != stock_code:
        try:
            hb2 = get_hibor_reports(stock_code, days=days, max_pages=2)
            seen = {r["detail_url"] for r in reports}
            for r in hb2.get("reports", []):
                if r.get("detail_url") not in seen:
                    reports.append({
                        "title": r["title"],
                        "org": r.get("org", ""),
                        "date": r.get("date", ""),
                        "summary": r.get("summary", r["title"]),
                        "detail_url": r.get("detail_url", ""),
                        "source": "hibor",
                        "category": "公司调研",
                    })
        except Exception as e:
            logger.debug("慧博代码搜索失败: %s", e)

    # 3. 巨潮公告
    announcements = []
    try:
        ann = get_announcements(stock_code, days=days, page_size=20)
        for a in ann.get("announcements", []):
            announcements.append({
                "title": a["title"],
                "date": a.get("date", ""),
                "detail_url": a.get("detail_url", ""),
                "source": "cninfo",
            })
    except Exception as e:
        logger.warning("巨潮公告查询失败: %s", e)

    # 去重 + 按日期排序
    seen_urls = set()
    unique_reports = []
    for r in reports:
        url = r.get("detail_url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        unique_reports.append(r)
    unique_reports.sort(key=lambda x: x.get("date", ""), reverse=True)

    # 统计
    src_count = {}
    for r in unique_reports:
        s = r["source"]
        src_count[s] = src_count.get(s, 0) + 1

    return {
        "stock_code": stock_code,
        "stock_name": stock_name,
        "period_days": days,
        "reports": unique_reports,
        "announcements": announcements,
        "sources_summary": {
            "djyanbao": src_count.get("djyanbao", 0),
            "hibor": src_count.get("hibor", 0),
            "cninfo": len(announcements),
        },
    }
