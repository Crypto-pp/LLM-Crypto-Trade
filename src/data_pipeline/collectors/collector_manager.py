"""
采集器管理器

管理多个采集器，提供统一的启动、停止和监控接口
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from ..adapters.base import BaseExchangeAdapter
from ..storage import KlineStorage, TickerStorage
from .historical_collector import HistoricalDataCollector
from .realtime_collector import RealtimeDataCollector


class CollectorManager:
    """采集器管理器"""

    def __init__(
        self,
        adapters: Dict[str, BaseExchangeAdapter],
        kline_storage: KlineStorage,
        ticker_storage: TickerStorage
    ):
        self.adapters = adapters
        self.kline_storage = kline_storage
        self.ticker_storage = ticker_storage

        self.historical_collectors: Dict[str, HistoricalDataCollector] = {}
        self.realtime_collectors: Dict[str, RealtimeDataCollector] = {}

        self.running = False
        self.stats = {
            'start_time': None,
            'klines_collected': 0,
            'tickers_collected': 0,
            'errors': 0
        }

    async def start_historical_collection(
        self,
        exchange: str,
        symbols: List[str],
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """启动历史数据采集"""

        if exchange not in self.adapters:
            raise ValueError(f"Unknown exchange: {exchange}")

        adapter = self.adapters[exchange]

        # 创建历史采集器
        if exchange not in self.historical_collectors:
            self.historical_collectors[exchange] = HistoricalDataCollector(
                adapter=adapter,
                storage=self.kline_storage
            )

        collector = self.historical_collectors[exchange]

        logger.info(f"Starting historical collection: {exchange}, {len(symbols)} symbols")

        # 并发采集多个交易对
        results = await collector.collect_multiple_symbols(
            symbols=symbols,
            interval=interval,
            start_date=start_date,
            end_date=end_date
        )

        # 统计结果
        total_count = sum(r['count'] for r in results.values())
        success_count = sum(1 for r in results.values() if r['success'])

        logger.info(
            f"Historical collection completed: "
            f"{success_count}/{len(symbols)} symbols, "
            f"{total_count} klines"
        )

        return {
            'exchange': exchange,
            'total_klines': total_count,
            'success_symbols': success_count,
            'total_symbols': len(symbols),
            'results': results
        }

    async def start_realtime_collection(
        self,
        exchange: str,
        symbols: List[str],
        intervals: List[str]
    ):
        """启动实时数据采集"""

        if exchange not in self.adapters:
            raise ValueError(f"Unknown exchange: {exchange}")

        adapter = self.adapters[exchange]

        # 创建实时采集器
        if exchange not in self.realtime_collectors:
            self.realtime_collectors[exchange] = RealtimeDataCollector(
                adapter=adapter,
                kline_storage=self.kline_storage,
                ticker_storage=self.ticker_storage
            )

        collector = self.realtime_collectors[exchange]

        logger.info(
            f"Starting realtime collection: {exchange}, "
            f"{len(symbols)} symbols, {len(intervals)} intervals"
        )

        # 启动K线采集
        await collector.start_kline_collection(symbols, intervals)

        # 启动价格采集
        await collector.start_ticker_collection(symbols)

        self.running = True
        self.stats['start_time'] = datetime.now()

        logger.info("Realtime collection started")

    async def stop_all(self):
        """停止所有采集器"""
        logger.info("Stopping all collectors...")

        self.running = False

        # 停止所有实时采集器
        for exchange, collector in self.realtime_collectors.items():
            try:
                await collector.stop()
                logger.info(f"Stopped realtime collector: {exchange}")
            except Exception as e:
                logger.error(f"Error stopping collector {exchange}: {e}")

        logger.info("All collectors stopped")

    def get_status(self) -> Dict:
        """获取采集器状态"""
        return {
            'running': self.running,
            'stats': self.stats,
            'exchanges': list(self.adapters.keys()),
            'historical_collectors': len(self.historical_collectors),
            'realtime_collectors': len(self.realtime_collectors)
        }
