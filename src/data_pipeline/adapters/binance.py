"""
Binance交易所适配器

实现Binance API的数据采集功能
"""

import json
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Callable
import aiohttp
import websockets
from loguru import logger

from .base import (
    BaseExchangeAdapter,
    KlineData,
    TickerData,
    OrderbookData
)


class BinanceAdapter(BaseExchangeAdapter):
    """Binance交易所适配器"""

    BASE_URL = "https://api.binance.com"
    WS_URL = "wss://stream.binance.com:9443/ws"

    def get_exchange_id(self) -> str:
        return "binance"

    def get_rate_limits(self) -> Dict[str, int]:
        return {
            'requests_per_minute': 1200,
            'orders_per_10_seconds': 100,
            'weight_per_minute': 6000
        }

    def normalize_symbol(self, symbol: str) -> str:
        """BTC/USDT -> BTCUSDT"""
        return symbol.replace('/', '').upper()

    def denormalize_symbol(self, symbol: str) -> str:
        """BTCUSDT -> BTC/USDT"""
        # 常见的quote货币
        quote_currencies = ['USDT', 'USDC', 'BUSD', 'BTC', 'ETH', 'BNB']
        for quote in quote_currencies:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                return f"{base}/{quote}"
        return symbol

    def parse_kline(self, raw_data: List) -> KlineData:
        """解析Binance K线数据

        Binance格式:
        [
            1499040000000,      // 开盘时间
            "0.01634000",       // 开盘价
            "0.80000000",       // 最高价
            "0.01575800",       // 最低价
            "0.01577100",       // 收盘价
            "148976.11427815",  // 成交量
            1499644799999,      // 收盘时间
            "2434.19055334",    // 成交额
            308,                // 成交笔数
            ...
        ]
        """
        return KlineData(
            timestamp=datetime.fromtimestamp(raw_data[0] / 1000, tz=timezone.utc),
            open=Decimal(str(raw_data[1])),
            high=Decimal(str(raw_data[2])),
            low=Decimal(str(raw_data[3])),
            close=Decimal(str(raw_data[4])),
            volume=Decimal(str(raw_data[5])),
            quote_volume=Decimal(str(raw_data[7])) if len(raw_data) > 7 else None,
            trades_count=int(raw_data[8]) if len(raw_data) > 8 else None
        )

    def _convert_interval(self, interval: str) -> str:
        """转换时间周期格式"""
        # Binance格式: 1m, 5m, 1h, 1d 等，已经兼容
        return interval

    async def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 500
    ) -> List[KlineData]:
        """获取历史K线数据"""

        # 等待限流
        await self.rate_limiter.acquire('requests_per_minute')

        # 构建请求参数
        params = {
            'symbol': self.normalize_symbol(symbol),
            'interval': self._convert_interval(interval),
            'limit': min(limit, 1000)  # Binance最大1000
        }

        if start_time:
            params['startTime'] = int(start_time.timestamp() * 1000)
        if end_time:
            params['endTime'] = int(end_time.timestamp() * 1000)

        # 发送请求
        url = f"{self.BASE_URL}/api/v3/klines"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        klines = [self.parse_kline(k) for k in data]
                        logger.debug(f"Fetched {len(klines)} klines for {symbol}")
                        return klines
                    else:
                        error_text = await response.text()
                        logger.error(f"Binance API error: {response.status} - {error_text}")
                        raise Exception(f"API error: {response.status} - {error_text}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching klines for {symbol}")
            raise
        except Exception as e:
            logger.error(f"Error fetching klines: {e}")
            raise

    async def fetch_ticker(self, symbol: str) -> TickerData:
        """获取最新价格"""
        await self.rate_limiter.acquire('requests_per_minute')

        params = {'symbol': self.normalize_symbol(symbol)}
        url = f"{self.BASE_URL}/api/v3/ticker/24hr"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return TickerData(
                            timestamp=datetime.fromtimestamp(data['closeTime'] / 1000, tz=timezone.utc),
                            symbol=symbol,
                            last_price=Decimal(str(data['lastPrice'])),
                            bid_price=Decimal(str(data['bidPrice'])) if 'bidPrice' in data else None,
                            ask_price=Decimal(str(data['askPrice'])) if 'askPrice' in data else None,
                            volume_24h=Decimal(str(data['volume'])) if 'volume' in data else None,
                            price_change_24h=Decimal(str(data['priceChangePercent'])) if 'priceChangePercent' in data else None
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(f"API error: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Error fetching ticker: {e}")
            raise

    async def fetch_orderbook(self, symbol: str, depth: int = 20) -> OrderbookData:
        """获取订单簿"""
        await self.rate_limiter.acquire('requests_per_minute')

        params = {
            'symbol': self.normalize_symbol(symbol),
            'limit': min(depth, 5000)
        }
        url = f"{self.BASE_URL}/api/v3/depth"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return OrderbookData(
                            timestamp=datetime.now(timezone.utc),
                            symbol=symbol,
                            bids=[(Decimal(str(p)), Decimal(str(q))) for p, q in data['bids']],
                            asks=[(Decimal(str(p)), Decimal(str(q))) for p, q in data['asks']]
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(f"API error: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Error fetching orderbook: {e}")
            raise

    async def subscribe_klines(
        self,
        symbol: str,
        interval: str,
        callback: Callable
    ):
        """订阅实时K线"""
        stream_name = f"{self.normalize_symbol(symbol).lower()}@kline_{interval}"
        ws_url = f"{self.WS_URL}/{stream_name}"

        logger.info(f"Subscribing to klines: {symbol} {interval}")

        try:
            async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as websocket:
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if 'k' in data:
                            kline = self._parse_ws_kline(data['k'])
                            await callback(kline)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON message: {e}")
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"WebSocket connection closed for {symbol}")
            raise
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            raise

    async def subscribe_ticker(
        self,
        symbol: str,
        callback: Callable
    ):
        """订阅实时价格"""
        stream_name = f"{self.normalize_symbol(symbol).lower()}@ticker"
        ws_url = f"{self.WS_URL}/{stream_name}"

        logger.info(f"Subscribing to ticker: {symbol}")

        try:
            async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as websocket:
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        ticker = TickerData(
                            timestamp=datetime.fromtimestamp(data['E'] / 1000, tz=timezone.utc),
                            symbol=symbol,
                            last_price=Decimal(str(data['c'])),
                            bid_price=Decimal(str(data['b'])) if 'b' in data else None,
                            ask_price=Decimal(str(data['a'])) if 'a' in data else None,
                            volume_24h=Decimal(str(data['v'])) if 'v' in data else None,
                            price_change_24h=Decimal(str(data['P'])) if 'P' in data else None
                        )
                        await callback(ticker)
                    except Exception as e:
                        logger.error(f"Ticker callback error: {e}")
        except Exception as e:
            logger.error(f"WebSocket ticker error: {e}")
            raise

    def _parse_ws_kline(self, data: Dict) -> KlineData:
        """解析WebSocket K线数据"""
        return KlineData(
            timestamp=datetime.fromtimestamp(data['t'] / 1000, tz=timezone.utc),
            open=Decimal(str(data['o'])),
            high=Decimal(str(data['h'])),
            low=Decimal(str(data['l'])),
            close=Decimal(str(data['c'])),
            volume=Decimal(str(data['v'])),
            quote_volume=Decimal(str(data['q'])) if 'q' in data else None,
            trades_count=int(data['n']) if 'n' in data else None
        )

