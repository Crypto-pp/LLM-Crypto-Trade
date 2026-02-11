"""
数据标准化测试
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal

from src.data_pipeline.normalizer import (
    TimestampNormalizer,
    PriceNormalizer,
    SymbolNormalizer,
    DataNormalizer
)
from src.data_pipeline.adapters.base import KlineData


def test_timestamp_normalizer():
    """测试时间戳标准化"""
    normalizer = TimestampNormalizer()

    # 测试毫秒时间戳
    ts_ms = 1609459200000  # 2021-01-01 00:00:00 UTC
    dt = normalizer.normalize(ts_ms)
    assert dt.year == 2021
    assert dt.month == 1
    assert dt.day == 1

    # 测试秒时间戳
    ts_s = 1609459200
    dt = normalizer.normalize(ts_s)
    assert dt.year == 2021

    # 测试ISO字符串
    iso_str = "2021-01-01T00:00:00Z"
    dt = normalizer.normalize(iso_str)
    assert dt.year == 2021


def test_timestamp_align():
    """测试时间戳对齐"""
    normalizer = TimestampNormalizer()

    # 对齐到5分钟
    dt = datetime(2024, 1, 1, 10, 23, 45, tzinfo=timezone.utc)
    aligned = normalizer.align_to_interval(dt, "5m")

    assert aligned.hour == 10
    assert aligned.minute == 20
    assert aligned.second == 0


def test_price_normalizer():
    """测试价格精度标准化"""
    normalizer = PriceNormalizer()

    # BTC/USDT 精度为2
    price = normalizer.normalize_price(50123.456789, "BTC/USDT")
    assert price == Decimal("50123.46")

    # 默认精度为8
    price = normalizer.normalize_price(0.123456789, "UNKNOWN/USDT")
    assert price == Decimal("0.12345679")


def test_symbol_normalizer():
    """测试交易对名称标准化"""
    normalizer = SymbolNormalizer()

    # Binance格式转换
    assert normalizer.to_standard("BTCUSDT", "binance") == "BTC/USDT"
    assert normalizer.to_exchange_format("BTC/USDT", "binance") == "BTCUSDT"

    # OKX格式转换
    assert normalizer.to_standard("BTC-USDT", "okx") == "BTC/USDT"
    assert normalizer.to_exchange_format("BTC/USDT", "okx") == "BTC-USDT"


def test_data_normalizer():
    """测试数据标准化器"""
    normalizer = DataNormalizer()

    kline = KlineData(
        timestamp=datetime.now(timezone.utc),
        open=Decimal("50000.123456"),
        high=Decimal("51000.654321"),
        low=Decimal("49000.111111"),
        close=Decimal("50500.999999"),
        volume=Decimal("100.5")
    )

    normalized = normalizer.normalize_kline(kline, "BTC/USDT", "binance")

    # 验证精度
    assert normalized.open == Decimal("50000.12")
    assert normalized.high == Decimal("51000.65")
    assert normalized.low == Decimal("49000.11")
    assert normalized.close == Decimal("50500.10")
