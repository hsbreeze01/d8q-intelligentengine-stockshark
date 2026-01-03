"""股票数据爬取模块"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from stockshark.utils.logger import get_logger
from stockshark.models.stock_basic_info import StockBasicInfo
from stockshark.models.stock_daily_trade import StockDailyTrade

logger = get_logger(__name__)


class StockDataCrawler:
    """股票数据爬取器"""
    
    def __init__(self):
        self.logger = logger
    
    def fetch_all_stock_list(self):
        """
        获取所有A股股票列表
        
        Returns:
            list: 股票列表，每个元素为包含code和name的字典
        """
        try:
            self.logger.info("开始获取所有A股股票列表...")
            stock_list = ak.stock_info_a_code_name()
            df = pd.DataFrame(stock_list, columns=['code', 'name'])
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': row['code'],
                    'name': row['name']
                })
            
            self.logger.info(f"成功获取 {len(stocks)} 只股票")
            return stocks
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            return []
    
    def fetch_stock_basic_info(self, symbol):
        """
        获取单只股票的基本信息（行业、概念等）
        
        Args:
            symbol: 股票代码
        
        Returns:
            dict: 股票基本信息
        """
        try:
            self.logger.info(f"获取股票 {symbol} 的基本信息...")
            
            name = ''
            industry = ''
            concept = ''
            region = ''
            full_name = ''
            list_date = None
            
            try:
                detail_info = ak.stock_individual_info_em(symbol=symbol)
                if not detail_info.empty:
                    detail_dict = dict(zip(detail_info['item'], detail_info['value']))
                    name = detail_dict.get('股票简称', '')
                    full_name = detail_dict.get('股票简称', '')
                    industry = detail_dict.get('行业', '')
                    region = detail_dict.get('地区', '')
                    list_date_str = detail_dict.get('上市日期', '')
                    if list_date_str:
                        try:
                            list_date = datetime.strptime(list_date_str, '%Y-%m-%d').date()
                        except:
                            pass
            except Exception as e:
                self.logger.warning(f"获取股票 {symbol} 详细信息失败: {e}")
            
            if not name:
                self.logger.warning(f"股票 {symbol} 不存在或无法获取信息")
                return None
            
            try:
                concepts = self._fetch_stock_concepts(symbol, limit=10)
                concept = '、'.join(concepts) if concepts else ''
            except Exception as e:
                self.logger.warning(f"获取股票 {symbol} 概念信息失败: {e}")
            
            market = '深市' if symbol.startswith('00') or symbol.startswith('30') else '沪市'
            
            result = {
                'symbol': symbol,
                'name': name,
                'full_name': full_name,
                'industry': industry,
                'concept': concept,
                'region': region,
                'market': market,
                'list_date': list_date
            }
            
            return result
        except Exception as e:
            self.logger.error(f"获取股票 {symbol} 基本信息失败: {e}")
            return None
    
    def _fetch_stock_concepts(self, symbol, limit=5):
        """
        获取股票所属的概念列表
        
        Args:
            symbol: 股票代码
            limit: 返回概念数量限制
        
        Returns:
            list: 概念名称列表
        """
        try:
            concepts = []
            
            concept_df = ak.stock_board_concept_name_em()
            
            for idx, row in concept_df.iterrows():
                concept_name = row['板块名称']
                concept_code = row['板块代码']
                
                try:
                    cons_df = ak.stock_board_concept_cons_em(symbol=concept_code)
                    
                    if not cons_df.empty and symbol in cons_df['代码'].values:
                        concepts.append(concept_name)
                        
                        if len(concepts) >= limit:
                            break
                except Exception as e:
                    continue
            
            return concepts
        except Exception as e:
            self.logger.error(f"获取股票 {symbol} 概念失败: {e}")
            return []
    
    def fetch_stock_daily_trade(self, symbol, start_date=None, end_date=None):
        """
        获取股票每日交易数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期，格式 YYYY-MM-DD
            end_date: 结束日期，格式 YYYY-MM-DD
        
        Returns:
            list: 交易数据列表
        """
        try:
            self.logger.info(f"获取股票 {symbol} 的交易数据...")
            
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            else:
                start_date = start_date.replace('-', '')
            
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            else:
                end_date = end_date.replace('-', '')
            
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                    start_date=start_date, end_date=end_date, adjust="qfq")
            
            if df.empty:
                self.logger.warning(f"股票 {symbol} 没有交易数据")
                return []
            
            trades = []
            for _, row in df.iterrows():
                trade = {
                    'symbol': symbol,
                    'trade_date': row['日期'].date() if hasattr(row['日期'], 'date') else row['日期'],
                    'open_price': float(row['开盘']),
                    'high_price': float(row['最高']),
                    'low_price': float(row['最低']),
                    'close_price': float(row['收盘']),
                    'volume': int(row['成交量']),
                    'amount': float(row['成交额']),
                    'change_pct': float(row['涨跌幅']) if '涨跌幅' in row else None,
                    'turnover_rate': float(row['换手率']) if '换手率' in row else None
                }
                trades.append(trade)
            
            self.logger.info(f"成功获取股票 {symbol} 的 {len(trades)} 条交易数据")
            return trades
        except Exception as e:
            self.logger.error(f"获取股票 {symbol} 交易数据失败: {e}")
            return []
    
    def crawl_all_stock_basic_info(self, limit=None, offset=None):
        """
        爬取所有股票的基本信息并保存到数据库
        
        Args:
            limit: 限制爬取的股票数量，None表示全部
            offset: 从第几只股票开始爬取（0-based），None表示从第一只开始
        
        Returns:
            tuple: (成功数量, 失败数量)
        """
        self.logger.info("开始爬取所有股票基本信息...")
        
        stocks = self.fetch_all_stock_list()
        if offset is not None:
            stocks = stocks[offset:]
        if limit:
            stocks = stocks[:limit]
        
        success_count = 0
        fail_count = 0
        
        for idx, stock in enumerate(stocks, 1):
            actual_idx = idx + offset if offset else idx
            self.logger.info(f"进度: {actual_idx}/{len(stocks) + (offset if offset else 0)} - 处理股票 {stock['code']}")
            
            basic_info = self.fetch_stock_basic_info(stock['code'])
            if basic_info:
                stock_basic = StockBasicInfo(
                    symbol=basic_info['symbol'],
                    name=basic_info['name'],
                    full_name=basic_info.get('full_name', ''),
                    industry=basic_info.get('industry', ''),
                    concept=basic_info.get('concept', ''),
                    region=basic_info.get('region', ''),
                    market=basic_info.get('market', ''),
                    list_date=basic_info.get('list_date')
                )
                
                if stock_basic.save():
                    success_count += 1
                else:
                    fail_count += 1
            else:
                fail_count += 1
        
        self.logger.info(f"爬取完成: 成功 {success_count} 只, 失败 {fail_count} 只")
        return success_count, fail_count
    
    def crawl_stock_daily_trade(self, symbol, start_date=None, end_date=None):
        """
        爬取单只股票的每日交易数据并保存到数据库
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            int: 成功保存的交易记录数
        """
        trades = self.fetch_stock_daily_trade(symbol, start_date, end_date)
        
        if not trades:
            return 0
        
        success_count = 0
        for trade in trades:
            stock_trade = StockDailyTrade(
                symbol=trade['symbol'],
                trade_date=trade['trade_date'],
                open_price=trade['open_price'],
                high_price=trade['high_price'],
                low_price=trade['low_price'],
                close_price=trade['close_price'],
                volume=trade['volume'],
                amount=trade['amount'],
                change_pct=trade.get('change_pct'),
                turnover_rate=trade.get('turnover_rate')
            )
            
            if stock_trade.save():
                success_count += 1
        
        return success_count
    
    def crawl_all_stock_daily_trade(self, start_date=None, end_date=None, limit=None):
        """
        爬取所有股票的每日交易数据并保存到数据库
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制爬取的股票数量，None表示全部
        
        Returns:
            tuple: (成功数量, 失败数量)
        """
        self.logger.info("开始爬取所有股票交易数据...")
        
        stocks = StockBasicInfo.get_all_symbols()
        if not stocks:
            self.logger.warning("数据库中没有股票基本信息，请先爬取股票基本信息")
            return 0, 0
        
        if limit:
            stocks = stocks[:limit]
        
        success_count = 0
        fail_count = 0
        
        for idx, symbol in enumerate(stocks, 1):
            self.logger.info(f"进度: {idx}/{len(stocks)} - 处理股票 {symbol}")
            
            count = self.crawl_stock_daily_trade(symbol, start_date, end_date)
            if count > 0:
                success_count += count
            else:
                fail_count += 1
        
        self.logger.info(f"爬取完成: 成功 {success_count} 条记录, 失败 {fail_count} 只股票")
        return success_count, fail_count
    
    def crawl_today_trade_data(self):
        """
        爬取今日交易数据（用于定时任务）
        
        Returns:
            tuple: (成功数量, 失败数量)
        """
        today = datetime.now().strftime('%Y-%m-%d')
        self.logger.info(f"开始爬取今日 {today} 的交易数据...")
        
        stocks = StockBasicInfo.get_all_symbols()
        if not stocks:
            self.logger.warning("数据库中没有股票基本信息")
            return 0, 0
        
        success_count = 0
        fail_count = 0
        
        for symbol in stocks:
            count = self.crawl_stock_daily_trade(symbol, start_date=today, end_date=today)
            if count > 0:
                success_count += count
            else:
                fail_count += 1
        
        self.logger.info(f"今日数据爬取完成: 成功 {success_count} 条记录, 失败 {fail_count} 只股票")
        return success_count, fail_count
    
    def crawl_incremental_basic_info(self, update_existing=False, workers=5):
        """
        增量爬取股票基本信息（每日更新）
        
        Args:
            update_existing: 是否更新已存在的股票信息（行业、概念等可能变化）
            workers: 并行worker数量
        
        Returns:
            dict: 包含新增、更新、失败数量的统计信息
        """
        self.logger.info("开始增量爬取股票基本信息...")
        
        existing_symbols = set(StockBasicInfo.get_all_symbols())
        self.logger.info(f"数据库中已有 {len(existing_symbols)} 只股票")
        
        all_stocks = self.fetch_all_stock_list()
        all_symbols = {stock['code'] for stock in all_stocks}
        
        new_symbols = all_symbols - existing_symbols
        
        result = {
            'new_count': 0,
            'updated_count': 0,
            'failed_count': 0,
            'skipped_count': 0
        }
        
        if new_symbols:
            self.logger.info(f"发现 {len(new_symbols)} 只新增股票，开始爬取...")
            
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def crawl_new_stock(symbol):
                try:
                    basic_info = self.fetch_stock_basic_info(symbol)
                    if basic_info:
                        stock = StockBasicInfo(
                            symbol=basic_info['symbol'],
                            name=basic_info['name'],
                            full_name=basic_info.get('full_name', ''),
                            industry=basic_info.get('industry', ''),
                            concept=basic_info.get('concept', ''),
                            region=basic_info.get('region', ''),
                            market=basic_info.get('market', ''),
                            list_date=basic_info.get('list_date')
                        )
                        if stock.save():
                            return {'symbol': symbol, 'success': True, 'type': 'new', 
                                    'name': basic_info['name'], 'industry': basic_info.get('industry', 'N/A')}
                        else:
                            return {'symbol': symbol, 'success': False, 'error': '保存失败'}
                    else:
                        return {'symbol': symbol, 'success': False, 'error': '获取信息失败'}
                except Exception as e:
                    return {'symbol': symbol, 'success': False, 'error': str(e)}
            
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_symbol = {executor.submit(crawl_new_stock, symbol): symbol for symbol in new_symbols}
                
                for future in as_completed(future_to_symbol):
                    result_data = future.result()
                    if result_data['success']:
                        result['new_count'] += 1
                        self.logger.info(f"新增: {result_data['symbol']} - {result_data['name']} (行业: {result_data['industry']})")
                    else:
                        result['failed_count'] += 1
                        self.logger.warning(f"失败: {result_data['symbol']} - {result_data['error']}")
        else:
            self.logger.info("没有发现新增股票")
            result['skipped_count'] = len(existing_symbols)
        
        if update_existing:
            self.logger.info(f"开始更新已有 {len(existing_symbols)} 只股票的基本信息...")
            
            def update_existing_stock(symbol):
                try:
                    basic_info = self.fetch_stock_basic_info(symbol)
                    if basic_info:
                        stock = StockBasicInfo(
                            symbol=basic_info['symbol'],
                            name=basic_info['name'],
                            full_name=basic_info.get('full_name', ''),
                            industry=basic_info.get('industry', ''),
                            concept=basic_info.get('concept', ''),
                            region=basic_info.get('region', ''),
                            market=basic_info.get('market', ''),
                            list_date=basic_info.get('list_date')
                        )
                        if stock.save():
                            return {'symbol': symbol, 'success': True, 'type': 'updated',
                                    'name': basic_info['name'], 'industry': basic_info.get('industry', 'N/A')}
                        else:
                            return {'symbol': symbol, 'success': False, 'error': '保存失败'}
                    else:
                        return {'symbol': symbol, 'success': False, 'error': '获取信息失败'}
                except Exception as e:
                    return {'symbol': symbol, 'success': False, 'error': str(e)}
            
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_symbol = {executor.submit(update_existing_stock, symbol): symbol for symbol in existing_symbols}
                
                for future in as_completed(future_to_symbol):
                    result_data = future.result()
                    if result_data['success']:
                        result['updated_count'] += 1
                        self.logger.info(f"更新: {result_data['symbol']} - {result_data['name']} (行业: {result_data['industry']})")
                    else:
                        result['failed_count'] += 1
                        self.logger.warning(f"失败: {result_data['symbol']} - {result_data['error']}")
        
        self.logger.info(f"增量更新完成: 新增 {result['new_count']} 只, 更新 {result['updated_count']} 只, 失败 {result['failed_count']} 只, 跳过 {result['skipped_count']} 只")
        return result
