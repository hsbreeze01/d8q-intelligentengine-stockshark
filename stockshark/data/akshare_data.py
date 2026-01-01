import akshare as ak
import pandas as pd
from datetime import datetime

class AkShareData:
    """
    akshare数据源封装类，提供股票基本信息、行情数据、财务数据的获取功能
    """
    
    def __init__(self):
        pass
    
    def get_stock_basic_info(self, symbol: str) -> dict:
        """
        获取股票基本信息
        :param symbol: 股票代码，如 '000001' (深市) 或 '600000' (沪市)
        :return: 股票基本信息字典
        """
        try:
            # 获取全部股票基本信息
            stock_info = ak.stock_info_a_code_name()
            
            # 转换为DataFrame
            df = pd.DataFrame(stock_info, columns=['code', 'name'])
            
            # 查找指定股票
            stock = df[df['code'] == symbol]
            
            if stock.empty:
                return None
            
            # 获取更详细的股票信息
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
                print(f"获取详细信息失败: {e}")
            
            # 获取概念信息
            try:
                concepts = self.get_stock_concepts(symbol, limit=10)
                concept = '、'.join(concepts) if concepts else ''
            except Exception as e:
                print(f"获取概念信息失败: {e}")
            
            result = {
                'code': symbol,
                'name': stock['name'].values[0],
                'full_name': full_name,
                'industry': industry,
                'concept': concept,
                'region': region,
                'market': '深市' if symbol.startswith('00') or symbol.startswith('30') else '沪市'
            }
            
            return result
        except Exception as e:
            print(f"获取股票基本信息失败: {e}")
            return None
    
    def get_stock_quote(self, symbol: str) -> dict:
        """
        获取股票实时行情数据
        :param symbol: 股票代码，如 '000001' (深市) 或 '600000' (沪市)
        :return: 股票行情数据字典
        """
        try:
            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            
            # 查找指定股票
            stock = df[df['代码'] == symbol]
            
            if stock.empty:
                return None
            
            result = {
                'code': symbol,
                'name': stock['名称'].values[0],
                'price': stock['最新价'].values[0],
                'change': stock['涨跌额'].values[0],
                'change_pct': stock['涨跌幅'].values[0],
                'volume': stock['成交量'].values[0],
                'amount': stock['成交额'].values[0],
                'open': stock['今开'].values[0],
                'high': stock['最高'].values[0],
                'low': stock['最低'].values[0],
                'previous_close': stock['昨收'].values[0],
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return result
        except Exception as e:
            print(f"获取股票行情数据失败: {e}")
            return None
    
    def get_stock_history_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取股票历史行情数据
        :param symbol: 股票代码，如 '000001' (深市) 或 '600000' (沪市)
        :param start_date: 开始日期，格式 'YYYY-MM-DD'
        :param end_date: 结束日期，格式 'YYYY-MM-DD'
        :return: 股票历史行情数据DataFrame
        """
        try:
            # 构造股票代码（带交易所前缀）
            if symbol.startswith('00') or symbol.startswith('30'):
                ak_symbol = f"sz{symbol}"
            else:
                ak_symbol = f"sh{symbol}"
            
            # 获取历史数据
            df = ak.stock_zh_a_hist(
                symbol=ak_symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            return df
        except Exception as e:
            print(f"获取股票历史数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_financial_data(self, symbol: str, report_type: str = 'annual') -> pd.DataFrame:
        """
        获取股票财务数据
        :param symbol: 股票代码，如 '000001' (深市) 或 '600000' (沪市)
        :param report_type: 报告类型，'annual' (年报), 'quarterly' (季报)
        :return: 股票财务数据DataFrame
        """
        try:
            # 使用东方财富接口获取财务数据
            df = ak.stock_financial_analysis_indicator(symbol=symbol)
            
            return df
        except Exception as e:
            print(f"获取股票财务数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_valuation_data(self, symbol: str) -> dict:
        """
        获取股票估值数据
        :param symbol: 股票代码，如 '000001' (深市) 或 '600000' (沪市)
        :return: 股票估值数据字典
        """
        try:
            # 获取股票估值数据
            df = ak.stock_zh_valuation_baidu(symbol=symbol)
            
            if df.empty:
                return None
            
            result = {
                'code': symbol,
                'pe_ttm': df.get('市盈率(TTM)', pd.Series([0])).values[0] if '市盈率(TTM)' in df.columns else 0,
                'pe_lyr': df.get('市盈率(LYR)', pd.Series([0])).values[0] if '市盈率(LYR)' in df.columns else 0,
                'pb': df.get('市净率', pd.Series([0])).values[0] if '市净率' in df.columns else 0,
                'ps_ttm': df.get('市销率(TTM)', pd.Series([0])).values[0] if '市销率(TTM)' in df.columns else 0,
                'pcf_ttm': df.get('市现率(TTM)', pd.Series([0])).values[0] if '市现率(TTM)' in df.columns else 0
            }
            
            return result
        except Exception as e:
            print(f"获取股票估值数据失败: {e}")
            return None
    
    def get_industry_stocks(self, industry_name: str) -> list:
        """
        获取指定行业的所有股票
        :param industry_name: 行业名称
        :return: 行业股票列表
        """
        try:
            # 获取行业分类数据
            industry_df = ak.stock_board_industry_name_em()
            
            # 查找指定行业
            industry_info = industry_df[industry_df['板块名称'] == industry_name]
            
            if industry_info.empty:
                return []
            
            # 获取行业成分股
            stocks = ak.stock_board_industry_cons_em(symbol=industry_info['板块代码'].values[0])
            
            return stocks.to_dict('records')
        except Exception as e:
            print(f"获取行业股票数据失败: {e}")
            return []
    
    def get_concept_stocks(self, concept_name: str) -> list:
        """
        获取指定概念的所有股票
        :param concept_name: 概念名称
        :return: 概念股票列表
        """
        try:
            # 获取概念分类数据
            concept_df = ak.stock_board_concept_name_em()
            
            # 查找指定概念
            concept_info = concept_df[concept_df['板块名称'] == concept_name]
            
            if concept_info.empty:
                return []
            
            # 获取概念成分股
            stocks = ak.stock_board_concept_cons_em(symbol=concept_info['板块代码'].values[0])
            
            return stocks.to_dict('records')
        except Exception as e:
            print(f"获取概念股票数据失败: {e}")
            return []
    
    def get_stock_concepts(self, symbol: str, limit: int = 5) -> list:
        """
        获取股票所属的概念列表
        :param symbol: 股票代码
        :param limit: 返回概念数量限制
        :return: 概念名称列表
        """
        try:
            concepts = []
            
            # 获取所有概念板块
            concept_df = ak.stock_board_concept_name_em()
            
            # 遍历所有概念板块
            for idx, row in concept_df.iterrows():
                concept_name = row['板块名称']
                concept_code = row['板块代码']
                
                try:
                    # 获取该概念的成分股
                    cons_df = ak.stock_board_concept_cons_em(symbol=concept_code)
                    
                    # 检查是否包含目标股票
                    if not cons_df.empty and symbol in cons_df['代码'].values:
                        concepts.append(concept_name)
                        
                        if len(concepts) >= limit:
                            break
                except Exception as e:
                    continue
            
            return concepts
        except Exception as e:
            print(f"获取股票概念失败: {e}")
            return []
    
    def get_all_stocks(self) -> list:
        """
        获取所有A股股票列表
        :return: 所有A股股票列表
        """
        try:
            # 获取全部股票基本信息
            stock_info = ak.stock_info_a_code_name()
            
            # 转换为DataFrame
            df = pd.DataFrame(stock_info, columns=['code', 'name'])
            
            return df.to_dict('records')
        except Exception as e:
            print(f"获取所有股票数据失败: {e}")
            return []
    
    def get_all_industries(self) -> list:
        """
        获取所有行业列表
        :return: 行业名称列表
        """
        try:
            # 获取行业分类数据
            industry_df = ak.stock_board_industry_name_em()
            
            return industry_df['板块名称'].tolist()
        except Exception as e:
            print(f"获取行业列表失败: {e}")
            return []
    
    def get_all_concepts(self) -> list:
        """
        获取所有概念列表
        :return: 概念名称列表
        """
        try:
            # 获取概念分类数据
            concept_df = ak.stock_board_concept_name_em()
            
            return concept_df['板块名称'].tolist()
        except Exception as e:
            print(f"获取概念列表失败: {e}")
            return []

# 创建全局实例
akshare_data = AkShareData()
