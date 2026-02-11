"""
策略适配器

桥接 trading_engine 中的策略接口与回测引擎的事件驱动接口。

现有策略接口：
    analyze(df: DataFrame) -> Dict
    generate_signals(df: DataFrame, analysis: Dict) -> List[Dict]

回测引擎期望：
    calculate_signals(event: MarketEvent, data_handler: DataHandler) -> List[SignalEvent]
"""

import logging
from typing import List, Optional

import pandas as pd

from .event_engine import MarketEvent, SignalEvent
from .data_handler import DataHandler

logger = logging.getLogger(__name__)

# 策略信号字段到 SignalEvent 信号类型的映射
_SIGNAL_MAP = {
    'BUY': 'BUY',
    'SELL': 'SELL',
    'HOLD': 'HOLD',
}


class StrategyAdapter:
    """
    策略适配器

    将 BaseStrategy 子类（TrendFollowing / MeanReversion / Momentum）
    适配为回测引擎可调用的 calculate_signals 接口。
    """

    def __init__(self, strategy, min_bars: int = 50):
        """
        Args:
            strategy: BaseStrategy 子类实例
            min_bars: 策略所需的最小K线数量
        """
        self.strategy = strategy
        self.min_bars = min_bars

    def calculate_signals(
        self,
        event: MarketEvent,
        data_handler: DataHandler,
    ) -> Optional[List[SignalEvent]]:
        """
        回测引擎调用此方法获取信号

        Args:
            event: 当前市场事件
            data_handler: 数据处理器（用于获取历史K线）

        Returns:
            SignalEvent 列表，无信号时返回 None
        """
        # 获取足够的历史K线构建 DataFrame
        bars = data_handler.get_latest_bars(self.min_bars)
        if bars is None or len(bars) < self.min_bars:
            return None

        df = pd.DataFrame(bars)

        # 确保列名正确
        required = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required):
            return None

        try:
            # 调用策略的标准接口
            analysis = self.strategy.analyze(df)
            if not analysis:
                return None

            raw_signals = self.strategy.generate_signals(df, analysis)
            if not raw_signals:
                return None

            # 转换为 SignalEvent
            signal_events = []
            for sig in raw_signals:
                signal_type = _SIGNAL_MAP.get(
                    str(sig.get('signal', 'HOLD')).upper(),
                    'HOLD',
                )
                if signal_type == 'HOLD':
                    continue

                confidence = sig.get('confidence', 0.5)
                strength = float(confidence) if confidence else 0.5

                signal_event = SignalEvent(
                    symbol=event.symbol,
                    timestamp=event.timestamp,
                    signal_type=signal_type,
                    strength=strength,
                    price=event.close,
                    metadata={
                        'strategy': self.strategy.name,
                        'stop_loss': sig.get('stop_loss'),
                        'take_profit': sig.get('take_profit'),
                        'reason': sig.get('reason', ''),
                    },
                )
                signal_events.append(signal_event)

            return signal_events if signal_events else None

        except Exception as e:
            logger.error(f"策略适配器执行失败 [{self.strategy.name}]: {e}")
            return None
