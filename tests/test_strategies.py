"""
策略测试
"""

import pytest
import pandas as pd
import numpy as np

from src.trading_engine.strategies import (
    TrendFollowingStrategy,
    MeanReversionStrategy,
    MomentumStrategy,
    StrategyManager
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


def test_trend_following_strategy(sample_data):
    """测试趋势跟踪策略"""
    strategy = TrendFollowingStrategy()

    # 测试分析
    analysis = strategy.analyze(sample_data)
    assert 'short_ema' in analysis
    assert 'long_ema' in analysis
    assert 'adx' in analysis

    # 测试信号生成
    signals = strategy.generate_signals(sample_data, analysis)
    assert isinstance(signals, list)


def test_mean_reversion_strategy(sample_data):
    """测试均值回归策略"""
    strategy = MeanReversionStrategy()

    analysis = strategy.analyze(sample_data)
    assert 'bb_upper' in analysis
    assert 'bb_lower' in analysis
    assert 'rsi' in analysis

    signals = strategy.generate_signals(sample_data, analysis)
    assert isinstance(signals, list)


def test_momentum_strategy(sample_data):
    """测试动量策略"""
    strategy = MomentumStrategy()

    analysis = strategy.analyze(sample_data)
    assert 'momentum' in analysis
    assert 'roc' in analysis

    signals = strategy.generate_signals(sample_data, analysis)
    assert isinstance(signals, list)


def test_strategy_manager(sample_data):
    """测试策略管理器"""
    manager = StrategyManager()

    # 添加策略
    trend_strategy = TrendFollowingStrategy()
    mean_strategy = MeanReversionStrategy()

    manager.add_strategy(trend_strategy)
    manager.add_strategy(mean_strategy)

    # 测试策略列表
    strategies = manager.list_strategies()
    assert 'TrendFollowing' in strategies
    assert 'MeanReversion' in strategies

    # 测试运行所有策略
    all_signals = manager.run_all_strategies(sample_data)
    assert isinstance(all_signals, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
