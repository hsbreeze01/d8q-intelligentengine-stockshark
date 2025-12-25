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
        """
        计算投资价值评分
        :param stock_data: 整合后的股票数据
        :return: 投资价值评分结果
        """
        score = 0
        factors = []
        
        # 估值因子（30分）
        valuation_score = 0
        if 'pe_ttm' in stock_data:
            pe = stock_data['pe_ttm']
            if pe > 0 and pe < 10:
                valuation_score = 30
                factors.append('低市盈率（PE<10）')
            elif pe >= 10 and pe < 20:
                valuation_score = 20
                factors.append('合理市盈率（10≤PE<20）')
            elif pe >= 20 and pe < 30:
                valuation_score = 10
                factors.append('较高市盈率（20≤PE<30）')
        
        # 成长因子（30分）
        growth_score = 0
        # 这里可以根据财务数据计算成长率，暂时给默认值
        growth_score = 15
        factors.append('成长潜力评估')
        
        # 技术因子（20分）
        technical_score = 0
        # 这里可以根据技术指标计算，暂时给默认值
        technical_score = 10
        factors.append('技术形态评估')
        
        # 行业因子（20分）
        industry_score = 0
        if 'industry' in stock_data:
            # 这里可以根据行业前景评分，暂时给默认值
            industry_score = 10
            factors.append('行业前景评估')
        
        # 总分
        total_score = valuation_score + growth_score + technical_score + industry_score
        
        # 评级
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
        """
        计算风险评分
        :param stock_data: 整合后的股票数据
        :return: 风险评分结果
        """
        risk_level = 'medium'
        risk_factors = []
        
        # 估值风险
        if 'pe_ttm' in stock_data:
            pe = stock_data['pe_ttm']
            if pe > 50:
                risk_factors.append(f'高估值风险（PE={pe}）')
        
        # 波动率风险
        if 'change_pct' in stock_data:
            if abs(stock_data['change_pct']) > 7:
                risk_factors.append(f'高波动率风险（涨跌幅={stock_data["change_pct"]}%）')
        
        # 行业风险
        if 'industry' in stock_data:
            risk_factors.append(f'{stock_data["industry"]}行业风险')
        
        # 确定风险等级
        if len(risk_factors) >= 3:
            risk_level = 'high'
        elif len(risk_factors) == 0:
            risk_level = 'low'
        else:
            risk_level = 'medium'
        
        return {
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'risk_count': len(risk_factors)
        }

# 创建全局实例
data_processor = DataProcessor()
