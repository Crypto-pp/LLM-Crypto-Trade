"""
交易所适配器测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.data_pipeline.adapters.binance import BinanceAdapter
from src.data_pipeline.adapters.base import KlineData


@pytest.mark.asyncio
async def test_binance_adapter_init():
    """测试Binance适配器初始化"""
    adapter = BinanceAdapter()

    assert adapter.get_exchange_id() == "binance"
    assert adapter.BASE_URL == "https://api.binance.com"
    assert adapter.rate_limiter is not None


@pytest.mark.asyncio
async def test_normalize_symbol():
    """测试交易对名称标准化"""
    adapter = BinanceAdapter()

    # BTC/USDT -> BTCUSDT
    assert adapter.normalize_symbol("BTC/USDT") == "BTCUSDT"
    assert adapter.normalize_symbol("ETH/USDT") == "ETHUSDT"

    # 反向转换
    assert adapter.denormalize_symbol("BTCUSDT") == "BTC/USDT"
    assert adapter.denormalize_symbol("ETHUSDT") == "ETH/USDT"


@pytest.mark.asyncio
async def test_parse_kline():
    """测试K线数据解析"""
    adapter = BinanceAdapter()

    # Binance K线格式
    raw_data = [
        1499040000000,      # 开盘时间
        "0.01634000",       # 开盘价
        "0.80000000",       # 最高价
        "0.01575800",       # 最低价
        "0.01577100",       # 收盘价
        "148976.11427815",  # 成交量
        1499644799999,      # 收盘时间
        "2434.19055334",    # 成交额
        308,                # 成交笔数
    ]

    kline = adapter.parse_kline(raw_data)

    assert isinstance(kline, KlineData)
    assert kline.open == Decimal("0.01634000")
    assert kline.high == Decimal("0.80000000")
    assert kline.low == Decimal("0.01575800")
    assert kline.close == Decimal("0.01577100")
    assert kline.volume == Decimal("148976.11427815")
    assert kline.quote_volume == Decimal("2434.19055334")
    assert kline.trades_count == 308


@pytest.mark.asyncio
@pytest.mark.integration
async def test_fetch_klines():
    """测试获取K线数据（集成测试）"""
    adapter = BinanceAdapter()

    # 获取最近100条1小时K线
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=100)

    klines = await adapter.fetch_klines(
        symbol="BTC/USDT",
        interval="1h",
        start_time=start_time,
        end_time=end_time,
        limit=100
    )

    assert len(klines) > 0
    assert all(isinstance(k, KlineData) for k in klines)

    # 验证数据顺序
    for i in range(1, len(klines)):
        assert klines[i].timestamp > klines[i-1].timestamp


@pytest.mark.asyncio
@pytest.mark.integration
async def test_fetch_ticker():
    """测试获取价格数据（集成测试）"""
    adapter = BinanceAdapter()

    ticker = await adapter.fetch_ticker("BTC/USDT")

    assert ticker is not None
    assert ticker.symbol == "BTC/USDT"
    assert ticker.last_price > 0
    assert ticker.timestamp is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_fetch_orderbook():
    """测试获取订单簿（集成测试）"""
    adapter = BinanceAdapter()

    orderbook = await adapter.fetch_orderbook("BTC/USDT", depth=20)

    assert orderbook is not None
    assert len(orderbook.bids) > 0
    assert len(orderbook.asks) > 0

    # 验证价格排序
    bid_prices = [float(p) for p, q in orderbook.bids]
    ask_prices = [float(p) for p, q in orderbook.asks]

    assert bid_prices == sorted(bid_prices, reverse=True)  # 买单降序
    assert ask_prices == sorted(ask_prices)  # 卖单升序
