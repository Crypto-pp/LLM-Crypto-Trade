"""
回测引擎测试
"""

import unittest
from datetime import datetime
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backtesting.engine.event_engine import (
    Event, EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent, EventQueue
)


class TestEventEngine(unittest.TestCase):
    """测试事件引擎"""

    def test_market_event_creation(self):
        """测试市场事件创建"""
        event = MarketEvent(
            symbol='BTC/USDT',
            timestamp=datetime.now(),
            open_price=50000,
            high_price=51000,
            low_price=49000,
            close_price=50500,
            volume=100
        )

        self.assertEqual(event.type, EventType.MARKET)
        self.assertEqual(event.symbol, 'BTC/USDT')
        self.assertEqual(event.close, 50500)

    def test_signal_event_creation(self):
        """测试信号事件创建"""
        event = SignalEvent(
            symbol='BTC/USDT',
            timestamp=datetime.now(),
            signal_type='BUY',
            strength=0.8,
            price=50000
        )

        self.assertEqual(event.type, EventType.SIGNAL)
        self.assertEqual(event.signal_type, 'BUY')
        self.assertEqual(event.strength, 0.8)

    def test_order_event_creation(self):
        """测试订单事件创建"""
        event = OrderEvent(
            symbol='BTC/USDT',
            timestamp=datetime.now(),
            order_type='MARKET',
            side='BUY',
            quantity=0.1,
            price=50000
        )

        self.assertEqual(event.type, EventType.ORDER)
        self.assertEqual(event.side, 'BUY')
        self.assertEqual(event.quantity, 0.1)

    def test_fill_event_creation(self):
        """测试成交事件创建"""
        event = FillEvent(
            symbol='BTC/USDT',
            timestamp=datetime.now(),
            side='BUY',
            quantity=0.1,
            fill_price=50000,
            commission=5.0
        )

        self.assertEqual(event.type, EventType.FILL)
        self.assertEqual(event.fill_cost, 5000)
        self.assertEqual(event.total_cost, 5005)

    def test_event_queue(self):
        """测试事件队列"""
        queue = EventQueue()

        # 添加事件
        event1 = MarketEvent('BTC/USDT', datetime.now(), 50000, 51000, 49000, 50500, 100)
        event2 = SignalEvent('BTC/USDT', datetime.now(), 'BUY', 1.0, 50000)

        queue.put(event1)
        queue.put(event2)

        self.assertEqual(queue.size(), 2)

        # 获取事件
        retrieved1 = queue.get(block=False)
        self.assertEqual(retrieved1.type, EventType.MARKET)

        retrieved2 = queue.get(block=False)
        self.assertEqual(retrieved2.type, EventType.SIGNAL)

        self.assertTrue(queue.empty())


if __name__ == '__main__':
    unittest.main()
