"""慧博投研资讯数据获取

来源: https://www.hibor.com.cn
通过 playwright 登录后搜索获取研报，失败则降级为分类页面抓取。
"""

import logging
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_BASE = "https://www.hibor.com.cn"
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": _BASE + "/",
})


def _parse_title(title: str) -> Dict:
    """解析标题元信息: '东吴证券-北特科技-603009-点评-260413'"""
    info = {"org": "", "date": "", "summary": title}
    parts = title.split("-")
    if parts:
        info["org"] = parts[0].strip()
    m = re.search(r"-(\d{2})(\d{2})(\d{2})$", title)
    if m:
        y, mo, d = m.groups()
        info["date"] = f"20{y}-{mo}-{d}"
        info["summary"] = "-".join(parts[1:-1]).strip() if len(parts) > 2 else title
    elif len(parts) > 2:
        info["summary"] = "-".join(parts[1:]).strip()
    return info


def _playwright_search(keyword: str, days: int = 7) -> List[Dict]:
    """通过 playwright 登录慧博并搜索研报"""
    username = os.getenv("HIBOR_USERNAME", "")
    password = os.getenv("HIBOR_PASSWORD", "")
    if not username or not password:
        logger.debug("慧博账号未配置，跳过搜索")
        return []

    try:
        import asyncio
        from playwright.async_api import async_playwright

        async def _do():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                ctx = await browser.new_context()
                page = await ctx.new_page()
                # 登录
                await page.goto(_BASE + "/", wait_until="networkidle", timeout=15000)
                login_js = (
                    "async ([u,pw]) => {"
                    "  const r = await fetch('/hiborweb/Login/Enter', {"
                    "    method:'POST',"
                    "    headers:{'Content-Type':'application/x-www-form-urlencoded','X-Requested-With':'XMLHttpRequest'},"
                    "    body:'uName='+encodeURIComponent(u)+'&pwd='+encodeURIComponent(pw)+'&chkLogin=on'"
                    "  });"
                    "  return await r.text();"
                    "}"
                )
                result = await page.evaluate(login_js, [username, password])
                logger.info("慧博登录: %s", result)
                # 搜索
                sjfw = "1" if days <= 30 else "3" if days <= 90 else "12"
                from urllib.parse import quote
                url = f"{_BASE}/newweb/HuiSou/s?gjc={quote(keyword)}&sslb=1&sjfw={sjfw}&cxzd=qb(qw)&px=sj"
                await page.goto(url, wait_until="networkidle", timeout=20000)
                await asyncio.sleep(5)
                html = await page.content()
                await browser.close()
                return html

        # Handle event loop
        try:
            loop = asyncio.get_running_loop()
            # Already in async context - use nest_asyncio or thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                html = pool.submit(lambda: asyncio.run(_do())).result(timeout=60)
        except RuntimeError:
            html = asyncio.run(_do())

        # Parse results
        reports = []
        pattern = r'<a[^>]+href="(/data/[^"]+\.html)"[^>]*>([^<]+)</a>'
        seen = set()
        for href, title in re.findall(pattern, html):
            if len(title) < 5 or href in seen:
                continue
            seen.add(href)
            meta = _parse_title(title)
            reports.append({
                "title": title, "org": meta["org"], "date": meta["date"],
                "summary": meta["summary"], "detail_url": _BASE + href, "source": "hibor",
            })
        logger.info("慧博搜索 '%s' 获取 %d 条研报", keyword, len(reports))
        return reports

    except Exception as e:
        logger.warning("慧博 playwright 搜索失败: %s", e)
        return []


def _fallback_category(keyword: str, days: int = 7) -> List[Dict]:
    """降级：从分类页面抓取+本地过滤"""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    all_reports = []
    for pg in range(1, 4):
        suffix = f"_{pg}" if pg > 1 else ""
        try:
            resp = _SESSION.get(f"{_BASE}/anreport_12{suffix}.html", timeout=15)
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=re.compile(r"^/data/[a-f0-9]+\.html$")):
                title = a.get("title", "") or a.get_text(strip=True)
                if title and len(title) >= 5:
                    all_reports.append({"title": title, "url": _BASE + a["href"]})
        except Exception as e:
            logger.warning("慧博分类页获取失败: %s", e)
            break

    matched, seen = [], set()
    for r in all_reports:
        if keyword not in r["title"] or r["url"] in seen:
            continue
        seen.add(r["url"])
        meta = _parse_title(r["title"])
        if meta["date"] and meta["date"] < cutoff:
            continue
        matched.append({
            "title": r["title"], "org": meta["org"], "date": meta["date"],
            "summary": meta["summary"], "detail_url": r["url"], "source": "hibor",
        })
    return matched


def get_hibor_reports(keyword: str, days: int = 7, max_pages: int = 3) -> Dict:
    """获取慧博中与指定股票相关的研报

    优先 playwright 登录搜索，失败降级为分类页面抓取。
    """
    reports = _playwright_search(keyword, days)
    if not reports:
        reports = _fallback_category(keyword, days)
    return {"keyword": keyword, "source": "hibor", "total": len(reports), "reports": reports}
