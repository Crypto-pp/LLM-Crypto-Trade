"""
动量策略
基于动量指标和相对强度的策略
"""

import pandas as pd
from typing import Dict, List, Any
import logging

from .base_strategy import BaseStrategy
from ..indicators import calculate_rsi, calculate_macd

logger = logging.getLogger(__name__)


class MomentumStrategy(BaseStrategy):
    """
    动量策略
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        """
        初始化动量策略

        默认参数:
        - momentum_period: 10
        - roc_period: 12
        - momentum_threshold: 5.0
        """
        default_params = {
            'momentum_period': 10,
            'roc_period': 12,
            'momentum_threshold': 5.0,
            'rsi_threshold': 60,
            'stop_loss_pct': 0.07,
            'take_profit_pct': 0.20
        }

        if parameters:
            default_params.update(parameters)

        super().__init__('Momentum', default_params)

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析市场动量
        """
        try:
            # 计算动量指标
            momentum = data['close'].diff(self.parameters['momentum_period'])
            momentum_pct = data['close'].pct_change(self.parameters['momentum_period']) * 100

            # 计算ROC
            roc = ((data['close'] - data['close'].shift(self.parameters['roc_period'])) /
                   data['close'].shift(self.parameters['roc_period'])) * 100

            # 计算RSI
            rsi = calculate_rsi(data)

            # 计算MACD
            macd = calculate_macd(data)

            # 检查是否创新高/新低
            high_20 = data['high'].rolling(window=20).max()
            low_20 = data['low'].rolling(window=20).min()

            analysis = {
                'momentum': momentum.iloc[-1],
                'momentum_pct': momentum_pct.iloc[-1],
                'roc': roc.iloc[-1],
                'rsi': rsi.iloc[-1],
                'macd_histogram': macd['histogram'].iloc[-1],
                'is_new_high': data['close'].iloc[-1] >= high_20.iloc[-1],
                'is_new_low': data['close'].iloc[-1] <= low_20.iloc[-1],
                'current_price': data['close'].iloc[-1]
            }

            return analysis

        except Exception as e:
            logger.error(f"动量分析失败: {e}")
            return {}

    def generate_signals(self, data: pd.DataFrame, analysis: Dict) -> List[Dict]:
        """
        生成交易信号
        """
        signals = []

        try:
            # 买入条件：强势动量
            buy_conditions = [
                analysis['momentum_pct'] > self.parameters['momentum_threshold'],
                analysis['roc'] > 3,
                analysis['is_new_high'],
                analysis['rsi'] > self.parameters['rsi_threshold'],
                analysis['macd_histogram'] > 0
            ]

            # 卖出条件：动量衰减
            sell_conditions = [
                analysis['momentum_pct'] < -self.parameters['momentum_threshold'],
                analysis['roc'] < -3,
                analysis['is_new_low'],
                analysis['rsi'] < (100 - self.parameters['rsi_threshold']),
                analysis['macd_histogram'] < 0
            ]

            buy_score = sum(buy_conditions)
            sell_score = sum(sell_conditions)

            # 生成买入信号
            if buy_score >= 3:
                entry_price = analysis['current_price']
                stop_loss = entry_price * (1 - self.parameters['stop_loss_pct'])
                take_profit = entry_price * (1 + self.parameters['take_profit_pct'])

                signal = {
                    'strategy': self.name,
                    'signal': 'BUY',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strength': buy_score,
                    'confidence': buy_score / 5.0,
                    'reason': f'动量买入信号 ({buy_score}/5条件满足)'
                }

                if self.check_risk(signal):
                    signals.append(signal)

            # 生成卖出信号
            elif sell_score >= 3:
                entry_price = analysis['current_price']
                stop_loss = entry_price * (1 + self.parameters['stop_loss_pct'])
                take_profit = entry_price * (1 - self.parameters['take_profit_pct'])

                signal = {
                    'strategy': self.name,
                    'signal': 'SELL',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strength': sell_score,
                    'confidence': sell_score / 5.0,
                    'reason': f'动量卖出信号 ({sell_score}/5条件满足)'
                }

                if self.check_risk(signal):
                    signals.append(signal)

        except Exception as e:
            logger.error(f"生成信号失败: {e}")

        return signals
