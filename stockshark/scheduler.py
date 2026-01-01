"""定时任务调度器"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from stockshark.data.crawler import StockDataCrawler
from stockshark.utils.logger import get_logger

logger = get_logger(__name__)

scheduler = None


def init_scheduler():
    """
    初始化定时任务调度器
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("调度器已经初始化")
        return scheduler
    
    logger.info("初始化定时任务调度器...")
    scheduler = BackgroundScheduler()
    
    add_scheduled_jobs()
    
    return scheduler


def add_scheduled_jobs():
    """
    添加定时任务
    """
    if not scheduler:
        logger.error("调度器未初始化")
        return
    
    crawler = StockDataCrawler()
    
    scheduler.add_job(
        func=crawl_daily_trade_job,
        trigger=CronTrigger(hour=16, minute=0),
        id='daily_trade_crawl',
        name='每日交易数据爬取',
        replace_existing=True
    )
    logger.info("已添加定时任务: 每日16:00爬取交易数据")
    
    scheduler.add_job(
        func=crawl_basic_info_job,
        trigger=CronTrigger(day_of_week='mon', hour=2, minute=0),
        id='weekly_basic_info_crawl',
        name='每周更新股票基本信息',
        replace_existing=True
    )
    logger.info("已添加定时任务: 每周一凌晨2点更新股票基本信息")


def crawl_daily_trade_job():
    """
    每日交易数据爬取任务
    """
    logger.info("开始执行每日交易数据爬取任务...")
    
    try:
        crawler = StockDataCrawler()
        success, fail = crawler.crawl_today_trade_data()
        
        logger.info(f"每日交易数据爬取任务完成: 成功 {success} 条记录, 失败 {fail} 只股票")
    except Exception as e:
        logger.error(f"每日交易数据爬取任务失败: {e}")


def crawl_basic_info_job():
    """
    股票基本信息更新任务
    """
    logger.info("开始执行股票基本信息更新任务...")
    
    try:
        crawler = StockDataCrawler()
        success, fail = crawler.crawl_all_stock_basic_info()
        
        logger.info(f"股票基本信息更新任务完成: 成功 {success} 只, 失败 {fail} 只")
    except Exception as e:
        logger.error(f"股票基本信息更新任务失败: {e}")


def start_scheduler():
    """
    启动调度器
    """
    global scheduler
    
    if not scheduler:
        init_scheduler()
    
    if not scheduler.running:
        logger.info("启动定时任务调度器...")
        scheduler.start()
        logger.info("定时任务调度器已启动")
    else:
        logger.warning("调度器已经在运行")


def stop_scheduler():
    """
    停止调度器
    """
    global scheduler
    
    if scheduler and scheduler.running:
        logger.info("停止定时任务调度器...")
        scheduler.shutdown()
        logger.info("定时任务调度器已停止")
        scheduler = None


def get_scheduler_status():
    """
    获取调度器状态
    
    Returns:
        dict: 调度器状态信息
    """
    if not scheduler:
        return {
            'running': False,
            'jobs': []
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run_time': str(job.next_run_time) if job.next_run_time else None
        })
    
    return {
        'running': scheduler.running,
        'jobs': jobs
    }
