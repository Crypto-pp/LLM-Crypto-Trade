"""
任务调度器
使用APScheduler管理定时任务
"""

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.running = False

    def add_job(self, func, trigger, **kwargs):
        """添加任务"""
        self.scheduler.add_job(func, trigger, **kwargs)
        logger.info(f"Added job: {func.__name__}")

    def add_interval_job(self, func, seconds: int, **kwargs):
        """添加间隔任务"""
        trigger = IntervalTrigger(seconds=seconds)
        self.add_job(func, trigger, **kwargs)

    def add_cron_job(self, func, **cron_kwargs):
        """添加Cron任务"""
        trigger = CronTrigger(**cron_kwargs)
        self.add_job(func, trigger)

    def start(self):
        """启动调度器"""
        if not self.running:
            self.scheduler.start()
            self.running = True
            logger.info("Task scheduler started")

    def shutdown(self):
        """关闭调度器"""
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            logger.info("Task scheduler stopped")

    def get_jobs(self):
        """获取所有任务"""
        return self.scheduler.get_jobs()


# 全局调度器实例
task_scheduler = TaskScheduler()
