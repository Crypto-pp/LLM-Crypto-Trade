"""
技术指标测试
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.trading_engine.indicators import (
    calculate_ma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_atr,
    IndicatorManager
)


@pytest.fixture
def sample_data():
    """生成测试数据"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    data = pd.DataFrame({
        'open': np.random.uniform(100, 110, 100),
        'high': np.random.uniform(110, 120, 100),
        'low': np.random.uniform(90, 100, 100),
        'close': np.random.uniform(100, 110, 100),
        'volume': np.random.uniform(1000, 10000, 100)
    }, index=dates)

    return data


def test_calculate_ma(sample_data):
    """测试MA计算"""
    ma = calculate_ma(sample_data, period=20)

    assert len(ma) == len(sample_data)
    assert not ma.iloc[-1] == 0
    assert ma.iloc[:19].isna().all()  # 前19个值应该是NaN


def test_calculate_ema(sample_data):
    """测试EMA计算"""
    ema = calculate_ema(sample_data, period=20)

    assert len(ema) == len(sample_data)
    assert not ema.iloc[-1] == 0


def test_calculate_rsi(sample_data):
    """测试RSI计算"""
    rsi = calculate_rsi(sample_data, period=14)

    assert len(rsi) == len(sample_data)
    assert 0 <= rsi.iloc[-1] <= 100


def test_calculate_macd(sample_data):
    """测试MACD计算"""
    macd = calculate_macd(sample_data)

    assert 'macd' in macd
    assert 'signal' in macd
    assert 'histogram' in macd
    assert len(macd['macd']) == len(sample_data)


def test_calculate_bollinger_bands(sample_data):
    """测试布林带计算"""
    bb = calculate_bollinger_bands(sample_data)

    assert 'upper' in bb
    assert 'middle' in bb
    assert 'lower' in bb
    assert bb['upper'].iloc[-1] > bb['middle'].iloc[-1] > bb['lower'].iloc[-1]


def test_calculate_atr(sample_data):
    """测试ATR计算"""
    atr = calculate_atr(sample_data, period=14)

    assert len(atr) == len(sample_data)
    assert atr.iloc[-1] > 0


def test_indicator_manager(sample_data):
    """测试指标管理器"""
    manager = IndicatorManager()

    # 测试单个指标计算
    ma = manager.calculate(sample_data, 'ma', period=20)
    assert len(ma) == len(sample_data)

    # 测试批量计算
    indicators = {
        'ma': {'period': 20},
        'rsi': {'period': 14},
        'macd': {}
    }
    results = manager.calculate_multiple(sample_data, indicators)

    assert 'ma' in results
    assert 'rsi' in results
    assert 'macd' in results

    # 测试缓存
    ma2 = manager.calculate(sample_data, 'ma', period=20)
    assert ma.equals(ma2)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
