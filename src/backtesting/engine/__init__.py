"""
回测引擎核心模块
"""

from .event_engine import (
    Event,
    MarketEvent,
    SignalEvent,
    OrderEvent,
    FillEvent,
    EventQueue
)
from .backtest_engine import BacktestEngine
from .data_handler import DataHandler, ExchangeDataHandler
from .execution_handler import ExecutionHandler
from .portfolio import Portfolio
from .strategy_adapter import StrategyAdapter

__all__ = [
    'Event',
    'MarketEvent',
    'SignalEvent',
    'OrderEvent',
    'FillEvent',
    'EventQueue',
    'BacktestEngine',
    'DataHandler',
    'ExchangeDataHandler',
    'ExecutionHandler',
    'Portfolio',
    'StrategyAdapter',
]
