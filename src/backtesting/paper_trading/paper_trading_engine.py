"""
模拟交易引擎

使用实时数据进行模拟交易，不真实下单
"""

import logging
from typing import Dict, Optional
from datetime import datetime
import time

from ..engine.event_engine import EventQueue, EventType
from ..engine.portfolio import Portfolio
from ..engine.execution_handler import SimulatedExecutionHandler

logger = logging.getLogger(__name__)


class PaperTradingEngine:
    """
    模拟交易引擎

    使用实时数据进行模拟交易
    """

    def __init__(
        self,
        initial_capital: float,
        strategy,
        data_source,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005
    ):
        """
        初始化模拟交易引擎

        Args:
            initial_capital: 初始资金
            strategy: 策略对象
            data_source: 数据源
            commission_rate: 手续费率
            slippage_rate: 滑点率
        """
        self.initial_capital = initial_capital
        self.strategy = strategy
        self.data_source = data_source

        # 初始化组件
        self.events = EventQueue()
        self.portfolio = Portfolio(initial_capital)
        self.execution_handler = SimulatedExecutionHandler(commission_rate, slippage_rate)

        # 状态
        self.is_running = False
        self.current_time = None

        logger.info("PaperTradingEngine initialized")

    def start(self) -> None:
        """启动模拟交易"""
        logger.info("Starting paper trading...")
        self.is_running = True

        try:
            while self.is_running:
                # 获取最新市场数据
                market_event = self.data_source.get_latest_data()

                if market_event is None:
                    time.sleep(1)
                    continue

                self.current_time = market_event.timestamp
                self.events.put(market_event)

                # 处理事件队列
                self._process_events()

                # 更新权益
                current_prices = {market_event.symbol: market_event.close}
                self.portfolio.update_equity(self.current_time, current_prices)

                # 短暂休眠
                time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("Paper trading interrupted by user")
        except Exception as e:
            logger.error(f"Error in paper trading: {e}")
        finally:
            self.stop()

    def stop(self) -> None:
        """停止模拟交易"""
        logger.info("Stopping paper trading...")
        self.is_running = False

    def _process_events(self) -> None:
        """处理事件队列"""
        while not self.events.empty():
            event = self.events.get(block=False)

            if event is None:
                continue

            if event.type == EventType.MARKET:
                self._handle_market_event(event)
            elif event.type == EventType.SIGNAL:
                self._handle_signal_event(event)
            elif event.type == EventType.ORDER:
                self._handle_order_event(event)
            elif event.type == EventType.FILL:
                self._handle_fill_event(event)

    def _handle_market_event(self, event) -> None:
        """处理市场事件"""
        signals = self.strategy.calculate_signals(event, None)
        if signals:
            for signal in signals:
                self.events.put(signal)

    def _handle_signal_event(self, event) -> None:
        """处理信号事件"""
        # 生成订单逻辑（简化版）
        pass

    def _handle_order_event(self, event) -> None:
        """处理订单事件"""
        # 执行订单
        pass

    def _handle_fill_event(self, event) -> None:
        """处理成交事件"""
        self.portfolio.update_fill(event)

    def get_status(self) -> Dict:
        """获取当前状态"""
        return {
            'is_running': self.is_running,
            'current_time': self.current_time,
            'portfolio': self.portfolio.get_statistics()
        }
