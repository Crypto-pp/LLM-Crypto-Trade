"""
回测框架模块

提供完整的回测功能，包括：
- 事件驱动回测引擎
- 性能评估和分析
- 参数优化
- 模拟交易
"""

from .engine.backtest_engine import BacktestEngine
from .engine.event_engine import Event, MarketEvent, SignalEvent, OrderEvent, FillEvent
from .performance.metrics_calculator import MetricsCalculator
from .performance.performance_analyzer import PerformanceAnalyzer

__all__ = [
    'BacktestEngine',
    'Event',
    'MarketEvent',
    'SignalEvent',
    'OrderEvent',
    'FillEvent',
    'MetricsCalculator',
    'PerformanceAnalyzer',
]
