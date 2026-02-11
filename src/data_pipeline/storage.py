"""
数据存储服务模块

提供K线、Ticker、订单簿数据的存储功能
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict
from loguru import logger
import asyncpg
import redis.asyncio as aioredis
import json

from .adapters.base import KlineData, TickerData, OrderbookData


class KlineStorage:
    """K线数据存储服务"""

    def __init__(self, db_pool: asyncpg.Pool, redis_client: aioredis.Redis):
        self.db_pool = db_pool
        self.redis = redis_client
        self.batch_size = 1000

    async def save_kline(
        self,
        exchange: str,
        symbol: str,
        interval: str,
        kline: KlineData
    ) -> bool:
        """保存单条K线数据"""
        return await self.save_klines(exchange, symbol, interval, [kline])

    async def save_klines(
        self,
        exchange: str,
        symbol: str,
        interval: str,
        klines: List[KlineData]
    ) -> bool:
        """批量保存K线数据"""
        if not klines:
            return True

        try:
            # 1. 保存到TimescaleDB
            await self._save_to_db(exchange, symbol, interval, klines)

            # 2. 更新Redis缓存（只缓存最新的数据）
            await self._update_cache(exchange, symbol, interval, klines[-1])

            logger.debug(f"Saved {len(klines)} klines for {exchange}/{symbol}/{interval}")
            return True

        except Exception as e:
            logger.error(f"Failed to save klines: {e}")
            return False

    async def _save_to_db(
        self,
        exchange: str,
        symbol: str,
        interval: str,
        klines: List[KlineData]
    ):
        """保存到数据库"""
        async with self.db_pool.acquire() as conn:
            # 使用COPY命令批量插入（高性能）
            await conn.copy_records_to_table(
                'klines',
                records=[
                    (
                        kline.timestamp,
                        exchange,
                        symbol,
                        interval,
                        float(kline.open),
                        float(kline.high),
                        float(kline.low),
                        float(kline.close),
                        float(kline.volume),
                        float(kline.quote_volume) if kline.quote_volume else None,
                        kline.trades_count
                    )
                    for kline in klines
                ],
                columns=['time', 'exchange', 'symbol', 'interval', 'open', 'high',
                        'low', 'close', 'volume', 'quote_volume', 'trades_count']
            )

    async def _update_cache(
        self,
        exchange: str,
        symbol: str,
        interval: str,
        kline: KlineData
    ):
        """更新Redis缓存"""
        key = f"kline:latest:{exchange}:{symbol}:{interval}"
        value = json.dumps({
            'timestamp': kline.timestamp.isoformat(),
            'open': str(kline.open),
            'high': str(kline.high),
            'low': str(kline.low),
            'close': str(kline.close),
            'volume': str(kline.volume)
        })
        await self.redis.setex(key, 300, value)  # 5分钟过期

    async def get_klines(
        self,
        exchange: str,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[KlineData]:
        """查询K线数据"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT time, open, high, low, close, volume, quote_volume, trades_count
                FROM klines
                WHERE exchange = $1 AND symbol = $2 AND interval = $3
                  AND time >= $4 AND time <= $5
                ORDER BY time DESC
                LIMIT $6
                """,
                exchange, symbol, interval, start_time, end_time, limit
            )

            return [
                KlineData(
                    timestamp=row['time'],
                    open=Decimal(str(row['open'])),
                    high=Decimal(str(row['high'])),
                    low=Decimal(str(row['low'])),
                    close=Decimal(str(row['close'])),
                    volume=Decimal(str(row['volume'])),
                    quote_volume=Decimal(str(row['quote_volume'])) if row['quote_volume'] else None,
                    trades_count=row['trades_count']
                )
                for row in rows
            ]

    async def get_last_timestamp(
        self,
        exchange: str,
        symbol: str,
        interval: str
    ) -> Optional[datetime]:
        """获取最后一条数据的时间戳"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT MAX(time) as last_time
                FROM klines
                WHERE exchange = $1 AND symbol = $2 AND interval = $3
                """,
                exchange, symbol, interval
            )
            return row['last_time'] if row else None


class TickerStorage:
    """价格数据存储服务"""

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def save_ticker(
        self,
        exchange: str,
        ticker: TickerData
    ) -> bool:
        """保存价格数据到Redis"""
        try:
            key = f"ticker:latest:{exchange}:{ticker.symbol}"
            value = json.dumps({
                'timestamp': ticker.timestamp.isoformat(),
                'last_price': str(ticker.last_price),
                'bid_price': str(ticker.bid_price) if ticker.bid_price else None,
                'ask_price': str(ticker.ask_price) if ticker.ask_price else None,
                'volume_24h': str(ticker.volume_24h) if ticker.volume_24h else None,
                'price_change_24h': str(ticker.price_change_24h) if ticker.price_change_24h else None
            })
            await self.redis.setex(key, 60, value)  # 1分钟过期
            return True
        except Exception as e:
            logger.error(f"Failed to save ticker: {e}")
            return False

    async def get_ticker(
        self,
        exchange: str,
        symbol: str
    ) -> Optional[TickerData]:
        """获取最新价格"""
        try:
            key = f"ticker:latest:{exchange}:{symbol}"
            value = await self.redis.get(key)
            if not value:
                return None

            data = json.loads(value)
            return TickerData(
                timestamp=datetime.fromisoformat(data['timestamp']),
                symbol=symbol,
                last_price=Decimal(data['last_price']),
                bid_price=Decimal(data['bid_price']) if data.get('bid_price') else None,
                ask_price=Decimal(data['ask_price']) if data.get('ask_price') else None,
                volume_24h=Decimal(data['volume_24h']) if data.get('volume_24h') else None,
                price_change_24h=Decimal(data['price_change_24h']) if data.get('price_change_24h') else None
            )
        except Exception as e:
            logger.error(f"Failed to get ticker: {e}")
            return None


class OrderbookStorage:
    """订单簿存储服务"""

    def __init__(self, db_pool: asyncpg.Pool, redis_client: aioredis.Redis):
        self.db_pool = db_pool
        self.redis = redis_client

    async def save_orderbook(
        self,
        exchange: str,
        orderbook: OrderbookData
    ) -> bool:
        """保存订单簿快照"""
        try:
            # 1. 保存到TimescaleDB
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO orderbook_snapshots
                    (time, exchange, symbol, bids, asks, checksum)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (time, exchange, symbol) DO NOTHING
                    """,
                    orderbook.timestamp,
                    exchange,
                    orderbook.symbol,
                    json.dumps([[str(p), str(q)] for p, q in orderbook.bids]),
                    json.dumps([[str(p), str(q)] for p, q in orderbook.asks]),
                    orderbook.checksum
                )

            # 2. 更新Redis缓存
            await self._update_cache(exchange, orderbook)

            return True
        except Exception as e:
            logger.error(f"Failed to save orderbook: {e}")
            return False

    async def _update_cache(
        self,
        exchange: str,
        orderbook: OrderbookData
    ):
        """更新Redis缓存"""
        key = f"orderbook:latest:{exchange}:{orderbook.symbol}"
        value = json.dumps({
            'timestamp': orderbook.timestamp.isoformat(),
            'bids': [[str(p), str(q)] for p, q in orderbook.bids[:20]],  # 只缓存前20档
            'asks': [[str(p), str(q)] for p, q in orderbook.asks[:20]]
        })
        await self.redis.setex(key, 10, value)  # 10秒过期
