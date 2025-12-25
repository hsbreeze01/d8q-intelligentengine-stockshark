#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试akshare数据源接入功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stockshark.data.akshare_data import AkShareData
from stockshark.data.data_processor import DataProcessor

def test_akshare_data():
    """测试akshare数据获取功能"""
    print("=== 测试akshare数据源接入功能 ===")
    
    try:
        # 初始化akshare数据对象
        ak_data = AkShareData()
        data_processor = DataProcessor()
        
        print("1. 测试获取股票基本信息...")
        stock_info = ak_data.get_stock_basic_info("000001")
        if stock_info:
            print(f"   成功: {stock_info['code']} - {stock_info['name']} ({stock_info['market']})")
        else:
            print("   失败: 未获取到股票信息")
        
        print("\n2. 测试获取股票实时行情...")
        quote_data = ak_data.get_stock_quote("000001")
        if quote_data:
            cleaned_quote = data_processor.clean_stock_quote(quote_data)
            print(f"   成功: {cleaned_quote['code']} - 当前价格: {cleaned_quote['price']} 元")
        else:
            print("   失败: 未获取到实时行情")
        
        print("\n3. 测试获取股票历史数据...")
        history_data = ak_data.get_stock_history_data("000001", start_date="2023-01-01", end_date="2023-12-31")
        if not history_data.empty:
            cleaned_history = data_processor.clean_stock_history(history_data)
            technical_history = data_processor.calculate_technical_indicators(cleaned_history)
            print(f"   成功: 获取到 {len(technical_history)} 条历史数据，包含技术指标")
        else:
            print("   失败: 未获取到历史数据")
        
        print("\n4. 测试获取股票财务数据...")
        financial_data = ak_data.get_stock_financial_data("000001")
        if not financial_data.empty:
            cleaned_financial = data_processor.clean_financial_data(financial_data)
            ratio_financial = data_processor.calculate_financial_ratios(cleaned_financial)
            print(f"   成功: 获取到 {len(ratio_financial)} 条财务数据，包含财务比率")
        else:
            print("   失败: 未获取到财务数据")
        
        print("\n5. 测试获取股票估值数据...")
        valuation_data = ak_data.get_stock_valuation_data("000001")
        if valuation_data:
            print(f"   成功: PE-TTM: {valuation_data.get('pe_ttm')}, PB: {valuation_data.get('pb')}")
        else:
            print("   失败: 未获取到估值数据")
        
        print("\n6. 测试获取行业股票列表...")
        industry_stocks = ak_data.get_industry_stocks(industry_name="计算机设备")
        if industry_stocks and len(industry_stocks) > 0:
            print(f"   成功: 获取到 {len(industry_stocks)} 只计算机设备行业股票")
            print(f"   前5只: {industry_stocks[:5]}")
        else:
            print("   失败: 未获取到行业股票列表")
        
        print("\n7. 测试获取概念股票列表...")
        concept_stocks = ak_data.get_concept_stocks(concept_name="人工智能")
        if concept_stocks and len(concept_stocks) > 0:
            print(f"   成功: 获取到 {len(concept_stocks)} 只人工智能概念股票")
            print(f"   前5只: {concept_stocks[:5]}")
        else:
            print("   失败: 未获取到概念股票列表")
        
        print("\n8. 测试股票数据整合功能...")
        if stock_info and quote_data and valuation_data:
            integrated_data = data_processor.integrate_stock_data(stock_info, quote_data, valuation_data)
            print(f"   成功: 整合了 {len(integrated_data)} 个字段的数据")
            
            # 测试投资价值评分
            investment_score = data_processor.calculate_investment_score(integrated_data)
            print(f"   投资价值评分: {investment_score['total_score']} ({investment_score['rating']})")
            
            # 测试风险评分
            risk_score = data_processor.calculate_risk_score(integrated_data)
            print(f"   风险评分: {risk_score['risk_level']} ({risk_score['risk_count']}个风险因素)")
        else:
            print("   失败: 数据不足，无法进行整合测试")
        
        print("\n=== 所有测试完成 ===")
        return True
        
    except Exception as e:
        print(f"\n测试失败，发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_akshare_data()
