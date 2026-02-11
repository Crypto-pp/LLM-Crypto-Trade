#!/usr/bin/env python3
"""
历史数据采集脚本

用法:
    python scripts/collect_historical.py --exchange binance --symbol BTC/USDT --interval 1h --start 2024-01-01 --end 2024-12-31
"""

import asyncio
import argparse
from datetime import datetime
from loguru import logger
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_pipeline.adapters.binance import BinanceAdapter
from src.data_pipeline.storage import KlineStorage
from src.data_pipeline.collectors.historical_collector import HistoricalDataCollector
from src.utils.database import get_db_pool
from src.utils.redis_client import get_redis_client


async def main():
    parser = argparse.ArgumentParser(description='采集历史K线数据')
    parser.add_argument('--exchange', required=True, help='交易所ID (binance)')
    parser.add_argument('--symbol', required=True, help='交易对 (BTC/USDT)')
    parser.add_argument('--interval', required=True, help='时间周期 (1m, 5m, 1h, 1d)')
    parser.add_argument('--start', required=True, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--resume', action='store_true', help='断点续传')

    args = parser.parse_args()

    # 解析日期
    start_date = datetime.strptime(args.start, '%Y-%m-%d')
    end_date = datetime.strptime(args.end, '%Y-%m-%d')

    logger.info(f"Starting historical data collection")
    logger.info(f"Exchange: {args.exchange}")
    logger.info(f"Symbol: {args.symbol}")
    logger.info(f"Interval: {args.interval}")
    logger.info(f"Date range: {start_date} to {end_date}")

    # 初始化数据库连接
    db_pool = await get_db_pool()
    redis_client = await get_redis_client()

    try:
        # 创建适配器
        if args.exchange == 'binance':
            adapter = BinanceAdapter()
        else:
            logger.error(f"Unsupported exchange: {args.exchange}")
            return

        # 创建存储服务
        storage = KlineStorage(db_pool, redis_client)

        # 创建采集器
        collector = HistoricalDataCollector(adapter, storage)

        # 开始采集
        count = await collector.collect_range(
            symbol=args.symbol,
            interval=args.interval,
            start_date=start_date,
            end_date=end_date,
            resume=args.resume
        )

        logger.info(f"Collection completed: {count} klines collected")

    except Exception as e:
        logger.error(f"Collection failed: {e}")
        raise
    finally:
        # 清理资源
        await db_pool.close()
        await redis_client.close()


if __name__ == '__main__':
    asyncio.run(main())
