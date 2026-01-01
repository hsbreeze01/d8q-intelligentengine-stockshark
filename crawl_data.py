#!/usr/bin/env python
"""
股票数据爬取命令行工具
用于手动触发数据爬取任务
"""
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from stockshark.data.crawler import StockDataCrawler
from stockshark.utils.logger import get_logger

logger = get_logger(__name__)


def init_database():
    """初始化数据库"""
    from migrations.migrate import init_database
    
    print("正在初始化数据库...")
    if init_database():
        print("数据库初始化成功")
    else:
        print("数据库初始化失败")
        sys.exit(1)


def crawl_single_stock_worker(symbol, crawler):
    """爬取单只股票的基本信息（worker函数）"""
    from stockshark.models.stock_basic_info import StockBasicInfo
    
    try:
        basic_info = crawler.fetch_stock_basic_info(symbol)
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
                return {'symbol': symbol, 'success': True, 'name': basic_info['name'], 
                        'industry': basic_info.get('industry', 'N/A'), 'concept': basic_info.get('concept', 'N/A')}
            else:
                return {'symbol': symbol, 'success': False, 'error': '保存失败'}
        else:
            return {'symbol': symbol, 'success': False, 'error': '获取信息失败'}
    except Exception as e:
        return {'symbol': symbol, 'success': False, 'error': str(e)}


def crawl_basic_info(limit=None, offset=None, batch_size=1000, batch_file=None, workers=5):
    """爬取股票基本信息"""
    from stockshark.models.stock_basic_info import StockBasicInfo
    crawler = StockDataCrawler()
    
    if batch_file:
        print(f"开始从文件 {batch_file} 爬取股票基本信息（{workers}个worker并行）...")
        with open(batch_file, 'r') as f:
            symbols = [line.strip() for line in f if line.strip()]
        
        success = 0
        fail = 0
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_symbol = {executor.submit(crawl_single_stock_worker, symbol, crawler): symbol for symbol in symbols}
            
            for future in as_completed(future_to_symbol):
                result = future.result()
                if result['success']:
                    success += 1
                    print(f"成功: {result['symbol']} - {result['name']} (行业: {result['industry']}, 概念: {result['concept']})")
                else:
                    fail += 1
                    print(f"失败: {result['symbol']} - {result['error']}")
        
        print(f"爬取完成: 成功 {success} 只, 失败 {fail} 只")
    elif offset is not None:
        print(f"开始爬取股票基本信息（从第 {offset} 只开始，批次大小: {batch_size}）...")
        success, fail = crawler.crawl_all_stock_basic_info(limit=batch_size, offset=offset)
    elif limit:
        print(f"开始爬取股票基本信息（限制: {limit} 只）...")
        success, fail = crawler.crawl_all_stock_basic_info(limit=limit)
    else:
        print("开始爬取所有股票基本信息...")
        success, fail = crawler.crawl_all_stock_basic_info(limit=limit)
    
    print(f"爬取完成: 成功 {success} 只, 失败 {fail} 只")


def crawl_daily_trade(start_date=None, end_date=None, limit=None):
    """爬取股票每日交易数据"""
    crawler = StockDataCrawler()
    
    print(f"开始爬取股票交易数据...")
    if start_date:
        print(f"起始日期: {start_date}")
    if end_date:
        print(f"结束日期: {end_date}")
    if limit:
        print(f"限制股票数量: {limit}")
    
    success, fail = crawler.crawl_all_stock_daily_trade(
        start_date=start_date, 
        end_date=end_date, 
        limit=limit
    )
    
    print(f"爬取完成: 成功 {success} 条记录, 失败 {fail} 只股票")


def crawl_today():
    """爬取今日交易数据"""
    crawler = StockDataCrawler()
    
    print("开始爬取今日交易数据...")
    
    success, fail = crawler.crawl_today_trade_data()
    
    print(f"今日数据爬取完成: 成功 {success} 条记录, 失败 {fail} 只股票")


def crawl_single_stock(symbol):
    """爬取单只股票的数据"""
    crawler = StockDataCrawler()
    
    print(f"开始爬取股票 {symbol} 的数据...")
    
    basic_info = crawler.fetch_stock_basic_info(symbol)
    if basic_info:
        print(f"股票基本信息: {basic_info['name']} - {basic_info['industry']}")
    else:
        print(f"获取股票 {symbol} 基本信息失败")
        return
    
    trades = crawler.fetch_stock_daily_trade(symbol)
    print(f"获取到 {len(trades)} 条交易记录")


def main():
    parser = argparse.ArgumentParser(description='股票数据爬取工具')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    init_parser = subparsers.add_parser('init', help='初始化数据库')
    
    basic_parser = subparsers.add_parser('basic', help='爬取股票基本信息')
    basic_parser.add_argument('--limit', type=int, help='限制爬取的股票数量')
    basic_parser.add_argument('--offset', type=int, help='从第几只股票开始爬取（0-based）')
    basic_parser.add_argument('--batch-size', type=int, default=1000, help='每批爬取的股票数量（默认1000）')
    basic_parser.add_argument('--batch-file', type=str, help='从文件读取股票代码列表进行爬取')
    basic_parser.add_argument('--workers', type=int, default=5, help='并行worker数量（默认5）')
    
    trade_parser = subparsers.add_parser('trade', help='爬取股票交易数据')
    trade_parser.add_argument('--start', type=str, help='开始日期 (YYYY-MM-DD)')
    trade_parser.add_argument('--end', type=str, help='结束日期 (YYYY-MM-DD)')
    trade_parser.add_argument('--limit', type=int, help='限制爬取的股票数量')
    
    today_parser = subparsers.add_parser('today', help='爬取今日交易数据')
    
    single_parser = subparsers.add_parser('single', help='爬取单只股票数据')
    single_parser.add_argument('symbol', type=str, help='股票代码')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'init':
        init_database()
    elif args.command == 'basic':
        crawl_basic_info(limit=args.limit, offset=args.offset, batch_size=args.batch_size, batch_file=args.batch_file, workers=args.workers)
    elif args.command == 'trade':
        crawl_daily_trade(start_date=args.start, end_date=args.end, limit=args.limit)
    elif args.command == 'today':
        crawl_today()
    elif args.command == 'single':
        crawl_single_stock(args.symbol)


if __name__ == '__main__':
    main()
