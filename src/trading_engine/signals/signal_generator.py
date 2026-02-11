"""
信号生成器
从策略生成信号，进行验证和过滤
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .signal_types import Signal, SignalType, SignalStrength

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    信号生成器
    """

    def __init__(self, min_confidence: float = 0.6, min_risk_reward: float = 2.0):
        """
        初始化信号生成器

        Args:
            min_confidence: 最小置信度
            min_risk_reward: 最小风险收益比
        """
        self.min_confidence = min_confidence
        self.min_risk_reward = min_risk_reward
        logger.info("信号生成器已初始化")

    def generate_from_strategy(
        self,
        strategy_signals: List[Dict],
        symbol: str,
        exchange: str = 'binance'
    ) -> List[Signal]:
        """
        从策略信号生成标准信号对象

        Args:
            strategy_signals: 策略生成的信号列表
            symbol: 交易对
            exchange: 交易所

        Returns:
            Signal对象列表
        """
        signals = []

        for sig in strategy_signals:
            try:
                # 转换信号类型
                signal_type = SignalType(sig['signal'])

                # 转换信号强度
                strength = self._convert_strength(sig.get('strength', 5))

                # 创建Signal对象
                signal = Signal(
                    signal_id='',
                    symbol=symbol,
                    exchange=exchange,
                    signal_type=signal_type,
                    entry_price=sig['entry_price'],
                    stop_loss=sig['stop_loss'],
                    take_profit=sig['take_profit'],
                    timestamp=datetime.now(),
                    strategy=sig.get('strategy', 'unknown'),
                    confidence=sig.get('confidence', 0.5),
                    strength=strength,
                    valid_until=datetime.now() + timedelta(hours=24),
                    metadata=sig.get('metadata', {}),
                    reason=sig.get('reason', '')
                )

                # 验证信号
                if self.validate_signal(signal):
                    signals.append(signal)
                else:
                    logger.warning(f"信号验证失败: {signal.signal_id}")

            except Exception as e:
                logger.error(f"生成信号失败: {e}")

        return signals

    def validate_signal(self, signal: Signal) -> bool:
        """
        验证信号

        Args:
            signal: 信号对象

        Returns:
            是否通过验证
        """
        # 检查置信度
        if signal.confidence < self.min_confidence:
            logger.debug(f"置信度不足: {signal.confidence}")
            return False

        # 检查风险收益比
        risk_reward = signal.calculate_risk_reward_ratio()
        if risk_reward < self.min_risk_reward:
            logger.debug(f"风险收益比不足: {risk_reward}")
            return False

        # 检查价格有效性
        if signal.entry_price <= 0 or signal.stop_loss <= 0 or signal.take_profit <= 0:
            logger.debug("价格无效")
            return False

        # 检查止损止盈逻辑
        if signal.signal_type == SignalType.BUY:
            if signal.stop_loss >= signal.entry_price or signal.take_profit <= signal.entry_price:
                logger.debug("买入信号止损止盈逻辑错误")
                return False
        elif signal.signal_type == SignalType.SELL:
            if signal.stop_loss <= signal.entry_price or signal.take_profit >= signal.entry_price:
                logger.debug("卖出信号止损止盈逻辑错误")
                return False

        return True

    def filter_by_risk(self, signals: List[Signal], max_risk_per_trade: float = 0.02) -> List[Signal]:
        """
        按风险过滤信号

        Args:
            signals: 信号列表
            max_risk_per_trade: 单笔最大风险比例

        Returns:
            过滤后的信号列表
        """
        filtered = []

        for signal in signals:
            risk_pct = abs(signal.entry_price - signal.stop_loss) / signal.entry_price

            if risk_pct <= max_risk_per_trade:
                filtered.append(signal)
            else:
                logger.warning(f"信号风险过高: {risk_pct:.2%}")

        return filtered

    def prioritize_signals(self, signals: List[Signal]) -> List[Signal]:
        """
        对信号进行优先级排序

        Args:
            signals: 信号列表

        Returns:
            排序后的信号列表
        """
        # 按置信度和强度排序
        return sorted(
            signals,
            key=lambda s: (s.confidence * s.strength.value),
            reverse=True
        )

    def _convert_strength(self, strength_value: int) -> SignalStrength:
        """转换信号强度"""
        if strength_value >= 9:
            return SignalStrength.VERY_STRONG
        elif strength_value >= 7:
            return SignalStrength.STRONG
        elif strength_value >= 5:
            return SignalStrength.MODERATE
        elif strength_value >= 3:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK
