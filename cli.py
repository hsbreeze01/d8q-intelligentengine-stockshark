#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
StockShark 股票分析系统 - 命令行工具
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stockshark.analysis.stock_analyzer import StockAnalyzer
from stockshark.analysis.search_engine import SearchEngine
from stockshark.analysis.supply_chain_analyzer import SupplyChainAnalyzer
from stockshark.data.akshare_data import AkShareData


def analyze_stock(symbol):
    """分析单只股票"""
    print(f"\n{'='*60}")
    print(f"分析股票: {symbol}")
    print(f"{'='*60}")
    
    analyzer = StockAnalyzer()
    result = analyzer.analyze_stock(symbol)
    
    print(f"\n股票代码: {result['symbol']}")
    print(f"股票名称: {result['basic_info']['name'] if result['basic_info'] else 'N/A'}")
    print(f"投资评分: {result['investment_score']}")
    print(f"风险评分: {result['risk_score']}")
    print(f"\n分析摘要: {result['analysis_summary']}")
    
    return result


def search_stocks(keyword, search_type='name'):
    """搜索股票"""
    print(f"\n{'='*60}")
    print(f"搜索股票: {keyword} (类型: {search_type})")
    print(f"{'='*60}")
    
    search_engine = SearchEngine()
    
    if search_type == 'industry':
        results = search_engine.search_by_industry(keyword)
    elif search_type == 'concept':
        results = search_engine.search_by_concept(keyword)
    else:
        results = search_engine.search_by_name(keyword)
    
    print(f"\n找到 {len(results)} 只相关股票:")
    for i, stock in enumerate(results[:10], 1):
        print(f"{i}. {stock['code']} - {stock['name']} ({stock.get('industry', 'N/A')})")
    
    return results


def analyze_supply_chain(scenario):
    """分析供应链"""
    print(f"\n{'='*60}")
    print(f"供应链分析: {scenario}")
    print(f"{'='*60}")
    
    ak_data = AkShareData()
    analyzer = SupplyChainAnalyzer(ak_data)
    
    results = analyzer.analyze_scenario(scenario)
    
    print(f"\n找到 {len(results)} 家相关企业:")
    for i, company in enumerate(results[:10], 1):
        print(f"{i}. {company['name']} - {company['relationship']} - 上市: {'是' if company['is_listed'] else '否'}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='StockShark 股票分析系统')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    analyze_parser = subparsers.add_parser('analyze', help='分析单只股票')
    analyze_parser.add_argument('symbol', help='股票代码')
    
    search_parser = subparsers.add_parser('search', help='搜索股票')
    search_parser.add_argument('keyword', help='搜索关键词')
    search_parser.add_argument('--type', choices=['name', 'industry', 'concept'], 
                             default='name', help='搜索类型')
    
    supply_parser = subparsers.add_parser('supply', help='供应链分析')
    supply_parser.add_argument('scenario', help='场景描述')
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        analyze_stock(args.symbol)
    elif args.command == 'search':
        search_stocks(args.keyword, args.type)
    elif args.command == 'supply':
        analyze_supply_chain(args.scenario)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
