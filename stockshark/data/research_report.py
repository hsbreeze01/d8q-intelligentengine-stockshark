"""洞见研报数据获取 - 券商研报、机构调研、定期报告"""

import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

_API_BASE = "https://api.djyanbao.com/api"
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.djyanbao.com/",
})


def _classify(item: Dict) -> str:
    """根据机构和标题自动分类"""
    org = item.get("orgName", "")
    title = item.get("title", "")
    if org in ("上交所", "深交所", "北交所"):
        return "定期报告/公告"
    if "调研" in title or org == "机构调研":
        return "机构调研"
    if any(k in org for k in ("证券", "基金", "资管", "海通", "中信", "国泰", "华创",
                               "天风", "民生", "东吴", "招商", "光大", "申万", "国金",
                               "浙商", "开源", "中泰", "国海", "山西", "东方", "银河")):
        return "券商研报"
    return "行业研报"


def get_reports(
    keyword: str,
    page: int = 1,
    limit: int = 20,
) -> Dict:
    """搜索研报/公告/调研

    Args:
        keyword: 搜索关键词（股票名称或代码）
        page: 页码
        limit: 每页条数

    Returns:
        {"keyword", "total", "reports": [...]}
    """
    try:
        resp = _SESSION.get(
            f"{_API_BASE}/report",
            params={"q": keyword, "page": page, "limit": limit},
            timeout=15,
        )
        data = resp.json()
    except Exception as e:
        logger.error("洞见研报查询失败 %s: %s", keyword, e)
        return {"keyword": keyword, "total": 0, "reports": [], "error": str(e)}

    inner = data.get("data", {})
    items = inner.get("data", [])

    reports = []
    for r in items:
        cat = _classify(r)
        reports.append({
            "id": r.get("id"),
            "title": r.get("title", ""),
            "category": cat,
            "org": r.get("orgName", ""),
            "authors": r.get("authors", ""),
            "date": (r.get("publishAt") or "")[:10],
            "pages": r.get("pageTotal", 0),
            "file_size_kb": round(r.get("fileSize", 0) / 1024),
            "stock_name": r.get("stockName", ""),
            "detail_url": f"https://www.djyanbao.com/report/detail?id={r.get('id')}",
        })

    return {
        "keyword": keyword,
        "total": inner.get("total"),
        "page": page,
        "limit": limit,
        "reports": reports,
    }
