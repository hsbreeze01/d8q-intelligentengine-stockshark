import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any

class DataProcessor:
    """
    数据处理类，提供数据清洗、转换和整合功能
    """
    
    def __init__(self):
        pass
    
    def clean_stock_quote(self, quote_data: dict) -> dict:
        """
        清洗股票行情数据
        :param quote_data: 原始行情数据字典
        :return: 清洗后的行情数据字典
        """
        if not quote_data:
            return {}
        
        # 移除空值或None值
        cleaned = {k: v for k, v in quote_data.items() if v is not None and v != 'None'}
        
        # 转换数值类型
        numeric_fields = ['price', 'change', 'change_pct', 'volume', 'amount', 'open', 'high', 'low', 'previous_close']
        for field in numeric_fields:
            if field in cleaned:
                try:
                    cleaned[field] = float(cleaned[field])
                except:
                    cleaned[field] = 0.0
        
        # 转换成交量为万股
        if 'volume' in cleaned:
            cleaned['volume'] = cleaned['volume'] / 100
        
        # 转换成交额为亿元
        if 'amount' in cleaned:
            cleaned['amount'] = cleaned['amount'] / 100000000
        
        return cleaned
    
    def clean_stock_history(self, history_df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗股票历史行情数据
        :param history_df: 原始历史行情DataFrame
        :return: 清洗后的历史行情DataFrame
        """
        if history_df.empty:
            return pd.DataFrame()
        
        # 复制数据
        df = history_df.copy()
        
        # 重命名列
        df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount']
        
        # 转换日期类型
        df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
        
        # 转换数值类型
        numeric_fields = ['open', 'close', 'high', 'low', 'volume', 'amount']
        for field in numeric_fields:
            df[field] = pd.to_numeric(df[field], errors='coerce')
        
        # 处理缺失值
        df = df.dropna(subset=['open', 'close', 'high', 'low'])
        
        # 处理异常值（比如收盘价为0的情况）
        df = df[df['close'] > 0]
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        return df
    
    def calculate_technical_indicators(self, history_df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        :param history_df: 清洗后的历史行情DataFrame
        :return: 添加了技术指标的DataFrame
        """
        if history_df.empty:
            return pd.DataFrame()
        
        # 复制数据
        df = history_df.copy()
        
        # 计算涨跌幅
        df['change_pct'] = (df['close'] - df['open']) / df['open'] * 100
        
        # 计算5日、10日、20日移动平均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        
        # 计算成交量5日、10日移动平均线
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_ma10'] = df['volume'].rolling(window=10).mean()
        
        # 计算MACD指标
        df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['dif'] = df['ema12'] - df['ema26']
        df['dea'] = df['dif'].ewm(span=9, adjust=False).mean()
        df['macd'] = (df['dif'] - df['dea']) * 2
        
        # 计算RSI指标
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    def clean_financial_data(self, financial_df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗财务数据
        :param financial_df: 原始财务数据DataFrame
        :return: 清洗后的财务数据DataFrame
        """
        if financial_df.empty:
            return pd.DataFrame()
        
        # 复制数据
        df = financial_df.copy()
        
        # 移除空列
        df = df.dropna(axis=1, how='all')
        
        # 转换数值类型
        for col in df.columns:
            if col != '报告期':
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 处理缺失值
        df = df.fillna(0)
        
        return df
    
    def calculate_financial_ratios(self, financial_df: pd.DataFrame) -> pd.DataFrame:
        """
        计算财务比率
        :param financial_df: 清洗后的财务数据DataFrame
        :return: 添加了财务比率的DataFrame
        """
        if financial_df.empty:
            return pd.DataFrame()
        
        # 复制数据
        df = financial_df.copy()
        
        # 计算盈利能力比率
        if '营业收入' in df.columns and '营业成本' in df.columns:
            df['毛利率'] = (df['营业收入'] - df['营业成本']) / df['营业收入'] * 100
        
        if '净利润' in df.columns and '营业收入' in df.columns:
            df['净利率'] = df['净利润'] / df['营业收入'] * 100
        
        if '净利润' in df.columns and '净资产' in df.columns:
            df['净资产收益率'] = df['净利润'] / df['净资产'] * 100
        
        # 计算偿债能力比率
        if '负债合计' in df.columns and '资产总计' in df.columns:
            df['资产负债率'] = df['负债合计'] / df['资产总计'] * 100
        
        if '流动资产' in df.columns and '流动负债' in df.columns:
            df['流动比率'] = df['流动资产'] / df['流动负债']
        
        # 计算运营能力比率
        if '营业收入' in df.columns and '总资产' in df.columns:
            df['总资产周转率'] = df['营业收入'] / df['总资产']
        
        return df
    
    def integrate_stock_data(self, basic_info: dict, quote_data: dict, valuation_data: dict) -> dict:
        """
        整合股票数据
        :param basic_info: 基本信息
        :param quote_data: 行情数据
        :param valuation_data: 估值数据
        :return: 整合后的股票数据
        """
        integrated = {}
        
        # 合并基本信息
        if basic_info:
            integrated.update(basic_info)
        
        # 合并行情数据
        if quote_data:
            integrated.update(quote_data)
        
        # 合并估值数据
        if valuation_data:
            integrated.update(valuation_data)
        
        return integrated
    
    def process_supply_chain_data(self, supply_chain_list: List[Dict]) -> List[Dict]:
        """
        处理供应链数据
        :param supply_chain_list: 原始供应链数据列表
        :return: 处理后的供应链数据列表
        """
        processed = []
        
        for item in supply_chain_list:
            # 清洗数据
            cleaned = {
                'company_name': item.get('company_name', ''),
                'company_code': item.get('company_code', ''),
                'relationship': item.get('relationship', ''),
                'supply_type': item.get('supply_type', 'direct'),  # direct或indirect
                'is_listed': item.get('is_listed', False),
                'listed_company': item.get('listed_company', ''),
                'stock_code': item.get('stock_code', ''),
                'industry': item.get('industry', '')
            }
            
            # 标准化关系类型
            if 'supplier' in cleaned['relationship'].lower():
                cleaned['relationship_type'] = 'supplier'
            elif 'customer' in cleaned['relationship'].lower():
                cleaned['relationship_type'] = 'customer'
            else:
                cleaned['relationship_type'] = 'other'
            
            processed.append(cleaned)
        
        return processed
    
    def calculate_investment_score(self, stock_data: dict) -> Dict[str, Any]:
        """计算投资价值评分 — 4 因子加权（估值30 + 成长30 + 技术20 + 行业20）"""
        score = 0
        factors = []

        # ── 估值因子（30分）──
        valuation_score = 0
        pe = stock_data.get('pe_ttm') or stock_data.get('pe_lyr')
        pb = stock_data.get('pb')
        if pe and pe > 0:
            if pe < 10:
                valuation_score = 30
                factors.append(f'低市盈率（PE={pe:.1f}）')
            elif pe < 15:
                valuation_score = 25
                factors.append(f'合理偏低市盈率（PE={pe:.1f}）')
            elif pe < 25:
                valuation_score = 18
                factors.append(f'合理市盈率（PE={pe:.1f}）')
            elif pe < 40:
                valuation_score = 10
                factors.append(f'偏高市盈率（PE={pe:.1f}）')
            else:
                valuation_score = 3
                factors.append(f'高市盈率（PE={pe:.1f}）')
        else:
            valuation_score = 5
            factors.append('估值数据缺失')
        if pb and pb > 0 and pb < 1:
            valuation_score = min(valuation_score + 5, 30)
            factors.append(f'破净（PB={pb:.2f}）')

        # ── 成长因子（30分）── 基于财务数据
        growth_score = 10  # 基础分
        roe = stock_data.get('roe')
        rev_growth = stock_data.get('revenue_growth')
        eps = stock_data.get('eps')
        if roe and roe > 0:
            if roe > 20:
                growth_score += 15
                factors.append(f'高ROE（{roe:.1f}%）')
            elif roe > 12:
                growth_score += 10
                factors.append(f'良好ROE（{roe:.1f}%）')
            elif roe > 6:
                growth_score += 5
                factors.append(f'一般ROE（{roe:.1f}%）')
        if rev_growth:
            if rev_growth > 20:
                growth_score += 5
                factors.append(f'高营收增长（{rev_growth:.1f}%）')
            elif rev_growth > 5:
                growth_score += 3
                factors.append(f'正营收增长（{rev_growth:.1f}%）')
            elif rev_growth < -10:
                growth_score -= 3
                factors.append(f'营收下滑（{rev_growth:.1f}%）')
        growth_score = max(0, min(30, growth_score))

        # ── 技术因子（20分）── 基于 DB 指标
        technical_score = 10  # 基础分
        rsi = stock_data.get('rsi_6')
        kdj_k = stock_data.get('kdj_k')
        macd_dif = stock_data.get('macd_dif')
        ma5 = stock_data.get('ma5')
        ma20 = stock_data.get('ma20')
        close = stock_data.get('close') or stock_data.get('price')
        if rsi is not None:
            if rsi < 30:
                technical_score += 5
                factors.append(f'RSI超卖区（{rsi:.1f}）')
            elif rsi < 45:
                technical_score += 3
                factors.append(f'RSI低位（{rsi:.1f}）')
            elif rsi > 70:
                technical_score -= 3
                factors.append(f'RSI超买区（{rsi:.1f}）')
        if kdj_k is not None and kdj_k < 20:
            technical_score += 3
            factors.append(f'KDJ低位（K={kdj_k:.1f}）')
        if macd_dif is not None and macd_dif > 0:
            technical_score += 2
            factors.append('MACD金叉区间')
        if close and ma5 and ma20:
            if close > ma5 > ma20:
                technical_score += 3
                factors.append('均线多头排列')
            elif close < ma5 < ma20:
                technical_score -= 3
                factors.append('均线空头排列')
        technical_score = max(0, min(20, technical_score))

        # ── 行业因子（20分）──
        industry_score = 10  # 基础分
        if stock_data.get('industry'):
            industry_score = 10
            factors.append(f'{stock_data["industry"]}行业评估')

        total_score = valuation_score + growth_score + technical_score + industry_score

        if total_score >= 80:
            rating = '优秀'
        elif total_score >= 60:
            rating = '良好'
        elif total_score >= 40:
            rating = '一般'
        else:
            rating = '较差'

        return {
            'total_score': total_score,
            'rating': rating,
            'valuation_score': valuation_score,
            'growth_score': growth_score,
            'technical_score': technical_score,
            'industry_score': industry_score,
            'factors': factors
        }
    
    def calculate_risk_score(self, stock_data: dict) -> Dict[str, Any]:
        """计算风险评分 — 多维度风险判定"""
        risk_level = 'low'
        risk_factors = []

        # 估值风险
        pe = stock_data.get('pe_ttm') or stock_data.get('pe_lyr')
        if pe and pe > 50:
            risk_factors.append(f'高估值风险（PE={pe:.1f}）')
        elif pe and pe > 0 and pe < 5:
            risk_factors.append(f'极低估值警惕（PE={pe:.1f}，可能盈利异常）')

        pb = stock_data.get('pb')
        if pb and pb > 10:
            risk_factors.append(f'高市净率风险（PB={pb:.1f}）')

        # 波动率风险
        change_pct = stock_data.get('change_pct')
        amplitude = stock_data.get('amplitude')
        if change_pct and abs(change_pct) > 7:
            risk_factors.append(f'高波动率（涨跌幅={change_pct:.2f}%）')
        if amplitude and amplitude > 8:
            risk_factors.append(f'高振幅（{amplitude:.2f}%）')

        # 技术面风险
        rsi = stock_data.get('rsi_6')
        if rsi is not None and rsi > 80:
            risk_factors.append(f'RSI严重超买（{rsi:.1f}）')
        elif rsi is not None and rsi < 15:
            risk_factors.append(f'RSI严重超卖（{rsi:.1f}）')

        kdj_j = stock_data.get('kdj_j')
        if kdj_j is not None and kdj_j > 100:
            risk_factors.append(f'KDJ超买（J={kdj_j:.1f}）')

        # 财务风险
        roe = stock_data.get('roe')
        if roe is not None and roe < 0:
            risk_factors.append(f'ROE为负（{roe:.1f}%）')

        # 行业风险
        if stock_data.get('industry'):
            risk_factors.append(f'{stock_data["industry"]}行业风险')

        # 确定风险等级
        risk_count = len(risk_factors)
        if risk_count >= 4:
            risk_level = 'high'
        elif risk_count >= 2:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        return {
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'risk_count': risk_count
        }

# 创建全局实例
data_processor = DataProcessor()
