"""
交易所适配器抽象基类

定义统一的接口规范，所有交易所适配器必须实现这些接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Callable
from decimal import Decimal


@dataclass
class KlineData:
    """K线数据标准格式"""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_volume: Optional[Decimal] = None
    trades_count: Optional[int] = None


@dataclass
class TickerData:
    """价格数据标准格式"""
    timestamp: datetime
    symbol: str
    last_price: Decimal
    bid_price: Optional[Decimal] = None
    ask_price: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    price_change_24h: Optional[Decimal] = None


@dataclass
class OrderbookData:
    """订单簿数据标准格式"""
    timestamp: datetime
    symbol: str
    bids: List[tuple[Decimal, Decimal]]  # [(price, quantity), ...]
    asks: List[tuple[Decimal, Decimal]]
    checksum: Optional[int] = None


@dataclass
class MarketData:
    """通用市场数据容器"""
    exchange: str
    symbol: str
    timestamp: datetime
    data_type: str  # 'kline', 'ticker', 'trade', 'orderbook'
    data: Dict
    raw_data: Optional[Dict] = None


class RateLimiter:
    """限流器 - Token Bucket算法"""

    def __init__(self, rate_limits: Dict[str, int]):
        self.rate_limits = rate_limits
        self.tokens: Dict[str, float] = {}
        self.last_update: Dict[str, datetime] = {}

        # 初始化令牌桶
        for key, limit in rate_limits.items():
            self.tokens[key] = float(limit)
            self.last_update[key] = datetime.now()

    async def acquire(self, key: str = 'requests_per_minute'):
        """获取令牌"""
        import asyncio

        while True:
            self._refill_tokens(key)

            if self.tokens.get(key, 0) >= 1:
                self.tokens[key] -= 1
                return

            await asyncio.sleep(0.1)

    def _refill_tokens(self, key: str):
        """补充令牌"""
        if key not in self.rate_limits:
            return

        now = datetime.now()
        time_passed = (now - self.last_update[key]).total_seconds()

        # 根据时间补充令牌
        if 'per_minute' in key:
            tokens_to_add = time_passed * (self.rate_limits[key] / 60)
        elif 'per_second' in key:
            tokens_to_add = time_passed * self.rate_limits[key]
        else:
            tokens_to_add = 0

        self.tokens[key] = min(
            self.tokens[key] + tokens_to_add,
            float(self.rate_limits[key])
        )
        self.last_update[key] = now


class BaseExchangeAdapter(ABC):
    """交易所适配器抽象基类"""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limiter = RateLimiter(self.get_rate_limits())

    @abstractmethod
    def get_exchange_id(self) -> str:
        """获取交易所ID"""
        pass

    @abstractmethod
    def get_rate_limits(self) -> Dict[str, int]:
        """获取限流配置"""
        pass

    @abstractmethod
    async def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 500
    ) -> List[KlineData]:
        """获取K线数据"""
        pass

    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> TickerData:
        """获取最新价格"""
        pass

    @abstractmethod
    async def fetch_orderbook(self, symbol: str, depth: int = 20) -> OrderbookData:
        """获取订单簿"""
        pass

    @abstractmethod
    async def subscribe_klines(
        self,
        symbol: str,
        interval: str,
        callback: Callable
    ):
        """订阅实时K线"""
        pass

    @abstractmethod
    async def subscribe_ticker(
        self,
        symbol: str,
        callback: Callable
    ):
        """订阅实时价格"""
        pass

    @abstractmethod
    def normalize_symbol(self, symbol: str) -> str:
        """标准化交易对名称 (转换为交易所格式)"""
        pass

    @abstractmethod
    def parse_kline(self, raw_data: any) -> KlineData:
        """解析K线数据"""
        pass
