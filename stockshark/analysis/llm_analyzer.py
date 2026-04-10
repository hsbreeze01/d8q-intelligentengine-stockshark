"""LLM 驱动的股票综合分析

整合 AkShare(行情/财务) + 巨潮(公告) + 洞见研报(研报/调研) 数据，
通过 DeepSeek 进行短期/中期/长期价值与风险分析。
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

import requests

from stockshark.data.akshare_data import AkShareData
from stockshark.data.announcement import get_announcements
from stockshark.data.research_report import get_reports

logger = logging.getLogger(__name__)

_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

_ak = AkShareData()


def _llm_call(prompt: str, max_tokens: int = 4000) -> str:
    """调用 DeepSeek LLM"""
    resp = requests.post(
        f"{_BASE_URL}/v1/chat/completions",
        headers={"Authorization": f"Bearer {_API_KEY}", "Content-Type": "application/json"},
        json={"model": _MODEL, "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.3, "max_tokens": max_tokens},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


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

    return data


def _build_prompt(data: Dict, scope: str) -> str:
    """构建分析 Prompt"""
    stock_name = data.get("stock_name", data["stock_code"])
    basic = json.dumps(data.get("basic", {}), ensure_ascii=False, default=str)[:800]
    quote = json.dumps(data.get("quote", {}), ensure_ascii=False, default=str)[:500]
    valuation = json.dumps(data.get("valuation", {}), ensure_ascii=False, default=str)[:500]
    financial = json.dumps(data.get("financial", {}), ensure_ascii=False, default=str)[:1000]
    announcements = json.dumps(data.get("announcements", [])[:10], ensure_ascii=False)[:800]
    reports = json.dumps(data.get("reports", [])[:8], ensure_ascii=False)[:1200]

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

### 券商研报/机构调研
{reports}

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


def analyze_stock_comprehensive(
    stock_code: str,
    scope: str = "all",
) -> Dict[str, Any]:
    """综合分析股票

    Args:
        stock_code: 股票代码
        scope: 分析范围 short/mid/long/all

    Returns:
        LLM 分析结果
    """
    if not _API_KEY:
        return {"error": "DEEPSEEK_API_KEY 未配置"}

    # 1. 采集数据
    logger.info("开始采集 %s 数据", stock_code)
    data = _gather_data(stock_code)

    # 2. 构建 Prompt
    prompt = _build_prompt(data, scope)

    # 3. LLM 分析
    logger.info("调用 LLM 分析 %s (scope=%s)", stock_code, scope)
    try:
        raw = _llm_call(prompt)
        # 解析 JSON（兼容 markdown 代码块）
        if raw.strip().startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(raw)
    except Exception as e:
        logger.error("LLM 分析失败: %s", e)
        return {"error": f"LLM分析失败: {e}", "raw_response": raw if 'raw' in dir() else ""}

    # 4. 补充元数据
    result["stock_code"] = stock_code
    result["scope"] = scope
    result["analyzed_at"] = datetime.now().isoformat()
    result["data_sources"] = {
        "akshare": "basic" in data and "error" not in str(data.get("basic", "")),
        "cninfo_announcements": len(data.get("announcements", [])),
        "djyanbao_reports": len(data.get("reports", [])),
    }

    return result
