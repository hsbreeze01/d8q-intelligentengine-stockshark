#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
股票搜索引擎
提供股票搜索功能，支持按代码、名称、行业、概念等多种方式搜索
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from stockshark.data.akshare_data import AkShareData
from stockshark.data.data_processor import DataProcessor

class SearchEngine:
    """
    股票搜索引擎类
    """
    
    def __init__(self):
        self.ak_data = AkShareData()
        self.data_processor = DataProcessor()
    
    def search_by_code_or_name(
        self, 
        keyword: str, 
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        按股票代码或名称搜索
        :param keyword: 关键词（代码或名称）
        :param limit: 返回结果数量限制
        :return: 搜索结果
        """
        result = {
            'keyword': keyword,
            'results': [],
            'total': 0
        }
        
        try:
            # 尝试按代码搜索
            if keyword.isdigit() and len(keyword) == 6:
                stock_info = self.ak_data.get_stock_basic_info(keyword)
                if stock_info:
                    result['results'].append(stock_info)
            
            # 获取所有股票列表
            # 使用行业和概念数据进行搜索
            industries = self.ak_data.get_all_industries()
            all_stocks = []
            
            # 处理所有行业（移除限制）
            for industry in industries:
                stocks = self.ak_data.get_industry_stocks(industry)
                if stocks:
                    all_stocks.extend(stocks)
            
            # 按名称模糊搜索
            for stock in all_stocks:
                stock_name = stock.get('名称', '')
                if keyword.lower() in stock_name.lower():
                    if len(result['results']) < limit:
                        result['results'].append({
                            'code': stock.get('代码', ''),
                            'name': stock_name,
                            'price': stock.get('最新价', 0),
                            'change_pct': stock.get('涨跌幅', 0)
                        })
            
            # 如果通过行业搜索结果不足，尝试通过概念搜索
            if len(result['results']) < limit:
                concepts = self.ak_data.get_all_concepts()
                for concept in concepts:
                    try:
                        concept_stocks = self.ak_data.get_concept_stocks(concept)
                        if concept_stocks:
                            for stock in concept_stocks:
                                stock_name = stock.get('名称', '')
                                if keyword.lower() in stock_name.lower():
                                    # 检查是否已存在
                                    existing = any(
                                        r['code'] == stock.get('代码', '') 
                                        for r in result['results']
                                    )
                                    if not existing and len(result['results']) < limit:
                                        result['results'].append({
                                            'code': stock.get('代码', ''),
                                            'name': stock_name,
                                            'price': stock.get('最新价', 0),
                                            'change_pct': stock.get('涨跌幅', 0)
                                        })
                    except Exception as e:
                        continue
            
            result['total'] = len(result['results'])
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def search_by_industry(
        self, 
        industry_name: str, 
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        按行业搜索股票
        :param industry_name: 行业名称
        :param filters: 筛选条件
        :param sort_by: 排序字段
        :param limit: 返回结果数量限制
        :return: 搜索结果
        """
        result = {
            'industry_name': industry_name,
            'results': [],
            'total': 0,
            'filters_applied': filters or {},
            'sort_by': sort_by
        }
        
        try:
            # 获取行业股票列表
            stocks = self.ak_data.get_industry_stocks(industry_name)
            
            if not stocks:
                result['error'] = f"未找到行业：{industry_name}"
                return result
            
            # 应用筛选条件
            filtered_stocks = self._apply_filters(stocks, filters)
            
            # 应用排序
            sorted_stocks = self._apply_sort(filtered_stocks, sort_by)
            
            # 限制数量
            result['results'] = sorted_stocks[:limit]
            result['total'] = len(sorted_stocks)
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def search_by_concept(
        self, 
        concept_name: str, 
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        按概念搜索股票
        :param concept_name: 概念名称
        :param filters: 筛选条件
        :param sort_by: 排序字段
        :param limit: 返回结果数量限制
        :return: 搜索结果
        """
        result = {
            'concept_name': concept_name,
            'results': [],
            'total': 0,
            'filters_applied': filters or {},
            'sort_by': sort_by
        }
        
        try:
            # 获取概念股票列表
            stocks = self.ak_data.get_concept_stocks(concept_name)
            
            if not stocks:
                result['error'] = f"未找到概念：{concept_name}"
                return result
            
            # 应用筛选条件
            filtered_stocks = self._apply_filters(stocks, filters)
            
            # 应用排序
            sorted_stocks = self._apply_sort(filtered_stocks, sort_by)
            
            # 限制数量
            result['results'] = sorted_stocks[:limit]
            result['total'] = len(sorted_stocks)
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def search_by_theme(
        self, 
        theme: str, 
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        按主题搜索股票（可以是行业或概念）
        :param theme: 主题名称
        :param filters: 筛选条件
        :param sort_by: 排序字段
        :param limit: 返回结果数量限制
        :return: 搜索结果
        """
        result = {
            'theme': theme,
            'industry_results': None,
            'concept_results': None,
            'combined_results': []
        }
        
        try:
            # 尝试按行业搜索
            industry_result = self.search_by_industry(
                theme, filters, sort_by, limit
            )
            
            # 尝试按概念搜索
            concept_result = self.search_by_concept(
                theme, filters, sort_by, limit
            )
            
            result['industry_results'] = industry_result
            result['concept_results'] = concept_result
            
            # 合并结果（去重）
            all_stocks = []
            seen_codes = set()
            
            if industry_result.get('results'):
                for stock in industry_result['results']:
                    code = stock.get('代码', '')
                    if code and code not in seen_codes:
                        all_stocks.append(stock)
                        seen_codes.add(code)
            
            if concept_result.get('results'):
                for stock in concept_result['results']:
                    code = stock.get('代码', '')
                    if code and code not in seen_codes:
                        all_stocks.append(stock)
                        seen_codes.add(code)
            
            result['combined_results'] = all_stocks[:limit]
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def _apply_filters(
        self, 
        stocks: List[Dict], 
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict]:
        """
        应用筛选条件
        :param stocks: 股票列表
        :param filters: 筛选条件
        :return: 筛选后的股票列表
        """
        if not filters:
            return stocks
        
        filtered_stocks = stocks
        
        # 价格范围筛选
        if 'price_min' in filters or 'price_max' in filters:
            price_min = filters.get('price_min', 0)
            price_max = filters.get('price_max', float('inf'))
            filtered_stocks = [
                s for s in filtered_stocks
                if price_min <= s.get('最新价', 0) <= price_max
            ]
        
        # 涨跌幅筛选
        if 'change_pct_min' in filters or 'change_pct_max' in filters:
            change_pct_min = filters.get('change_pct_min', -float('inf'))
            change_pct_max = filters.get('change_pct_max', float('inf'))
            filtered_stocks = [
                s for s in filtered_stocks
                if change_pct_min <= s.get('涨跌幅', 0) <= change_pct_max
            ]
        
        # 市盈率筛选
        if 'pe_min' in filters or 'pe_max' in filters:
            pe_min = filters.get('pe_min', 0)
            pe_max = filters.get('pe_max', float('inf'))
            filtered_stocks = [
                s for s in filtered_stocks
                if pe_min <= s.get('市盈率-动态', 0) <= pe_max
            ]
        
        # 换手率筛选
        if 'turnover_min' in filters or 'turnover_max' in filters:
            turnover_min = filters.get('turnover_min', 0)
            turnover_max = filters.get('turnover_max', float('inf'))
            filtered_stocks = [
                s for s in filtered_stocks
                if turnover_min <= s.get('换手率', 0) <= turnover_max
            ]
        
        return filtered_stocks
    
    def _apply_sort(
        self, 
        stocks: List[Dict], 
        sort_by: Optional[str]
    ) -> List[Dict]:
        """
        应用排序
        :param stocks: 股票列表
        :param sort_by: 排序字段（格式：字段名:asc 或 字段名:desc）
        :return: 排序后的股票列表
        """
        if not sort_by:
            return stocks
        
        parts = sort_by.split(':')
        field = parts[0]
        order = parts[1] if len(parts) > 1 else 'desc'
        
        reverse = (order.lower() == 'desc')
        
        try:
            sorted_stocks = sorted(
                stocks,
                key=lambda x: x.get(field, 0),
                reverse=reverse
            )
            return sorted_stocks
        except Exception:
            return stocks
    
    def get_all_industries(self) -> List[str]:
        """
        获取所有行业列表
        :return: 行业名称列表
        """
        try:
            industries = self.ak_data.get_all_industries()
            return industries
        except Exception as e:
            print(f"获取行业列表失败: {e}")
            return []
    
    def get_all_concepts(self) -> List[str]:
        """
        获取所有概念列表
        :return: 概念名称列表
        """
        try:
            concepts = self.ak_data.get_all_concepts()
            return concepts
        except Exception as e:
            print(f"获取概念列表失败: {e}")
            return []

# 创建全局实例
search_engine = SearchEngine()
