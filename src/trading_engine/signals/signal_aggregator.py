"""
信号聚合器
多策略信号聚合，冲突处理，最终决策
"""

from typing import List, Dict, Optional
from datetime import datetime
import logging

from .signal_types import Signal, SignalType

logger = logging.getLogger(__name__)


class SignalAggregator:
    """
    信号聚合器
    """

    def __init__(self, min_supporting_strategies: int = 2):
        """
        初始化信号聚合器

        Args:
            min_supporting_strategies: 最少支持策略数量
        """
        self.min_supporting_strategies = min_supporting_strategies
        logger.info("信号聚合器已初始化")

    def aggregate(self, signals: List[Signal]) -> Optional[Signal]:
        """
        聚合多个信号

        Args:
            signals: 信号列表

        Returns:
            聚合后的信号
        """
        if not signals:
            return None

        # 按信号类型分组
        buy_signals = [s for s in signals if s.signal_type == SignalType.BUY]
        sell_signals = [s for s in signals if s.signal_type == SignalType.SELL]

        # 处理冲突
        if buy_signals and sell_signals:
            return self._resolve_conflict(buy_signals, sell_signals)

        # 聚合买入信号
        if len(buy_signals) >= self.min_supporting_strategies:
            return self._aggregate_signals(buy_signals, SignalType.BUY)

        # 聚合卖出信号
        if len(sell_signals) >= self.min_supporting_strategies:
            return self._aggregate_signals(sell_signals, SignalType.SELL)

        logger.info("信号数量不足，无法生成聚合信号")
        return None

    def _aggregate_signals(self, signals: List[Signal], signal_type: SignalType) -> Signal:
        """
        聚合同类型信号
        """
        # 计算平均值
        avg_entry = sum(s.entry_price for s in signals) / len(signals)
        avg_stop_loss = sum(s.stop_loss for s in signals) / len(signals)
        avg_take_profit = sum(s.take_profit for s in signals) / len(signals)
        avg_confidence = sum(s.confidence for s in signals) / len(signals)

        # 使用最高强度
        max_strength = max(s.strength for s in signals)

        # 合并策略名称
        strategies = [s.strategy for s in signals]

        # 创建聚合信号
        aggregated = Signal(
            signal_id='',
            symbol=signals[0].symbol,
            exchange=signals[0].exchange,
            signal_type=signal_type,
            entry_price=avg_entry,
            stop_loss=avg_stop_loss,
            take_profit=avg_take_profit,
            timestamp=datetime.now(),
            strategy='aggregated',
            confidence=avg_confidence,
            strength=max_strength,
            metadata={
                'supporting_strategies': len(signals),
                'strategies': strategies
            },
            reason=f"{len(signals)}个策略支持{signal_type.value}"
        )

        return aggregated

    def _resolve_conflict(
        self,
        buy_signals: List[Signal],
        sell_signals: List[Signal]
    ) -> Optional[Signal]:
        """
        解决信号冲突
        """
        logger.warning("检测到信号冲突")

        # 计算买入和卖出的总置信度
        buy_confidence = sum(s.confidence for s in buy_signals) / len(buy_signals)
        sell_confidence = sum(s.confidence for s in sell_signals) / len(sell_signals)

        # 选择置信度更高的方向
        if buy_confidence > sell_confidence * 1.2:  # 买入置信度明显更高
            logger.info("选择买入信号")
            return self._aggregate_signals(buy_signals, SignalType.BUY)
        elif sell_confidence > buy_confidence * 1.2:  # 卖出置信度明显更高
            logger.info("选择卖出信号")
            return self._aggregate_signals(sell_signals, SignalType.SELL)
        else:
            logger.info("信号冲突无法解决，返回HOLD")
            return None
