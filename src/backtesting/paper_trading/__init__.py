"""
模拟交易模块

提供模拟交易功能：
- 模拟交易引擎
- 执行模拟器
- 实时性能监控
"""

from .paper_trading_engine import PaperTradingEngine
from .execution_simulator import ExecutionSimulator
from .performance_monitor import PerformanceMonitor

__all__ = [
    'PaperTradingEngine',
    'ExecutionSimulator',
    'PerformanceMonitor',
]
