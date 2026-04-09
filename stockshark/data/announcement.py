"""巨潮资讯网公告数据获取"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.cninfo.com.cn/",
})

_CNINFO_BASE = "https://www.cninfo.com.cn"
_STATIC_BASE = "https://static.cninfo.com.cn/"

# orgId 缓存
_ORG_CACHE: Dict[str, str] = {}


def _resolve_org_id(stock_code: str) -> Optional[str]:
    """通过股票代码查询巨潮 orgId"""
    if stock_code in _ORG_CACHE:
        return _ORG_CACHE[stock_code]

    try:
        resp = _SESSION.get(
            f"{_CNINFO_BASE}/new/fulltextSearch/full",
            params={"searchkey": stock_code, "isfulltext": "false",
                    "sortName": "nothing", "sortType": "desc",
                    "pageNum": 1, "pageSize": 1},
            timeout=10,
        )
        data = resp.json()
        for ann in data.get("announcements") or []:
            if ann.get("secCode") == stock_code:
                org_id = ann["orgId"]
                _ORG_CACHE[stock_code] = org_id
                return org_id
    except Exception as e:
        logger.error("查询orgId失败 %s: %s", stock_code, e)
    return None


def _detect_column(stock_code: str) -> str:
    """根据股票代码判断交易所"""
    if stock_code.startswith("6"):
        return "sse"
    if stock_code.startswith(("0", "3")):
        return "szse"
    if stock_code.startswith(("4", "8")):
        return "bse"
    return "sse"


def get_announcements(
    stock_code: str,
    days: int = 15,
    page_size: int = 30,
    category: str = "",
) -> Dict:
    """获取指定股票的公告列表

    Args:
        stock_code: 股票代码，如 '603009'
        days: 查询天数范围，默认近15天
        page_size: 每页条数
        category: 公告类别筛选，空字符串为全部

    Returns:
        {"stock_code", "stock_name", "total", "announcements": [...]}
    """
    org_id = _resolve_org_id(stock_code)
    if not org_id:
        return {"stock_code": stock_code, "stock_name": "", "total": 0,
                "announcements": [], "error": "无法查询到该股票的orgId"}

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    se_date = f"{start_date:%Y-%m-%d}~{end_date:%Y-%m-%d}"
    column = _detect_column(stock_code)

    try:
        resp = _SESSION.post(
            f"{_CNINFO_BASE}/new/hisAnnouncement/query",
            data={
                "stock": f"{stock_code},{org_id}",
                "tabName": "fulltext",
                "pageSize": page_size,
                "pageNum": 1,
                "column": column,
                "category": category,
                "plate": "sh" if column == "sse" else "sz",
                "seDate": se_date,
                "searchkey": "",
                "secid": "",
                "sortName": "",
                "sortType": "",
                "isHLtitle": "true",
            },
            timeout=15,
        )
        data = resp.json()
    except Exception as e:
        logger.error("获取公告失败 %s: %s", stock_code, e)
        return {"stock_code": stock_code, "stock_name": "", "total": 0,
                "announcements": [], "error": str(e)}

    announcements = []
    stock_name = ""
    for ann in data.get("announcements") or []:
        stock_name = stock_name or ann.get("secName", "")
        title = re.sub(r"<[^>]+>", "", ann.get("announcementTitle", ""))
        ts = ann.get("announcementTime")
        date_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d") if ts else ""
        pdf_url = (_STATIC_BASE + ann["adjunctUrl"]) if ann.get("adjunctUrl") else ""

        announcements.append({
            "title": title,
            "date": date_str,
            "announcement_id": ann.get("announcementId", ""),
            "pdf_url": pdf_url,
            "pdf_size_kb": ann.get("adjunctSize", 0),
            "detail_url": f"{_CNINFO_BASE}/new/disclosure/detail?annoId={ann.get('announcementId')}&orgId={org_id}",
        })

    return {
        "stock_code": stock_code,
        "stock_name": stock_name,
        "org_id": org_id,
        "total": data.get("totalAnnouncement", 0),
        "date_range": se_date,
        "announcements": announcements,
    }
