"""股票数据服务层 - 优先从数据库查询，失败时触发实时获取并更新数据库"""
from datetime import datetime, timedelta
from stockshark.models.stock_basic_info import StockBasicInfo
from stockshark.models.stock_daily_trade import StockDailyTrade
from stockshark.data.akshare_data import AkShareData
from stockshark.utils.logger import get_logger

logger = get_logger(__name__)


class StockService:
    """股票数据服务"""
    
    def __init__(self):
        self.ak_data = AkShareData()
    
    def get_stock_basic_info(self, symbol):
        """
        获取股票基本信息（优先从数据库查询）
        
        Args:
            symbol: 股票代码
        
        Returns:
            dict: 股票基本信息
        """
        # 1. 先从数据库查询
        db_info = StockBasicInfo.get_by_symbol(symbol)
        
        if db_info:
            logger.info(f"从数据库获取股票 {symbol} 基本信息")
            return {
                'code': db_info['symbol'],
                'name': db_info['name'],
                'full_name': db_info.get('full_name', ''),
                'industry': db_info.get('industry', ''),
                'concept': db_info.get('concept', ''),
                'region': db_info.get('region', ''),
                'market': db_info.get('market', ''),
                'list_date': db_info.get('list_date'),
                'source': 'database'
            }
        
        # 2. 数据库中没有，从akshare获取
        logger.info(f"数据库中没有股票 {symbol}，从akshare获取...")
        api_info = self.ak_data.get_stock_basic_info(symbol)
        
        if api_info:
            # 3. 保存到数据库
            try:
                stock_basic = StockBasicInfo(
                    symbol=api_info['code'],
                    name=api_info['name'],
                    full_name=api_info.get('full_name', ''),
                    industry=api_info.get('industry', ''),
                    concept=api_info.get('concept', ''),
                    region=api_info.get('region', ''),
                    market=api_info.get('market', ''),
                    list_date=api_info.get('list_date')
                )
                stock_basic.save()
                logger.info(f"股票 {symbol} 基本信息已保存到数据库")
            except Exception as e:
                logger.error(f"保存股票 {symbol} 基本信息到数据库失败: {e}")
            
            api_info['source'] = 'api'
            return api_info
        
        return None
    
    def get_stock_daily_trade(self, symbol, trade_date=None):
        """
        获取股票每日交易数据（优先从数据库查询）
        
        Args:
            symbol: 股票代码
            trade_date: 交易日期，格式 YYYY-MM-DD，None表示最新交易日
        
        Returns:
            dict: 交易数据
        """
        # 1. 先从数据库查询
        if trade_date:
            db_trade = StockDailyTrade.get_by_symbol_and_date(symbol, trade_date)
        else:
            # 获取最新交易数据
            db_trade = StockDailyTrade.get_history_by_symbol(symbol, limit=1)
            db_trade = db_trade[0] if db_trade else None
        
        if db_trade:
            logger.info(f"从数据库获取股票 {symbol} 交易数据")
            return {
                'symbol': db_trade['symbol'],
                'trade_date': db_trade['trade_date'].strftime('%Y-%m-%d') if db_trade['trade_date'] else None,
                'open': float(db_trade['open_price']) if db_trade['open_price'] else None,
                'high': float(db_trade['high_price']) if db_trade['high_price'] else None,
                'low': float(db_trade['low_price']) if db_trade['low_price'] else None,
                'close': float(db_trade['close_price']) if db_trade['close_price'] else None,
                'volume': int(db_trade['volume']) if db_trade['volume'] else None,
                'amount': float(db_trade['amount']) if db_trade['amount'] else None,
                'change_pct': float(db_trade['change_pct']) if db_trade['change_pct'] else None,
                'turnover_rate': float(db_trade['turnover_rate']) if db_trade['turnover_rate'] else None,
                'source': 'database'
            }
        
        # 2. 数据库中没有，从akshare获取
        logger.info(f"数据库中没有股票 {symbol} 交易数据，从akshare获取...")
        
        if trade_date:
            start_date = trade_date
            end_date = trade_date
        else:
            start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        history_data = self.ak_data.get_stock_history_data(symbol, start_date, end_date)
        
        if history_data is not None and not history_data.empty:
            # 获取最新一条或指定日期的数据
            if trade_date:
                trade_row = history_data[history_data['日期'] == trade_date]
                if trade_row.empty:
                    return None
                trade_row = trade_row.iloc[0]
            else:
                trade_row = history_data.iloc[-1]
            
            # 3. 保存到数据库
            try:
                stock_trade = StockDailyTrade(
                    symbol=symbol,
                    trade_date=trade_row['日期'].date() if hasattr(trade_row['日期'], 'date') else trade_row['日期'],
                    open_price=float(trade_row['开盘']),
                    high_price=float(trade_row['最高']),
                    low_price=float(trade_row['最低']),
                    close_price=float(trade_row['收盘']),
                    volume=int(trade_row['成交量']),
                    amount=float(trade_row['成交额']),
                    change_pct=float(trade_row['涨跌幅']) if '涨跌幅' in trade_row else None,
                    turnover_rate=float(trade_row['换手率']) if '换手率' in trade_row else None
                )
                stock_trade.save()
                logger.info(f"股票 {symbol} 交易数据已保存到数据库")
            except Exception as e:
                logger.error(f"保存股票 {symbol} 交易数据到数据库失败: {e}")
            
            return {
                'symbol': symbol,
                'trade_date': trade_row['日期'].strftime('%Y-%m-%d') if hasattr(trade_row['日期'], 'strftime') else str(trade_row['日期']),
                'open': float(trade_row['开盘']),
                'high': float(trade_row['最高']),
                'low': float(trade_row['最低']),
                'close': float(trade_row['收盘']),
                'volume': int(trade_row['成交量']),
                'amount': float(trade_row['成交额']),
                'change_pct': float(trade_row['涨跌幅']) if '涨跌幅' in trade_row else None,
                'turnover_rate': float(trade_row['换手率']) if '换手率' in trade_row else None,
                'source': 'api'
            }
        
        return None
    
    def get_stock_history(self, symbol, start_date, end_date):
        """
        获取股票历史行情数据（优先从数据库查询）
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            list: 历史数据列表
        """
        # 1. 先从数据库查询
        db_history = StockDailyTrade.get_history_by_symbol(symbol, start_date, end_date, limit=1000)
        
        if db_history:
            logger.info(f"从数据库获取股票 {symbol} 历史数据，共 {len(db_history)} 条")
            return [{
                '日期': item['trade_date'].strftime('%Y-%m-%d') if item['trade_date'] else None,
                '开盘': float(item['open_price']) if item['open_price'] else None,
                '最高': float(item['high_price']) if item['high_price'] else None,
                '最低': float(item['low_price']) if item['low_price'] else None,
                '收盘': float(item['close_price']) if item['close_price'] else None,
                '成交量': int(item['volume']) if item['volume'] else None,
                '成交额': float(item['amount']) if item['amount'] else None,
                '涨跌幅': float(item['change_pct']) if item['change_pct'] else None,
                '换手率': float(item['turnover_rate']) if item['turnover_rate'] else None,
                'source': 'database'
            } for item in db_history]
        
        # 2. 数据库中没有，从akshare获取
        logger.info(f"数据库中没有股票 {symbol} 历史数据，从akshare获取...")
        api_history = self.ak_data.get_stock_history_data(symbol, start_date, end_date)
        
        if api_history is not None and not api_history.empty:
            # 3. 批量保存到数据库
            try:
                trade_records = []
                for _, row in api_history.iterrows():
                    trade_date = row['日期']
                    if hasattr(trade_date, 'date'):
                        trade_date = trade_date.date()
                    trade_records.append({
                        'symbol': symbol,
                        'trade_date': trade_date,
                        'open_price': float(row['开盘']),
                        'high_price': float(row['最高']),
                        'low_price': float(row['最低']),
                        'close_price': float(row['收盘']),
                        'volume': int(row['成交量']),
                        'amount': float(row['成交额']),
                        'change_pct': float(row['涨跌幅']) if '涨跌幅' in row else None,
                        'turnover_rate': float(row['换手率']) if '换手率' in row else None
                    })
                
                StockDailyTrade.batch_save(trade_records)
                logger.info(f"股票 {symbol} 历史数据已保存到数据库，共 {len(trade_records)} 条")
            except Exception as e:
                logger.error(f"保存股票 {symbol} 历史数据到数据库失败: {e}")
            
            return api_history.to_dict('records')
        
        return []
    
    def get_stock_sectors(self, symbol):
        """
        获取股票所属的行业和概念信息（优先从数据库查询）
        
        Args:
            symbol: 股票代码
        
        Returns:
            dict: 行业和概念信息
        """
        # 1. 先从数据库查询基本信息
        db_info = StockBasicInfo.get_by_symbol(symbol)
        
        industry_name = ''
        concept_str = ''
        stock_name = ''
        
        if db_info:
            industry_name = db_info.get('industry', '')
            concept_str = db_info.get('concept', '')
            stock_name = db_info.get('name', '')
            logger.info(f"从数据库获取股票 {symbol} 行业和概念信息")
        else:
            # 2. 数据库中没有，从akshare获取
            logger.info(f"数据库中没有股票 {symbol}，从akshare获取...")
            api_info = self.ak_data.get_stock_basic_info(symbol)
            
            if api_info:
                industry_name = api_info.get('industry', '')
                concept_str = api_info.get('concept', '')
                stock_name = api_info.get('name', '')
                
                # 3. 保存到数据库
                try:
                    stock_basic = StockBasicInfo(
                        symbol=api_info['code'],
                        name=api_info['name'],
                        full_name=api_info.get('full_name', ''),
                        industry=industry_name,
                        concept=concept_str,
                        region=api_info.get('region', ''),
                        market=api_info.get('market', ''),
                        list_date=api_info.get('list_date')
                    )
                    stock_basic.save()
                    logger.info(f"股票 {symbol} 基本信息已保存到数据库")
                except Exception as e:
                    logger.error(f"保存股票 {symbol} 基本信息到数据库失败: {e}")
        
        # 获取行业详细信息
        industry_stocks = []
        if industry_name:
            industry_stocks = self.ak_data.get_industry_stocks(industry_name)
        
        # 获取概念详细信息
        concepts = []
        if concept_str:
            concept_list = [c.strip() for c in concept_str.split('、') if c.strip()]
            for concept_name in concept_list[:5]:
                concept_stocks = self.ak_data.get_concept_stocks(concept_name)
                if concept_stocks:
                    concepts.append({
                        'name': concept_name,
                        'stock_count': len(concept_stocks)
                    })
        
        return {
            'symbol': symbol,
            'name': stock_name,
            'industry': {
                'name': industry_name,
                'stock_count': len(industry_stocks)
            },
            'concepts': concepts
        }


# 全局实例
stock_service = StockService()
