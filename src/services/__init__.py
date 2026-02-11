"""
服务层模块

提供信号调度和信号存储等业务服务。
SignalScheduler 有重依赖（ccxt/pandas/numpy），按需导入。
"""

from .signal_store import SignalStore

__all__ = ["SignalStore"]
