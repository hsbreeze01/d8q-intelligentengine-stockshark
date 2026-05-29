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
        """获取股票行情 — DB 优先，AkShare 降级"""
        # 1. 从 DB 获取最新行情
        try:
            from stockshark.utils.database import get_mysql_connection
            conn = get_mysql_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM stock_data_daily WHERE stock_code = %s ORDER BY date DESC LIMIT 1",
                    (symbol,)
                )
                row = cursor.fetchone()
                if row and row.get('close'):
                    # 获取名称
                    name = ''
                    try:
                        cursor.execute("SELECT name FROM stock_basic WHERE code = %s", (symbol,))
                        nr = cursor.fetchone()
                        if nr:
                            name = _safe_str(nr.get('name', ''))
                    except Exception:
                        pass
                    return {
                        'code': symbol,
                        'name': name,
                        'price': _safe_float(row.get('close')),
                        'change': _safe_float(row.get('change_amount')),
                        'change_pct': _safe_float(row.get('change_percentage')),
                        'volume': _safe_float(row.get('volume')),
                        'amount': _safe_float(row.get('turnover')),
                        'open': _safe_float(row.get('open')),
                        'high': _safe_float(row.get('high')),
                        'low': _safe_float(row.get('low')),
                        'previous_close': _safe_float(row.get('close', 0)) - _safe_float(row.get('change_amount', 0)),
                        'turnover_rate': _safe_float(row.get('turnover_rate')),
                        'amplitude': _safe_float(row.get('amplitude')),
                        'update_time': str(row.get('date', ''))
                    }
            finally:
                conn.close()
        except Exception as e:
            logger.warning("DB quote failed for %s: %s, trying AkShare", symbol, e)

        # 2. AkShare 降级 (Sina)
        try:
            df = fetcher.fetch('stock_zh_a_spot_sina', lambda: ak.stock_zh_a_spot(), ttl=1800)
            stock = df[df['代码'] == symbol]
            if not stock.empty:
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
            logger.warning("AkShare quote also failed for %s: %s", symbol, e)

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
        """获取估值数据 — 获取价格后用 AkShare 财务指标算 PE/PB"""
        result = {'code': symbol, 'pe_ttm': 0.0, 'pe_lyr': 0.0, 'pb': 0.0, 'ps_ttm': 0.0, 'pcf_ttm': 0.0}
        price = 0.0

        # 1. 从 DB 获取最新收盘价
        try:
            from stockshark.utils.database import get_mysql_connection
            conn = get_mysql_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT close FROM stock_data_daily WHERE stock_code=%s ORDER BY date DESC LIMIT 1",
                    (symbol,)
                )
                price_row = cursor.fetchone()
                if price_row and price_row.get('close'):
                    price = float(price_row['close'])
            finally:
                conn.close()
        except Exception as e:
            logger.warning("DB price fetch failed for %s: %s", symbol, e)

        # 2. 用 AkShare 财务指标算 PE/PB
        if price > 0:
            result = self._valuation_from_akshare_financial(symbol, price, result)

        return result

    def _valuation_from_akshare_financial(self, symbol: str, price: float, result: dict) -> dict:
        """从 AkShare 财务指标接口计算 PE/PB"""
        try:
            df = ak.stock_financial_analysis_indicator(symbol=symbol)
            if df is None or df.empty:
                return result

            # 跳过第一行 (1900-01-01 哨兵)
            # 从最新报告期开始遍历
            for i in range(len(df) - 1, max(len(df) - 15, -1), -1):
                if i < 0:
                    break
                row = df.iloc[i]
                dt = str(row.get('日期', ''))
                if dt.startswith('1900'):
                    continue
                eps = _safe_float(row.get('摊薄每股收益(元)'), 0)
                bvps = _safe_float(row.get('每股净资产_调整前(元)'), 0)
                if eps > 0:
                    result['pe_lyr'] = round(price / eps, 2)
                    result['pe_ttm'] = result['pe_lyr']  # 简化
                if bvps > 0:
                    result['pb'] = round(price / bvps, 2)
                if result['pe_lyr'] > 0 or result['pb'] > 0:
                    result['financial_date'] = dt
                    break
        except Exception as e:
            logger.warning("_valuation_from_akshare_financial failed for %s: %s", symbol, e)
        return result

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
