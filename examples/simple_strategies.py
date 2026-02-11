"""
简单策略示例

演示如何创建一个基本的交易策略
"""

from typing import List
from src.backtesting.engine.event_engine import SignalEvent


class SimpleStrategy:
    """
    策略基类示例

    所有策略都应该实现 calculate_signals 方法
    """

    def __init__(self, **params):
        """
        初始化策略

        Args:
            **params: 策略参数
        """
        self.params = params

    def calculate_signals(self, market_event, data_handler) -> List[SignalEvent]:
        """
        计算交易信号

        Args:
            market_event: 市场事件
            data_handler: 数据处理器

        Returns:
            信号事件列表
        """
        raise NotImplementedError("Must implement calculate_signals()")


class BuyAndHoldStrategy(SimpleStrategy):
    """买入持有策略"""

    def __init__(self):
        super().__init__()
        self.bought = False

    def calculate_signals(self, market_event, data_handler) -> List[SignalEvent]:
        """只在第一次买入，然后一直持有"""
        signals = []

        if not self.bought:
            signal = SignalEvent(
                symbol=market_event.symbol,
                timestamp=market_event.timestamp,
                signal_type='BUY',
                strength=1.0,
                price=market_event.close
            )
            signals.append(signal)
            self.bought = True

        return signals


class RSIStrategy(SimpleStrategy):
    """RSI策略"""

    def __init__(self, period=14, oversold=30, overbought=70):
        super().__init__(period=period, oversold=oversold, overbought=overbought)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.prices = []

    def calculate_signals(self, market_event, data_handler) -> List[SignalEvent]:
        """基于RSI指标生成信号"""
        signals = []

        # 获取历史数据
        bars = data_handler.get_latest_bars(self.period + 1)
        if bars is None or len(bars) < self.period + 1:
            return signals

        # 计算RSI
        closes = [bar['close'] for bar in bars]
        rsi = self._calculate_rsi(closes, self.period)

        if rsi is None:
            return signals

        # 生成信号
        if rsi < self.oversold:
            # 超卖，买入信号
            signal = SignalEvent(
                symbol=market_event.symbol,
                timestamp=market_event.timestamp,
                signal_type='BUY',
                strength=1.0,
                price=market_event.close,
                metadata={'rsi': rsi}
            )
            signals.append(signal)

        elif rsi > self.overbought:
            # 超买，卖出信号
            signal = SignalEvent(
                symbol=market_event.symbol,
                timestamp=market_event.timestamp,
                signal_type='SELL',
                strength=1.0,
                price=market_event.close,
                metadata={'rsi': rsi}
            )
            signals.append(signal)

        return signals

    def _calculate_rsi(self, prices: List[float], period: int) -> float:
        """计算RSI指标"""
        if len(prices) < period + 1:
            return None

        # 计算价格变化
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]

        # 分离涨跌
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        # 计算平均涨跌
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100

        # 计算RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi
