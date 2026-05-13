"""Daemon 调度 — APScheduler BackgroundScheduler 管理"""

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from stockshark.config import Config
from stockshark.pipeline.kline_collector import KLineCollector
from stockshark.pipeline.indicator_calculator import IndicatorCalculator
from stockshark.utils.logger import get_logger

logger = get_logger(__name__)


class PipelineDaemon:
    """Pipeline Daemon — 管理 APScheduler 定时任务"""

    def __init__(self):
        self.scheduler = None
        self.collector = KLineCollector()
        self.calculator = IndicatorCalculator()
        self.last_collect_time = None
        self.last_indicator_time = None

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def start(self):
        """初始化并启动 BackgroundScheduler"""
        if not Config.DAEMON_ENABLED:
            logger.info("DAEMON_ENABLED=False，跳过 daemon 初始化")
            return

        self.scheduler = BackgroundScheduler()

        hour = Config.COLLECT_CRON_HOUR
        minute = Config.COLLECT_CRON_MINUTE
        offset = Config.INDICATOR_CRON_OFFSET_MINUTES

        # 增量 K 线采集：周一至周五 hour:minute
        self.scheduler.add_job(
            self._job_collect,
            "cron",
            day_of_week="mon-fri",
            hour=hour,
            minute=minute,
            id="pipeline_collect",
            name="增量K线采集",
        )

        # 增量指标计算：在采集之后 offset 分钟
        indicator_minute = minute + offset
        indicator_hour = hour + indicator_minute // 60
        indicator_minute = indicator_minute % 60

        self.scheduler.add_job(
            self._job_indicators,
            "cron",
            day_of_week="mon-fri",
            hour=indicator_hour,
            minute=indicator_minute,
            id="pipeline_indicators",
            name="增量指标计算",
        )

        self.scheduler.start()
        logger.info(
            "Pipeline daemon 已启动 — 采集 cron %02d:%02d, 指标 cron %02d:%02d",
            hour, minute, indicator_hour, indicator_minute,
        )

    def stop(self):
        """停止 scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Pipeline daemon 已停止")

    # ------------------------------------------------------------------
    # 手动触发
    # ------------------------------------------------------------------

    def trigger_collect(self):
        """手动触发一次全量增量采集"""
        return self._job_collect()

    def trigger_indicators(self):
        """手动触发一次全量指标计算"""
        return self._job_indicators()

    # ------------------------------------------------------------------
    # 定时任务
    # ------------------------------------------------------------------

    def _job_collect(self):
        logger.info("开始增量 K 线采集...")
        try:
            result = self.collector.collect_all()
            self.last_collect_time = datetime.utcnow().isoformat() + "Z"
            logger.info("K 线采集完成: %s", result)
            return result
        except Exception as e:
            logger.error("K 线采集异常: %s", e)
            return {"error": str(e)}

    def _job_indicators(self):
        logger.info("开始增量指标计算...")
        try:
            result = self.calculator.calculate_all()
            self.last_indicator_time = datetime.utcnow().isoformat() + "Z"
            logger.info("指标计算完成: %s", result)
            return result
        except Exception as e:
            logger.error("指标计算异常: %s", e)
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------

    def status(self):
        from stockshark.pipeline.tables import count_tracked_stocks

        return {
            "daemon_enabled": Config.DAEMON_ENABLED,
            "scheduler_running": (
                self.scheduler.running if self.scheduler else False
            ),
            "last_collect_time": self.last_collect_time,
            "last_indicator_time": self.last_indicator_time,
            "tracked_stock_count": count_tracked_stocks(),
        }


# 全局单例
pipeline_daemon = PipelineDaemon()
