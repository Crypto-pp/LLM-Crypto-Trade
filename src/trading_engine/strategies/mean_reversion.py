"""
均值回归策略
基于布林带、RSI的超买超卖策略
"""

import pandas as pd
from typing import Dict, List, Any
import logging

from .base_strategy import BaseStrategy
from ..indicators import calculate_bollinger_bands, calculate_rsi

logger = logging.getLogger(__name__)


class MeanReversionStrategy(BaseStrategy):
    """
    均值回归策略
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        """
        初始化均值回归策略

        默认参数:
        - bb_period: 20
        - bb_std: 2.0
        - rsi_period: 14
        - rsi_oversold: 30
        - rsi_overbought: 70
        """
        default_params = {
            'bb_period': 20,
            'bb_std': 2.0,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'stop_loss_pct': 0.03,
            'take_profit_pct': 0.08
        }

        if parameters:
            default_params.update(parameters)

        super().__init__('MeanReversion', default_params)

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析市场超买超卖状态
        """
        try:
            # 计算指标
            bb = calculate_bollinger_bands(
                data,
                self.parameters['bb_period'],
                self.parameters['bb_std']
            )
            rsi = calculate_rsi(data, self.parameters['rsi_period'])

            current_price = data['close'].iloc[-1]

            # 计算价格在布林带中的位置
            bb_position = (current_price - bb['lower'].iloc[-1]) / \
                         (bb['upper'].iloc[-1] - bb['lower'].iloc[-1])

            analysis = {
                'bb_upper': bb['upper'].iloc[-1],
                'bb_middle': bb['middle'].iloc[-1],
                'bb_lower': bb['lower'].iloc[-1],
                'bb_bandwidth': bb['bandwidth'].iloc[-1],
                'bb_position': bb_position,
                'rsi': rsi.iloc[-1],
                'current_price': current_price
            }

            return analysis

        except Exception as e:
            logger.error(f"均值回归分析失败: {e}")
            return {}

    def generate_signals(self, data: pd.DataFrame, analysis: Dict) -> List[Dict]:
        """
        生成交易信号
        """
        signals = []

        try:
            # 买入条件：超卖
            buy_conditions = [
                analysis['current_price'] <= analysis['bb_lower'],  # 触及下轨
                analysis['rsi'] < self.parameters['rsi_oversold'],  # RSI超卖
                analysis['bb_position'] < 0.2  # 价格在布林带下方
            ]

            # 卖出条件：超买
            sell_conditions = [
                analysis['current_price'] >= analysis['bb_upper'],  # 触及上轨
                analysis['rsi'] > self.parameters['rsi_overbought'],  # RSI超买
                analysis['bb_position'] > 0.8  # 价格在布林带上方
            ]

            buy_score = sum(buy_conditions)
            sell_score = sum(sell_conditions)

            # 生成买入信号
            if buy_score >= 2:
                entry_price = analysis['current_price']
                stop_loss = entry_price * (1 - self.parameters['stop_loss_pct'])
                take_profit = analysis['bb_middle']  # 目标：回归中轨

                signal = {
                    'strategy': self.name,
                    'signal': 'BUY',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strength': buy_score,
                    'confidence': buy_score / 3.0,
                    'reason': f'均值回归买入信号 (超卖，{buy_score}/3条件满足)'
                }

                if self.check_risk(signal):
                    signals.append(signal)

            # 生成卖出信号
            elif sell_score >= 2:
                entry_price = analysis['current_price']
                stop_loss = entry_price * (1 + self.parameters['stop_loss_pct'])
                take_profit = analysis['bb_middle']  # 目标：回归中轨

                signal = {
                    'strategy': self.name,
                    'signal': 'SELL',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strength': sell_score,
                    'confidence': sell_score / 3.0,
                    'reason': f'均值回归卖出信号 (超买，{sell_score}/3条件满足)'
                }

                if self.check_risk(signal):
                    signals.append(signal)

        except Exception as e:
            logger.error(f"生成信号失败: {e}")

        return signals
