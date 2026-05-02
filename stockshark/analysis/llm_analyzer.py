"""LLM 驱动的股票综合分析

整合 AkShare(行情/财务) + 巨潮(公告) + 洞见研报(研报/调研) 数据，
通过 DeepSeek 进行短期/中期/长期价值与风险分析。

v1.1 - 增加评估结论缓存与智能重新评估（docs/evaluation_cache_design.md）
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

import requests
import time

from stockshark.data.akshare_data import AkShareData
from stockshark.data.announcement import get_announcements
from stockshark.data.research_report import get_reports
from stockshark.data.hibor_report import get_hibor_reports
from stockshark.analysis.evaluation_cache import (
    get_cached_evaluation, save_evaluation, build_fingerprint,
    check_triggers, ensure_index,
)

logger = logging.getLogger(__name__)

_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

_ak = AkShareData()

# 启动时确保索引
try:
    ensure_index()
except Exception:
    pass


def _llm_call(prompt: str, max_tokens: int = 4000, max_retries: int = 2) -> str:
    """调用 DeepSeek LLM（含重试）"""
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                f"{_BASE_URL}/v1/chat/completions",
                headers={"Authorization": f"Bearer {_API_KEY}", "Content-Type": "application/json"},
                json={"model": _MODEL, "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.3, "max_tokens": max_tokens},
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                wait = 2 ** attempt
                logger.warning("LLM call failed (%s), retry in %ds (attempt %d/%d)...", e, wait, attempt + 1, max_retries)
                time.sleep(wait)
    raise last_err


def _gather_data(stock_code: str) -> Dict[str, Any]:
    """并行采集所有数据源"""
    data = {"stock_code": stock_code}

    # 1. AkShare: 基本信息 + 行情 + 估值
    try:
        data["basic"] = _ak.get_stock_basic_info(stock_code)
    except Exception as e:
        data["basic"] = {"error": str(e)}

    try:
        data["quote"] = _ak.get_stock_quote(stock_code)
    except Exception as e:
        data["quote"] = {"error": str(e)}

    try:
        data["valuation"] = _ak.get_stock_valuation_data(stock_code)
    except Exception as e:
        data["valuation"] = {"error": str(e)}

    try:
        data["financial"] = _ak.get_stock_financial_data(stock_code)
        if hasattr(data["financial"], "to_dict"):
            data["financial"] = data["financial"].head(5).to_dict("records")
    except Exception as e:
        data["financial"] = {"error": str(e)}

    # 2. 巨潮: 近30天公告
    try:
        ann = get_announcements(stock_code, days=30, page_size=15)
        data["announcements"] = [
            {"title": a["title"], "date": a["date"]}
            for a in ann.get("announcements", [])
        ]
        data["stock_name"] = ann.get("stock_name", "")
    except Exception as e:
        data["announcements"] = []

    # 3. 洞见研报: 最新研报
    keyword = data.get("stock_name") or stock_code
    try:
        rpt = get_reports(keyword, limit=10)
        data["reports"] = [
            {"title": r["title"], "org": r["org"], "category": r["category"],
             "date": r["date"], "authors": r["authors"]}
            for r in rpt.get("reports", [])
        ]
    except Exception as e:
        data["reports"] = []

    # 4. 慧博投研: 公司调研研报
    try:
        hb = get_hibor_reports(keyword, days=30, max_pages=2)
        data["hibor_reports"] = [
            {"title": r["title"], "org": r["org"], "date": r["date"],
             "summary": r.get("summary", "")}
            for r in hb.get("reports", [])
        ]
    except Exception as e:
        data["hibor_reports"] = []

    return data


def _build_prompt(data: Dict, scope: str) -> str:
    """构建分析 Prompt（支持从 prompts.yml 动态加载）"""
    stock_name = data.get("stock_name", data["stock_code"])
    basic = json.dumps(data.get("basic", {}), ensure_ascii=False, default=str)[:800]
    quote = json.dumps(data.get("quote", {}), ensure_ascii=False, default=str)[:500]
    valuation = json.dumps(data.get("valuation", {}), ensure_ascii=False, default=str)[:500]
    financial = json.dumps(data.get("financial", {}), ensure_ascii=False, default=str)[:1000]
    announcements = json.dumps(data.get("announcements", [])[:10], ensure_ascii=False)[:800]
    reports = json.dumps(data.get("reports", [])[:8], ensure_ascii=False)[:1200]
    hibor_reports = json.dumps(data.get("hibor_reports", [])[:5], ensure_ascii=False)[:800]

    scope_instruction = {
        "short": "重点分析短期(1-4周)：技术面信号、近期公告事件催化、资金面、短期风险。",
        "mid": "重点分析中期(1-6月)：业绩预期、券商研报观点、估值合理性、行业景气度。",
        "long": "重点分析长期(1-3年)：商业模式、竞争壁垒、成长空间、财务健康趋势。",
        "all": "分别从短期(1-4周)、中期(1-6月)、长期(1-3年)三个维度进行分析。",
    }.get(scope, "all")

    return f"""你是专业的A股投资分析师。请对 {stock_name}({data['stock_code']}) 进行价值与风险分析。

{scope_instruction}

## 数据

### 基本信息
{basic}

### 实时行情
{quote}

### 估值数据
{valuation}

### 财务指标(近几期)
{financial}

### 近期公告(近30天)
{announcements}

### 券商研报/机构调研(洞见研报)
{reports}

### 券商研报/机构调研(慧博投研)
{hibor_reports}

## 输出要求

请严格按以下JSON格式输出，不要输出其他内容：
{{
  "stock_name": "{stock_name}",
  "score": 0-100的投资评分,
  "risk_level": "低/中/高",
  "short_term": {{
    "outlook": "短期展望(2-3句话)",
    "signal": "看多/看空/中性",
    "key_factors": ["关键因素1", "关键因素2"]
  }},
  "mid_term": {{
    "outlook": "中期展望(2-3句话)",
    "signal": "看多/看空/中性",
    "key_factors": ["关键因素1", "关键因素2"]
  }},
  "long_term": {{
    "outlook": "长期展望(2-3句话)",
    "signal": "看多/看空/中性",
    "key_factors": ["关键因素1", "关键因素2"]
  }},
  "risk_alerts": ["风险提示1", "风险提示2"],
  "summary": "一段话总结投资建议(50字内)"
}}"""


def _do_full_evaluation(stock_code: str, scope: str,
                        trigger_reason: str) -> Dict[str, Any]:
    """执行全量评估：采集数据 → LLM分析 → 存储结论"""
    # 1. 采集数据
    logger.info("全量评估 %s (scope=%s, reason=%s)", stock_code, scope, trigger_reason)
    data = _gather_data(stock_code)

    # 2. 构建 Prompt & LLM 分析
    prompt = _build_prompt(data, scope)
    try:
        raw = _llm_call(prompt)
        if raw.strip().startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(raw)
    except Exception as e:
        logger.error("LLM 分析失败: %s", e)
        return {"error": f"LLM分析失败: {e}", "raw_response": raw if 'raw' in dir() else ""}

    # 3. 补充元数据
    result["stock_code"] = stock_code
    result["scope"] = scope
    result["analyzed_at"] = datetime.now().isoformat()
    result["cached"] = False
    result["trigger_reason"] = trigger_reason
    result["data_sources"] = {
        "akshare": "basic" in data and "error" not in str(data.get("basic", "")),
        "cninfo_announcements": len(data.get("announcements", [])),
        "djyanbao_reports": len(data.get("reports", [])),
        "hibor_reports": len(data.get("hibor_reports", [])),
    }

    # 4. 构建指纹并持久化
    fingerprint = build_fingerprint(
        data.get("quote", {}),
        data.get("valuation", {}),
        data.get("announcements", []),
        data.get("reports", []) + data.get("hibor_reports", []),
    )
    save_evaluation(stock_code, scope, result, fingerprint, trigger_reason)

    return result


def analyze_stock_comprehensive(
    stock_code: str,
    scope: str = "all",
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """综合分析股票（带智能缓存）

    Args:
        stock_code: 股票代码
        scope: 分析范围 short/mid/long/all
        force_refresh: 强制刷新，忽略缓存

    Returns:
        LLM 分析结果，含 cached / trigger_reason 字段
    """
    if not _API_KEY:
        return {"error": "DEEPSEEK_API_KEY 未配置"}

    # 强制刷新 → 直接全量评估
    if force_refresh:
        return _do_full_evaluation(stock_code, scope, "force_refresh")

    # 查询缓存
    cached = get_cached_evaluation(stock_code, scope)
    if not cached:
        return _do_full_evaluation(stock_code, scope, "initial")

    # 触发检测
    should_refresh, reason = check_triggers(cached, stock_code)
    if should_refresh:
        return _do_full_evaluation(stock_code, scope, reason)

    # 返回缓存结论
    logger.info("复用缓存评估: %s scope=%s", stock_code, scope)
    result = cached.get("result", {})
    result["cached"] = True
    result["trigger_reason"] = "none"
    result["cached_at"] = cached.get("evaluated_at", "")
    return result
