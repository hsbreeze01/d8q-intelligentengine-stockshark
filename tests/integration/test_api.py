#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API测试脚本
测试股票分析系统的所有API端点
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:5000"

def print_result(test_name: str, result: Dict[str, Any]):
    """打印测试结果"""
    print(f"\n{'='*60}")
    print(f"测试: {test_name}")
    print(f"{'='*60}")
    print(json.dumps(result, ensure_ascii=False, indent=2))

def test_health_check():
    """测试健康检查接口"""
    print("\n测试健康检查接口...")
    response = requests.get(f"{BASE_URL}/health")
    print_result("健康检查", response.json())
    return response.status_code == 200

def test_api_info():
    """测试API信息接口"""
    print("\n测试API信息接口...")
    response = requests.get(f"{BASE_URL}/")
    print_result("API信息", response.json())
    return response.status_code == 200

def test_stock_analysis(symbol: str = "000001"):
    """测试股票分析接口"""
    print(f"\n测试股票分析接口: {symbol}...")
    response = requests.post(
        f"{BASE_URL}/api/analysis/stock/analyze",
        json={"symbol": symbol}
    )
    print_result(f"股票分析 ({symbol})", response.json())
    return response.status_code == 200

def test_stock_quote(symbol: str = "000001"):
    """测试股票行情接口"""
    print(f"\n测试股票行情接口: {symbol}...")
    response = requests.get(
        f"{BASE_URL}/api/analysis/stock/quote",
        params={"symbol": symbol}
    )
    print_result(f"股票行情 ({symbol})", response.json())
    return response.status_code == 200

def test_stock_basic_info(symbol: str = "000001"):
    """测试股票基本信息接口"""
    print(f"\n测试股票基本信息接口: {symbol}...")
    response = requests.get(
        f"{BASE_URL}/api/analysis/stock/basic",
        params={"symbol": symbol}
    )
    print_result(f"股票基本信息 ({symbol})", response.json())
    return response.status_code == 200

def test_search_by_industry(industry_name: str = "银行"):
    """测试按行业搜索接口"""
    print(f"\n测试按行业搜索接口: {industry_name}...")
    response = requests.get(
        f"{BASE_URL}/api/search/stock/by-industry",
        params={"industry_name": industry_name, "limit": 5}
    )
    print_result(f"按行业搜索 ({industry_name})", response.json())
    return response.status_code == 200

def test_search_by_keyword(keyword: str = "平安"):
    """测试按关键词搜索接口"""
    print(f"\n测试按关键词搜索接口: {keyword}...")
    response = requests.get(
        f"{BASE_URL}/api/search/stock/by-keyword",
        params={"keyword": keyword, "limit": 5}
    )
    print_result(f"按关键词搜索 ({keyword})", response.json())
    return response.status_code == 200

def test_get_industries():
    """测试获取行业列表接口"""
    print("\n测试获取行业列表接口...")
    response = requests.get(f"{BASE_URL}/api/search/industries")
    print_result("行业列表", response.json())
    return response.status_code == 200

def test_get_concepts():
    """测试获取概念列表接口"""
    print("\n测试获取概念列表接口...")
    response = requests.get(f"{BASE_URL}/api/search/concepts")
    print_result("概念列表", response.json())
    return response.status_code == 200

def test_supply_chain_scenario(scenario: str = "英伟达GPU最新消息"):
    """测试供应链场景分析接口"""
    print(f"\n测试供应链场景分析接口: {scenario}...")
    response = requests.post(
        f"{BASE_URL}/api/supply-chain/analyze-scenario",
        json={"scenario": scenario}
    )
    print_result(f"供应链场景分析 ({scenario})", response.json())
    return response.status_code == 200

def test_supply_chain_company(company_name: str = "英伟达"):
    """测试公司供应链查询接口"""
    print(f"\n测试公司供应链查询接口: {company_name}...")
    response = requests.get(
        f"{BASE_URL}/api/supply-chain/company",
        params={"company_name": company_name}
    )
    print_result(f"公司供应链查询 ({company_name})", response.json())
    return response.status_code == 200

def test_supply_chain_search(keyword: str = "芯片"):
    """测试供应链供应商搜索接口"""
    print(f"\n测试供应链供应商搜索接口: {keyword}...")
    response = requests.get(
        f"{BASE_URL}/api/supply-chain/supplier/search",
        params={"keyword": keyword, "limit": 5}
    )
    print_result(f"供应链供应商搜索 ({keyword})", response.json())
    return response.status_code == 200

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始运行股票分析系统API测试")
    print("="*60)
    
    tests = [
        ("健康检查", test_health_check),
        ("API信息", test_api_info),
        ("股票分析", lambda: test_stock_analysis("000001")),
        ("股票行情", lambda: test_stock_quote("000001")),
        ("股票基本信息", lambda: test_stock_basic_info("000001")),
        ("按行业搜索", lambda: test_search_by_industry("银行")),
        ("按关键词搜索", lambda: test_search_by_keyword("平安")),
        ("获取行业列表", test_get_industries),
        ("获取概念列表", test_get_concepts),
        ("供应链场景分析", lambda: test_supply_chain_scenario("英伟达GPU最新消息")),
        ("公司供应链查询", lambda: test_supply_chain_company("英伟达")),
        ("供应链供应商搜索", lambda: test_supply_chain_search("芯片")),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, "通过" if success else "失败"))
        except Exception as e:
            print(f"\n测试失败: {test_name}")
            print(f"错误: {str(e)}")
            results.append((test_name, f"异常: {str(e)}"))
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for test_name, result in results:
        status = "✓" if "通过" in result else "✗"
        print(f"{status} {test_name}: {result}")
    
    passed = sum(1 for _, result in results if "通过" in result)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
