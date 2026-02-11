#!/usr/bin/env python3
"""
实时数据采集脚本

用法:
    python scripts/start_realtime_collector.py --exchange binance --symbols BTC/USDT,ETH/USDT --intervals 1m,5m,1h
"""

import asyncio
import argparse
import signal
from loguru import logger
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_pipeline.adapters.binance import BinanceAdapter
from src.data_pipeline.storage import KlineStorage, TickerStorage
from src.data_pipeline.collectors.realtime_collector import RealtimeDataCollector
from src.utils.database import get_db_pool
from src.utils.redis_client import get_redis_client


class RealtimeCollectorService:
    """实时采集服务"""

    def __init__(self):
        self.collector = None
        self.running = False

    async def start(self, exchange: str, symbols: list, intervals: list):
        """启动服务"""
        logger.info("Starting realtime collector service")
        logger.info(f"Exchange: {exchange}")
        logger.info(f"Symbols: {', '.join(symbols)}")
        logger.info(f"Intervals: {', '.join(intervals)}")

        # 初始化数据库连接
        db_pool = await get_db_pool()
        redis_client = await get_redis_client()

        try:
            # 创建适配器
            if exchange == 'binance':
                adapter = BinanceAdapter()
            else:
                logger.error(f"Unsupported exchange: {exchange}")
                return

            # 创建存储服务
            kline_storage = KlineStorage(db_pool, redis_client)
            ticker_storage = TickerStorage(redis_client)

            # 创建采集器
            self.collector = RealtimeDataCollector(
                adapter=adapter,
                kline_storage=kline_storage,
                ticker_storage=ticker_storage
            )

            # 启动采集
            await self.collector.start_kline_collection(symbols, intervals)
            await self.collector.start_ticker_collection(symbols)

            self.running = True
            logger.info("Realtime collector service started")

            # 保持运行
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Service error: {e}")
            raise
        finally:
            # 清理资源
            if self.collector:
                await self.collector.stop()
            await db_pool.close()
            await redis_client.close()
            logger.info("Service stopped")

    async def stop(self):
        """停止服务"""
        logger.info("Stopping service...")
        self.running = False


async def main():
    parser = argparse.ArgumentParser(description='启动实时数据采集')
    parser.add_argument('--exchange', required=True, help='交易所ID (binance)')
    parser.add_argument('--symbols', required=True, help='交易对列表，逗号分隔 (BTC/USDT,ETH/USDT)')
    parser.add_argument('--intervals', required=True, help='时间周期列表，逗号分隔 (1m,5m,1h)')

    args = parser.parse_args()

    # 解析参数
    symbols = [s.strip() for s in args.symbols.split(',')]
    intervals = [i.strip() for i in args.intervals.split(',')]

    # 创建服务
    service = RealtimeCollectorService()

    # 设置信号处理
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(service.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动服务
    await service.start(args.exchange, symbols, intervals)


if __name__ == '__main__':
    asyncio.run(main())
