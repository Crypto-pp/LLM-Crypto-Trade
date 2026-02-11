"""
历史数据采集器

批量下载历史K线数据，支持断点续传和进度显示
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger

from ..adapters.base import BaseExchangeAdapter, KlineData
from ..storage import KlineStorage
from ..quality_checker import DataQualityChecker


class HistoricalDataCollector:
    """历史数据采集器"""

    def __init__(
        self,
        adapter: BaseExchangeAdapter,
        storage: KlineStorage,
        quality_checker: Optional[DataQualityChecker] = None
    ):
        self.adapter = adapter
        self.storage = storage
        self.quality_checker = quality_checker or DataQualityChecker()
        self.batch_size = 1000
        self.concurrent_limit = 5

    async def collect_range(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime,
        resume: bool = True
    ) -> int:
        """采集指定时间范围的数据

        Args:
            symbol: 交易对
            interval: 时间周期
            start_date: 开始日期
            end_date: 结束日期
            resume: 是否断点续传

        Returns:
            采集的数据条数
        """
        exchange = self.adapter.get_exchange_id()

        # 检查是否需要断点续传
        if resume:
            last_timestamp = await self.storage.get_last_timestamp(exchange, symbol, interval)
            if last_timestamp and last_timestamp > start_date:
                start_date = last_timestamp + timedelta(seconds=self._parse_interval_seconds(interval))
                logger.info(f"Resuming from {start_date}")

        all_klines = []
        current_start = start_date
        interval_seconds = self._parse_interval_seconds(interval)
        batch_duration = timedelta(seconds=interval_seconds * self.batch_size)

        logger.info(f"Collecting {symbol} {interval} from {start_date} to {end_date}")

        while current_start < end_date:
            current_end = min(current_start + batch_duration, end_date)

            try:
                klines = await self.adapter.fetch_klines(
                    symbol=symbol,
                    interval=interval,
                    start_time=current_start,
                    end_time=current_end,
                    limit=self.batch_size
                )

                if klines:
                    # 数据质量检查
                    valid_klines = self._validate_klines(klines)

                    # 保存到数据库
                    await self.storage.save_klines(exchange, symbol, interval, valid_klines)

                    all_klines.extend(valid_klines)
                    logger.info(f"Collected {len(valid_klines)} klines, total: {len(all_klines)}")

                    # 更新起始时间
                    current_start = klines[-1].timestamp + timedelta(seconds=interval_seconds)
                else:
                    current_start = current_end

            except Exception as e:
                logger.error(f"Collection failed: {e}")
                # 继续下一批次
                current_start = current_end
                await asyncio.sleep(5)

        logger.info(f"Collection completed: {len(all_klines)} klines")
        return len(all_klines)

    async def collect_multiple_symbols(
        self,
        symbols: List[str],
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """并发采集多个交易对"""

        semaphore = asyncio.Semaphore(self.concurrent_limit)

        async def collect_with_limit(symbol):
            async with semaphore:
                try:
                    count = await self.collect_range(symbol, interval, start_date, end_date)
                    return symbol, count, None
                except Exception as e:
                    logger.error(f"Failed to collect {symbol}: {e}")
                    return symbol, 0, str(e)

        tasks = [collect_with_limit(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)

        # 整理结果
        result_dict = {}
        for symbol, count, error in results:
            result_dict[symbol] = {
                'count': count,
                'error': error,
                'success': error is None
            }

        return result_dict

    def _validate_klines(self, klines: List[KlineData]) -> List[KlineData]:
        """验证K线数据"""
        valid_klines = []

        for i, kline in enumerate(klines):
            prev_kline = klines[i-1] if i > 0 else None
            is_valid, error_msg = self.quality_checker.check_validity(kline, prev_kline)

            if is_valid:
                valid_klines.append(kline)
            else:
                logger.warning(f"Invalid kline at {kline.timestamp}: {error_msg}")

        return valid_klines

    def _parse_interval_seconds(self, interval: str) -> int:
        """解析时间间隔为秒数"""
        unit = interval[-1]
        value = int(interval[:-1])

        multipliers = {
            'm': 60,
            'h': 3600,
            'd': 86400,
            'w': 604800
        }

        return value * multipliers.get(unit, 60)
