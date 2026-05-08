import akshare as ak
import pandas as pd
import logging
from datetime import datetime
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
    if val is None or pd.isna(val):
        return default
    return str(val)


class AkShareData:

    def get_stock_basic_info(self, symbol: str) -> dict:
        try:
            stock_info = ak.stock_info_a_code_name()
            df = pd.DataFrame(stock_info, columns=['code', 'name'])
            stock = df[df['code'] == symbol]

            if stock.empty:
                return None

            industry = ''
            concept = ''
            region = ''
            full_name = ''

            try:
                detail_info = ak.stock_individual_info_em(symbol=symbol)
                if not detail_info.empty:
                    detail_dict = dict(zip(detail_info['item'], detail_info['value']))
                    industry = detail_dict.get('行业', '')
                    region = detail_dict.get('地区', '')
                    full_name = detail_dict.get('股票简称', '')
            except Exception as e:
                logger.warning("stock_individual_info_em failed for %s: %s", symbol, e)

            try:
                concepts = self.get_stock_concepts(symbol, limit=10)
                concept = '、'.join(concepts) if concepts else ''
            except Exception as e:
                logger.warning("get_stock_concepts failed for %s: %s", symbol, e)

            return {
                'code': symbol,
                'name': stock['name'].values[0],
                'full_name': full_name,
                'industry': industry,
                'concept': concept,
                'region': region,
                'market': '深市' if symbol.startswith('00') or symbol.startswith('30') else '沪市'
            }
        except Exception as e:
            logger.error("get_stock_basic_info failed for %s: %s", symbol, e)
            return None

    def get_stock_quote(self, symbol: str) -> dict:
        # Uses Sina source (stock_zh_a_spot) instead of blocked EM
        def _fetch_all():
            return ak.stock_zh_a_spot()

        try:
            df = fetcher.fetch('stock_zh_a_spot_sina', _fetch_all, ttl=1800)
            stock = df[df['代码'] == symbol]

            if stock.empty:
                return None

            return {
                'code': symbol,
                'name': _safe_str(stock['名称'].values[0]),
                'price': _safe_float(stock['最新价'].values[0]),
                'change': _safe_float(stock['涨跌额'].values[0]),
                'change_pct': _safe_float(stock['涨跌幅'].values[0]),
                'volume': _safe_float(stock['成交量'].values[0]),
                'amount': _safe_float(stock['成交额'].values[0]),
                'open': _safe_float(stock['今开'].values[0]),
                'high': _safe_float(stock['最高'].values[0]),
                'low': _safe_float(stock['最低'].values[0]),
                'previous_close': _safe_float(stock['昨收'].values[0]),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error("get_stock_quote failed for %s: %s", symbol, e)
            return None

    def get_stock_history_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            if symbol.startswith('00') or symbol.startswith('30'):
                ak_symbol = f"sz{symbol}"
            else:
                ak_symbol = f"sh{symbol}"

            return ak.stock_zh_a_hist(
                symbol=ak_symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
        except Exception as e:
            logger.error("get_stock_history_data failed: %s", e)
            return pd.DataFrame()

    def get_stock_financial_data(self, symbol: str, report_type: str = 'annual') -> pd.DataFrame:
        try:
            return ak.stock_financial_analysis_indicator(symbol=symbol)
        except Exception as e:
            logger.error("get_stock_financial_data failed: %s", e)
            return pd.DataFrame()

    def get_stock_valuation_data(self, symbol: str) -> dict:
        try:
            df = ak.stock_zh_valuation_baidu(symbol=symbol)
            if df.empty:
                return None

            result = {
                'code': symbol,
                'pe_ttm': _safe_float(df.get('市盈率(TTM)', pd.Series([0])).values[0]),
                'pe_lyr': _safe_float(df.get('市盈率(LYR)', pd.Series([0])).values[0]),
                'pb': _safe_float(df.get('市净率', pd.Series([0])).values[0]),
                'ps_ttm': _safe_float(df.get('市销率(TTM)', pd.Series([0])).values[0]),
                'pcf_ttm': _safe_float(df.get('市现率(TTM)', pd.Series([0])).values[0])
            }
            return result
        except Exception as e:
            logger.error("get_stock_valuation_data failed: %s", e)
            return None

    def get_industry_stocks(self, industry_name: str) -> list:
        # THS: returns industry summary (not constituent stock list)
        try:
            def _fetch():
                return ak.stock_board_industry_info_ths(symbol=industry_name)

            df = fetcher.fetch(
                f'industry_info_ths:{industry_name}',
                _fetch,
                ttl=1800
            )

            if df.empty:
                return []

            result = {}
            for _, row in df.iterrows():
                key = _safe_str(row.iloc[0])
                val = row.iloc[1] if len(row) > 1 else ''
                result[key] = val

            return [{
                'industry_name': industry_name,
                'detail': result
            }]
        except Exception as e:
            logger.error("get_industry_stocks failed for %s: %s", industry_name, e)
            return []

    def get_concept_stocks(self, concept_name: str) -> list:
        # THS: returns concept summary (not constituent stock list)
        try:
            def _fetch():
                return ak.stock_board_concept_summary_ths()

            df = fetcher.fetch('concept_summary_ths', _fetch, ttl=1800)

            matched = df[df['概念名称'] == concept_name]
            if matched.empty:
                return []

            row = matched.iloc[0]
            return [{
                'concept_name': concept_name,
                'driver_event': _safe_str(row.get('驱动事件', '')),
                'leading_stock': _safe_str(row.get('龙头股', '')),
                'stock_count': _safe_int(row.get('成分股数量', 0))
            }]
        except Exception as e:
            logger.error("get_concept_stocks failed for %s: %s", concept_name, e)
            return []

    def get_stock_concepts(self, symbol: str, limit: int = 5) -> list:
        # DEPRECATED: reverse lookup requires iterating all concepts — impractical
        return []

    def get_all_stocks(self) -> list:
        try:
            stock_info = ak.stock_info_a_code_name()
            df = pd.DataFrame(stock_info, columns=['code', 'name'])
            return df.to_dict('records')
        except Exception as e:
            logger.error("get_all_stocks failed: %s", e)
            return []

    def get_all_industries(self) -> list:
        # THS replacement for stock_board_industry_name_em
        try:
            def _fetch():
                return ak.stock_board_industry_name_ths()

            df = fetcher.fetch('industry_name_ths', _fetch, ttl=86400)
            return df['name'].tolist()
        except Exception as e:
            logger.error("get_all_industries failed: %s", e)
            return []

    def get_all_concepts(self) -> list:
        # THS replacement for stock_board_concept_name_em
        try:
            def _fetch():
                return ak.stock_board_concept_name_ths()

            df = fetcher.fetch('concept_name_ths', _fetch, ttl=86400)
            return df['name'].tolist()
        except Exception as e:
            logger.error("get_all_concepts failed: %s", e)
            return []


akshare_data = AkShareData()
