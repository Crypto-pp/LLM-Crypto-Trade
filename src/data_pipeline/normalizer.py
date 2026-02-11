"""
数据标准化模块

提供数据标准化、格式转换功能
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List
from loguru import logger

from .adapters.base import KlineData, TickerData, OrderbookData


class TimestampNormalizer:
    """时间戳标准化器"""

    @staticmethod
    def normalize(timestamp: any) -> datetime:
        """标准化时间戳为UTC datetime"""

        # 处理毫秒时间戳
        if isinstance(timestamp, int):
            if timestamp > 1e12:  # 毫秒
                return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            else:  # 秒
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)

        # 处理字符串
        elif isinstance(timestamp, str):
            # ISO 8601格式
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

        # 处理datetime对象
        elif isinstance(timestamp, datetime):
            if timestamp.tzinfo is None:
                return timestamp.replace(tzinfo=timezone.utc)
            return timestamp.astimezone(timezone.utc)

        else:
            raise ValueError(f"Unsupported timestamp type: {type(timestamp)}")

    @staticmethod
    def align_to_interval(timestamp: datetime, interval: str) -> datetime:
        """对齐时间戳到时间间隔

        例如: 2024-01-01 10:23:45 对齐到5分钟 -> 2024-01-01 10:20:00
        """
        interval_seconds = TimestampNormalizer._parse_interval_seconds(interval)

        # 转换为时间戳
        ts = int(timestamp.timestamp())

        # 对齐
        aligned_ts = (ts // interval_seconds) * interval_seconds

        return datetime.fromtimestamp(aligned_ts, tz=timezone.utc)

    @staticmethod
    def _parse_interval_seconds(interval: str) -> int:
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


class PriceNormalizer:
    """价格精度标准化器"""

    def __init__(self):
        # 不同交易对的精度配置
        self.precision_config = {
            'BTC/USDT': 2,
            'ETH/USDT': 2,
            'BNB/USDT': 2,
            'default': 8
        }

    def normalize_price(self, price: float, symbol: str) -> Decimal:
        """标准化价格精度"""
        precision = self.precision_config.get(symbol, self.precision_config['default'])

        decimal_price = Decimal(str(price))
        quantize_str = '0.' + '0' * precision

        return decimal_price.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)

    def normalize_kline(self, kline: KlineData, symbol: str) -> KlineData:
        """标准化K线数据的价格精度"""
        return KlineData(
            timestamp=kline.timestamp,
            open=self.normalize_price(float(kline.open), symbol),
            high=self.normalize_price(float(kline.high), symbol),
            low=self.normalize_price(float(kline.low), symbol),
            close=self.normalize_price(float(kline.close), symbol),
            volume=kline.volume,
            quote_volume=kline.quote_volume,
            trades_count=kline.trades_count
        )


class SymbolNormalizer:
    """交易对命名标准化器"""

    @staticmethod
    def to_standard(symbol: str, exchange: str) -> str:
        """转换为标准格式: BTC/USDT"""

        # 移除空格和特殊字符
        symbol = symbol.strip().upper()

        # 不同交易所的格式转换
        if exchange == 'binance':
            # BTCUSDT -> BTC/USDT
            if '/' not in symbol:
                quote_currencies = ['USDT', 'USDC', 'BUSD', 'BTC', 'ETH', 'BNB']
                for quote in quote_currencies:
                    if symbol.endswith(quote):
                        base = symbol[:-len(quote)]
                        return f"{base}/{quote}"
            return symbol

        elif exchange == 'okx':
            # BTC-USDT -> BTC/USDT
            return symbol.replace('-', '/')

        elif exchange == 'coinbase':
            # BTC-USD -> BTC/USD
            return symbol.replace('-', '/')

        else:
            return symbol

    @staticmethod
    def to_exchange_format(symbol: str, exchange: str) -> str:
        """转换为交易所格式"""

        if exchange == 'binance':
            return symbol.replace('/', '')
        elif exchange == 'okx':
            return symbol.replace('/', '-')
        elif exchange == 'coinbase':
            return symbol.replace('/', '-')
        else:
            return symbol


class DataNormalizer:
    """数据标准化器（统一接口）"""

    def __init__(self):
        self.timestamp_normalizer = TimestampNormalizer()
        self.price_normalizer = PriceNormalizer()
        self.symbol_normalizer = SymbolNormalizer()

    def normalize_kline(
        self,
        kline: KlineData,
        symbol: str,
        exchange: str
    ) -> KlineData:
        """标准化K线数据"""

        # 标准化交易对名称
        standard_symbol = self.symbol_normalizer.to_standard(symbol, exchange)

        # 标准化价格精度
        normalized_kline = self.price_normalizer.normalize_kline(kline, standard_symbol)

        # 对齐时间戳（如果需要）
        # normalized_kline.timestamp = self.timestamp_normalizer.align_to_interval(
        #     normalized_kline.timestamp, interval
        # )

        return normalized_kline

    def normalize_ticker(
        self,
        ticker: TickerData,
        exchange: str
    ) -> TickerData:
        """标准化价格数据"""

        # 标准化交易对名称
        standard_symbol = self.symbol_normalizer.to_standard(ticker.symbol, exchange)

        return TickerData(
            timestamp=ticker.timestamp,
            symbol=standard_symbol,
            last_price=ticker.last_price,
            bid_price=ticker.bid_price,
            ask_price=ticker.ask_price,
            volume_24h=ticker.volume_24h,
            price_change_24h=ticker.price_change_24h
        )

    def normalize_orderbook(
        self,
        orderbook: OrderbookData,
        exchange: str
    ) -> OrderbookData:
        """标准化订单簿数据"""

        # 标准化交易对名称
        standard_symbol = self.symbol_normalizer.to_standard(orderbook.symbol, exchange)

        return OrderbookData(
            timestamp=orderbook.timestamp,
            symbol=standard_symbol,
            bids=orderbook.bids,
            asks=orderbook.asks,
            checksum=orderbook.checksum
        )
