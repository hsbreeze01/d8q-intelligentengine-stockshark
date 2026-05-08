import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from stockshark.data.akshare_data import AkShareData
from stockshark.data.data_processor import DataProcessor
from stockshark.data.fetcher import fetcher

logger = logging.getLogger(__name__)


def _safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        f = float(val)
        return default if f != f else f
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=0):
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_str(val, default=''):
    if val is None:
        return default
    try:
        s = str(val)
        return default if s == 'nan' else s
    except (ValueError, TypeError):
        return default


class SearchEngine:

    def __init__(self):
        self.ak_data = AkShareData()
        self.data_processor = DataProcessor()

    def search_by_code_or_name(self, keyword: str, limit: int = 20) -> Dict[str, Any]:
        result = {'keyword': keyword, 'results': [], 'total': 0}
        try:
            if keyword.isdigit() and len(keyword) == 6:
                stock_info = self.ak_data.get_stock_basic_info(keyword)
                if stock_info:
                    result['results'].append(stock_info)

            all_stocks = self.ak_data.get_all_stocks()
            for stock in all_stocks:
                stock_name = stock.get('name', '')
                if keyword.lower() in stock_name.lower():
                    if len(result['results']) < limit:
                        result['results'].append({
                            'code': stock.get('code', ''),
                            'name': stock_name,
                        })
            result['total'] = len(result['results'])
            return result
        except Exception as e:
            result['error'] = str(e)
            return result

    def search_by_industry(self, industry_name: str, filters: Optional[Dict[str, Any]] = None,
                           sort_by: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        result = {'industry_name': industry_name, 'results': [], 'total': 0,
                  'filters_applied': filters or {}, 'sort_by': sort_by}
        try:
            stocks = self.ak_data.get_industry_stocks(industry_name)
            if not stocks:
                result['error'] = f"未找到行业：{industry_name}"
                return result
            filtered_stocks = self._apply_filters(stocks, filters)
            sorted_stocks = self._apply_sort(filtered_stocks, sort_by)
            result['results'] = sorted_stocks[:limit]
            result['total'] = len(sorted_stocks)
            return result
        except Exception as e:
            result['error'] = str(e)
            return result

    def search_by_concept(self, concept_name: str, filters: Optional[Dict[str, Any]] = None,
                          sort_by: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        result = {'concept_name': concept_name, 'results': [], 'total': 0,
                  'filters_applied': filters or {}, 'sort_by': sort_by}
        try:
            stocks = self.ak_data.get_concept_stocks(concept_name)
            if not stocks:
                result['error'] = f"未找到概念：{concept_name}"
                return result
            filtered_stocks = self._apply_filters(stocks, filters)
            sorted_stocks = self._apply_sort(filtered_stocks, sort_by)
            result['results'] = sorted_stocks[:limit]
            result['total'] = len(sorted_stocks)
            return result
        except Exception as e:
            result['error'] = str(e)
            return result

    def search_by_theme(self, theme: str, filters: Optional[Dict[str, Any]] = None,
                        sort_by: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        result = {'theme': theme, 'industry_results': None, 'concept_results': None, 'combined_results': []}
        try:
            industry_result = self.search_by_industry(theme, filters, sort_by, limit)
            concept_result = self.search_by_concept(theme, filters, sort_by, limit)
            result['industry_results'] = industry_result
            result['concept_results'] = concept_result

            all_stocks = []
            seen_codes = set()
            for src in [industry_result, concept_result]:
                if src.get('results'):
                    for stock in src['results']:
                        code = stock.get('代码', '') or stock.get('code', '')
                        if code and code not in seen_codes:
                            all_stocks.append(stock)
                            seen_codes.add(code)
            result['combined_results'] = all_stocks[:limit]
            return result
        except Exception as e:
            result['error'] = str(e)
            return result

    def _apply_filters(self, stocks: List[Dict], filters: Optional[Dict[str, Any]]) -> List[Dict]:
        if not filters:
            return stocks
        filtered = stocks
        if 'price_min' in filters or 'price_max' in filters:
            pmin = filters.get('price_min', 0)
            pmax = filters.get('price_max', float('inf'))
            filtered = [s for s in filtered if pmin <= s.get('最新价', s.get('price', 0)) <= pmax]
        if 'change_pct_min' in filters or 'change_pct_max' in filters:
            cmin = filters.get('change_pct_min', -float('inf'))
            cmax = filters.get('change_pct_max', float('inf'))
            filtered = [s for s in filtered if cmin <= s.get('涨跌幅', s.get('change_pct', 0)) <= cmax]
        return filtered

    def _apply_sort(self, stocks: List[Dict], sort_by: Optional[str]) -> List[Dict]:
        if not sort_by:
            return stocks
        parts = sort_by.split(':')
        field = parts[0]
        reverse = len(parts) > 1 and parts[1].lower() == 'desc'
        try:
            return sorted(stocks, key=lambda x: x.get(field, 0), reverse=reverse)
        except Exception:
            return stocks

    def get_all_industries(self) -> List[str]:
        try:
            return self.ak_data.get_all_industries()
        except Exception as e:
            logger.error("get_all_industries failed: %s", e)
            return []

    def get_all_concepts(self) -> List[str]:
        try:
            return self.ak_data.get_all_concepts()
        except Exception as e:
            logger.error("get_all_concepts failed: %s", e)
            return []

    def get_industries_summary(self, limit: int = 20) -> List[Dict[str, Any]]:
        # THS replacement: stock_board_industry_summary_ths (0.2s, 90 rows)
        try:
            import akshare as ak

            def _fetch():
                return ak.stock_board_industry_summary_ths()

            df = fetcher.fetch('industry_summary_ths', _fetch, ttl=1800)
            result = []
            for _, row in df.head(limit).iterrows():
                result.append({
                    'name': _safe_str(row.get('板块', '')),
                    'change_pct': _safe_float(row.get('涨跌幅', 0)),
                    'volume': _safe_float(row.get('总成交量', 0)),
                    'amount': _safe_float(row.get('总成交额', 0)),
                    'net_flow': _safe_float(row.get('净流入', 0)),
                    'up_count': _safe_int(row.get('上涨家数', 0)),
                    'down_count': _safe_int(row.get('下跌家数', 0)),
                    'avg_price': _safe_float(row.get('均价', 0)),
                    'leading_stock': _safe_str(row.get('领涨股', '')),
                    'leading_price': _safe_float(row.get('领涨股-最新价', 0)),
                    'leading_change': _safe_float(row.get('领涨股-涨跌幅', 0)),
                })
            return result
        except Exception as e:
            logger.error("get_industries_summary failed: %s", e)
            return []

    def get_concepts_summary(self, limit: int = 30) -> List[Dict[str, Any]]:
        # THS replacement: stock_board_concept_summary_ths (4s, 50 rows)
        try:
            import akshare as ak

            def _fetch():
                return ak.stock_board_concept_summary_ths()

            df = fetcher.fetch('concept_summary_ths', _fetch, ttl=1800)
            result = []
            for _, row in df.head(limit).iterrows():
                result.append({
                    'name': _safe_str(row.get('概念名称', '')),
                    'leading_stock': _safe_str(row.get('龙头股', '')),
                    'driver_event': _safe_str(row.get('驱动事件', '')),
                    'stock_count': _safe_int(row.get('成分股数量', 0)),
                })
            return result
        except Exception as e:
            logger.error("get_concepts_summary failed: %s", e)
            return []


search_engine = SearchEngine()
