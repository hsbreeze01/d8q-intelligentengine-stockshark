#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
股票分析引擎
提供股票分析功能，包括基本面分析、技术面分析、估值分析和风险评估
"""

import pandas as pd
from typing import Dict, List, Any
from stockshark.data.akshare_data import AkShareData
from stockshark.data.data_processor import DataProcessor

class StockAnalyzer:
    """
    股票分析引擎类
    """
    
    def __init__(self):
        self.ak_data = AkShareData()
        self.data_processor = DataProcessor()
    
    def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """
        分析单只股票
        :param symbol: 股票代码
        :return: 分析结果
        """
        result = {
            'symbol': symbol,
            'basic_info': None,
            'quote_data': None,
            'valuation_data': None,
            'investment_score': None,
            'risk_score': None,
            'analysis_summary': None
        }
        
        try:
            # 获取股票基本信息
            basic_info = self.ak_data.get_stock_basic_info(symbol)
            if basic_info:
                result['basic_info'] = basic_info
            
            # 获取实时行情数据
            quote_data = self.ak_data.get_stock_quote(symbol)
            if quote_data:
                cleaned_quote = self.data_processor.clean_stock_quote(quote_data)
                result['quote_data'] = cleaned_quote
            
            # 获取估值数据
            valuation_data = self.ak_data.get_stock_valuation_data(symbol)
            if valuation_data:
                result['valuation_data'] = valuation_data
            
            # 整合数据
            integrated_data = self.data_processor.integrate_stock_data(
                basic_info, quote_data, valuation_data
            )
            
            # 计算投资价值评分
            if integrated_data:
                investment_score = self.data_processor.calculate_investment_score(integrated_data)
                result['investment_score'] = investment_score
                
                # 计算风险评分
                risk_score = self.data_processor.calculate_risk_score(integrated_data)
                result['risk_score'] = risk_score
                
                # 生成分析摘要
                result['analysis_summary'] = self._generate_analysis_summary(
                    basic_info, quote_data, valuation_data, investment_score, risk_score
                )
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def _generate_analysis_summary(
        self, 
        basic_info: Dict, 
        quote_data: Dict, 
        valuation_data: Dict,
        investment_score: Dict,
        risk_score: Dict
    ) -> str:
        """
        生成分析摘要
        """
        summary_parts = []
        
        if basic_info:
            summary_parts.append(f"股票名称：{basic_info.get('name', 'N/A')} ({basic_info.get('code', 'N/A')})")
            summary_parts.append(f"所属市场：{basic_info.get('market', 'N/A')}")
        
        if quote_data:
            price = quote_data.get('price', 0)
            change_pct = quote_data.get('change_pct', 0)
            summary_parts.append(f"当前价格：{price:.2f} 元")
            summary_parts.append(f"涨跌幅：{change_pct:.2f}%")
        
        if valuation_data:
            pe_ttm = valuation_data.get('pe_ttm', 0)
            pb = valuation_data.get('pb', 0)
            summary_parts.append(f"市盈率(TTM)：{pe_ttm:.2f}")
            summary_parts.append(f"市净率：{pb:.2f}")
        
        if investment_score:
            total_score = investment_score.get('total_score', 0)
            rating = investment_score.get('rating', 'N/A')
            summary_parts.append(f"投资价值评分：{total_score} ({rating})")
        
        if risk_score:
            risk_level = risk_score.get('risk_level', 'N/A')
            risk_count = risk_score.get('risk_count', 0)
            summary_parts.append(f"风险等级：{risk_level} ({risk_count}个风险因素)")
        
        return "\n".join(summary_parts)
    
    def batch_analyze_stocks(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        批量分析多只股票
        :param symbols: 股票代码列表
        :return: 分析结果列表
        """
        results = []
        
        for symbol in symbols:
            result = self.analyze_stock(symbol)
            results.append(result)
        
        return results
    
    def analyze_industry_stocks(
        self, 
        industry_name: str, 
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        分析行业股票
        :param industry_name: 行业名称
        :param limit: 返回的股票数量限制
        :return: 分析结果
        """
        result = {
            'industry_name': industry_name,
            'stocks': [],
            'summary': None
        }
        
        try:
            # 获取行业股票列表
            industry_stocks = self.ak_data.get_industry_stocks(industry_name)
            
            if not industry_stocks:
                result['error'] = f"未找到行业：{industry_name}"
                return result
            
            # 限制数量
            limited_stocks = industry_stocks[:limit]
            
            # 批量分析
            symbols = [stock['代码'] for stock in limited_stocks]
            analysis_results = self.batch_analyze_stocks(symbols)
            
            result['stocks'] = analysis_results
            
            # 生成行业摘要
            result['summary'] = self._generate_industry_summary(analysis_results)
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def _generate_industry_summary(self, analysis_results: List[Dict]) -> Dict[str, Any]:
        """
        生成行业分析摘要
        """
        total_stocks = len(analysis_results)
        valid_stocks = [r for r in analysis_results if r.get('investment_score')]
        
        if not valid_stocks:
            return {
                'total_stocks': total_stocks,
                'valid_stocks': 0,
                'avg_investment_score': 0,
                'high_quality_stocks': []
            }
        
        # 计算平均投资价值评分
        total_score = sum(r['investment_score']['total_score'] for r in valid_stocks)
        avg_score = total_score / len(valid_stocks)
        
        # 找出优质股票（评分>=60）
        high_quality_stocks = [
            r for r in valid_stocks 
            if r['investment_score']['total_score'] >= 60
        ]
        
        return {
            'total_stocks': total_stocks,
            'valid_stocks': len(valid_stocks),
            'avg_investment_score': round(avg_score, 2),
            'high_quality_stocks': [
                {
                    'symbol': r['symbol'],
                    'name': r.get('basic_info', {}).get('name', ''),
                    'score': r['investment_score']['total_score'],
                    'rating': r['investment_score']['rating']
                }
                for r in high_quality_stocks[:5]
            ]
        }
    
    def analyze_concept_stocks(
        self, 
        concept_name: str, 
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        分析概念股票
        :param concept_name: 概念名称
        :param limit: 返回的股票数量限制
        :return: 分析结果
        """
        result = {
            'concept_name': concept_name,
            'stocks': [],
            'summary': None
        }
        
        try:
            # 获取概念股票列表
            concept_stocks = self.ak_data.get_concept_stocks(concept_name)
            
            if not concept_stocks:
                result['error'] = f"未找到概念：{concept_name}"
                return result
            
            # 限制数量
            limited_stocks = concept_stocks[:limit]
            
            # 批量分析
            symbols = [stock['代码'] for stock in limited_stocks]
            analysis_results = self.batch_analyze_stocks(symbols)
            
            result['stocks'] = analysis_results
            
            # 生成概念摘要
            result['summary'] = self._generate_industry_summary(analysis_results)
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result

# 创建全局实例
stock_analyzer = StockAnalyzer()
