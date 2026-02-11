"""
实时数据采集器

通过WebSocket订阅实时K线和价格数据
"""

import asyncio
from typing import List, Dict, Callable, Optional
from loguru import logger

from ..adapters.base import BaseExchangeAdapter, KlineData, TickerData
from ..storage import KlineStorage, TickerStorage


class RealtimeDataCollector:
    """实时数据采集器"""

    def __init__(
        self,
        adapter: BaseExchangeAdapter,
        kline_storage: KlineStorage,
        ticker_storage: TickerStorage
    ):
        self.adapter = adapter
        self.kline_storage = kline_storage
        self.ticker_storage = ticker_storage
        self.running = False
        self.tasks: List[asyncio.Task] = []
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60

    async def start_kline_collection(
        self,
        symbols: List[str],
        intervals: List[str],
        callback: Optional[Callable] = None
    ):
        """启动K线数据采集

        Args:
            symbols: 交易对列表
            intervals: 时间周期列表
            callback: 可选的回调函数
        """
        self.running = True
        exchange = self.adapter.get_exchange_id()

        logger.info(f"Starting kline collection for {len(symbols)} symbols, {len(intervals)} intervals")

        # 为每个交易对和时间周期创建订阅任务
        for symbol in symbols:
            for interval in intervals:
                task = asyncio.create_task(
                    self._subscribe_kline_with_retry(symbol, interval, callback)
                )
                self.tasks.append(task)

        logger.info(f"Started {len(self.tasks)} kline subscription tasks")

    async def start_ticker_collection(
        self,
        symbols: List[str],
        callback: Optional[Callable] = None
    ):
        """启动价格数据采集"""
        self.running = True
        exchange = self.adapter.get_exchange_id()

        logger.info(f"Starting ticker collection for {len(symbols)} symbols")

        for symbol in symbols:
            task = asyncio.create_task(
                self._subscribe_ticker_with_retry(symbol, callback)
            )
            self.tasks.append(task)

        logger.info(f"Started {len(self.tasks)} ticker subscription tasks")

    async def stop(self):
        """停止采集"""
        logger.info("Stopping realtime collector...")
        self.running = False

        # 取消所有任务
        for task in self.tasks:
            task.cancel()

        # 等待任务完成
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

        logger.info("Realtime collector stopped")

    async def _subscribe_kline_with_retry(
        self,
        symbol: str,
        interval: str,
        callback: Optional[Callable]
    ):
        """订阅K线（带重试）"""
        exchange = self.adapter.get_exchange_id()

        while self.running:
            try:
                logger.info(f"Subscribing to kline: {symbol} {interval}")

                async def kline_callback(kline: KlineData):
                    # 保存到存储
                    await self.kline_storage.save_kline(exchange, symbol, interval, kline)

                    # 调用用户回调
                    if callback:
                        try:
                            await callback(symbol, interval, kline)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")

                # 订阅
                await self.adapter.subscribe_klines(symbol, interval, kline_callback)

            except asyncio.CancelledError:
                logger.info(f"Kline subscription cancelled: {symbol} {interval}")
                break
            except Exception as e:
                logger.error(f"Kline subscription error: {e}")

                if self.running:
                    # 指数退避重连
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
                    logger.info(f"Reconnecting kline: {symbol} {interval}")
                else:
                    break

        logger.info(f"Kline subscription stopped: {symbol} {interval}")

    async def _subscribe_ticker_with_retry(
        self,
        symbol: str,
        callback: Optional[Callable]
    ):
        """订阅价格（带重试）"""
        exchange = self.adapter.get_exchange_id()

        while self.running:
            try:
                logger.info(f"Subscribing to ticker: {symbol}")

                async def ticker_callback(ticker: TickerData):
                    # 保存到存储
                    await self.ticker_storage.save_ticker(exchange, ticker)

                    # 调用用户回调
                    if callback:
                        try:
                            await callback(symbol, ticker)
                        except Exception as e:
                            logger.error(f"Ticker callback error: {e}")

                # 订阅
                await self.adapter.subscribe_ticker(symbol, ticker_callback)

            except asyncio.CancelledError:
                logger.info(f"Ticker subscription cancelled: {symbol}")
                break
            except Exception as e:
                logger.error(f"Ticker subscription error: {e}")

                if self.running:
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
                    logger.info(f"Reconnecting ticker: {symbol}")
                else:
                    break

        logger.info(f"Ticker subscription stopped: {symbol}")
