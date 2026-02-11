"""
价格行为策略
基于K线形态、支撑阻力、市场结构的策略
"""

import pandas as pd
from typing import Dict, List, Any
import logging

from .base_strategy import BaseStrategy
from ..price_action import (
    identify_pin_bar,
    identify_engulfing,
    identify_support_resistance,
    identify_market_structure
)

logger = logging.getLogger(__name__)


class PriceActionStrategy(BaseStrategy):
    """
    价格行为策略
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        """
        初始化价格行为策略
        """
        default_params = {
            'lookback': 50,
            'stop_loss_pct': 0.03,
            'take_profit_pct': 0.10
        }

        if parameters:
            default_params.update(parameters)

        super().__init__('PriceAction', default_params)

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析价格行为
        """
        try:
            # 识别K线形态
            last_candle = data.iloc[-1]
            prev_candle = data.iloc[-2] if len(data) > 1 else None

            pin_bar = identify_pin_bar(last_candle)
            engulfing = identify_engulfing(prev_candle, last_candle) if prev_candle is not None else None

            # 识别支撑阻力
            sr_levels = identify_support_resistance(data, self.parameters['lookback'])

            # 识别市场结构
            market_structure = identify_market_structure(data)

            analysis = {
                'pin_bar': pin_bar,
                'engulfing': engulfing,
                'support_levels': sr_levels['support'],
                'resistance_levels': sr_levels['resistance'],
                'market_structure': market_structure,
                'current_price': data['close'].iloc[-1]
            }

            return analysis

        except Exception as e:
            logger.error(f"价格行为分析失败: {e}")
            return {}

    def generate_signals(self, data: pd.DataFrame, analysis: Dict) -> List[Dict]:
        """
        生成交易信号
        """
        signals = []

        try:
            current_price = analysis['current_price']

            # 基于Pin Bar的信号
            if analysis.get('pin_bar'):
                pin_bar = analysis['pin_bar']
                if pin_bar['signal'] == 'buy':
                    signal = {
                        'strategy': self.name,
                        'signal': 'BUY',
                        'entry_price': current_price,
                        'stop_loss': current_price * (1 - self.parameters['stop_loss_pct']),
                        'take_profit': current_price * (1 + self.parameters['take_profit_pct']),
                        'strength': 8,
                        'confidence': pin_bar['confidence'],
                        'reason': f"看涨Pin Bar: {pin_bar['description']}"
                    }
                    if self.check_risk(signal):
                        signals.append(signal)

                elif pin_bar['signal'] == 'sell':
                    signal = {
                        'strategy': self.name,
                        'signal': 'SELL',
                        'entry_price': current_price,
                        'stop_loss': current_price * (1 + self.parameters['stop_loss_pct']),
                        'take_profit': current_price * (1 - self.parameters['take_profit_pct']),
                        'strength': 8,
                        'confidence': pin_bar['confidence'],
                        'reason': f"看跌Pin Bar: {pin_bar['description']}"
                    }
                    if self.check_risk(signal):
                        signals.append(signal)

            # 基于吞没形态的信号
            if analysis.get('engulfing'):
                engulfing = analysis['engulfing']
                if engulfing['signal'] == 'buy':
                    signal = {
                        'strategy': self.name,
                        'signal': 'BUY',
                        'entry_price': current_price,
                        'stop_loss': current_price * (1 - self.parameters['stop_loss_pct']),
                        'take_profit': current_price * (1 + self.parameters['take_profit_pct']),
                        'strength': 7,
                        'confidence': engulfing['confidence'],
                        'reason': f"看涨吞没: {engulfing['description']}"
                    }
                    if self.check_risk(signal):
                        signals.append(signal)

                elif engulfing['signal'] == 'sell':
                    signal = {
                        'strategy': self.name,
                        'signal': 'SELL',
                        'entry_price': current_price,
                        'stop_loss': current_price * (1 + self.parameters['stop_loss_pct']),
                        'take_profit': current_price * (1 - self.parameters['take_profit_pct']),
                        'strength': 7,
                        'confidence': engulfing['confidence'],
                        'reason': f"看跌吞没: {engulfing['description']}"
                    }
                    if self.check_risk(signal):
                        signals.append(signal)

        except Exception as e:
            logger.error(f"生成信号失败: {e}")

        return signals
