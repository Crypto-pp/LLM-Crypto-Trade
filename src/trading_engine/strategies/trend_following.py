"""
趋势跟踪策略
基于MA/EMA、MACD、ADX的趋势策略
"""

import pandas as pd
from typing import Dict, List, Any
import logging

from .base_strategy import BaseStrategy
from ..indicators import calculate_ema, calculate_macd, calculate_adx, calculate_rsi

logger = logging.getLogger(__name__)


class TrendFollowingStrategy(BaseStrategy):
    """
    趋势跟踪策略
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        """
        初始化趋势跟踪策略

        默认参数:
        - short_ma: 20
        - long_ma: 50
        - signal_ma: 200
        - adx_threshold: 25
        - volume_multiplier: 1.5
        """
        default_params = {
            'short_ma': 20,
            'long_ma': 50,
            'signal_ma': 200,
            'adx_threshold': 25,
            'volume_multiplier': 1.5,
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.15
        }

        if parameters:
            default_params.update(parameters)

        super().__init__('TrendFollowing', default_params)

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析市场趋势
        """
        try:
            # 计算指标
            short_ema = calculate_ema(data, self.parameters['short_ma'])
            long_ema = calculate_ema(data, self.parameters['long_ma'])
            signal_ema = calculate_ema(data, self.parameters['signal_ma'])
            macd = calculate_macd(data)
            adx = calculate_adx(data)
            rsi = calculate_rsi(data)

            # 计算成交量比率
            avg_volume = data['volume'].rolling(window=20).mean()
            volume_ratio = data['volume'] / avg_volume

            analysis = {
                'short_ema': short_ema.iloc[-1],
                'long_ema': long_ema.iloc[-1],
                'signal_ema': signal_ema.iloc[-1],
                'macd': macd['macd'].iloc[-1],
                'macd_signal': macd['signal'].iloc[-1],
                'macd_histogram': macd['histogram'].iloc[-1],
                'adx': adx['adx'].iloc[-1],
                'plus_di': adx['plus_di'].iloc[-1],
                'minus_di': adx['minus_di'].iloc[-1],
                'rsi': rsi.iloc[-1],
                'volume_ratio': volume_ratio.iloc[-1],
                'current_price': data['close'].iloc[-1]
            }

            return analysis

        except Exception as e:
            logger.error(f"趋势分析失败: {e}")
            return {}

    def generate_signals(self, data: pd.DataFrame, analysis: Dict) -> List[Dict]:
        """
        生成交易信号
        """
        signals = []

        try:
            # 多头信号条件
            bullish_conditions = [
                analysis['short_ema'] > analysis['long_ema'],  # 金叉
                analysis['current_price'] > analysis['signal_ema'],  # 价格在200MA上方
                analysis['adx'] > self.parameters['adx_threshold'],  # 趋势明显
                analysis['plus_di'] > analysis['minus_di'],  # 上升趋势
                analysis['volume_ratio'] > self.parameters['volume_multiplier']  # 成交量确认
            ]

            # 空头信号条件
            bearish_conditions = [
                analysis['short_ema'] < analysis['long_ema'],  # 死叉
                analysis['current_price'] < analysis['signal_ema'],  # 价格在200MA下方
                analysis['adx'] > self.parameters['adx_threshold'],  # 趋势明显
                analysis['minus_di'] > analysis['plus_di'],  # 下降趋势
                analysis['volume_ratio'] > self.parameters['volume_multiplier']  # 成交量确认
            ]

            # 计算信号强度
            bullish_score = sum(bullish_conditions)
            bearish_score = sum(bearish_conditions)

            # 生成买入信号
            if bullish_score >= 3:
                entry_price = analysis['current_price']
                stop_loss = entry_price * (1 - self.parameters['stop_loss_pct'])
                take_profit = entry_price * (1 + self.parameters['take_profit_pct'])

                signal = {
                    'strategy': self.name,
                    'signal': 'BUY',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strength': bullish_score,
                    'confidence': bullish_score / 5.0,
                    'reason': f'趋势跟踪买入信号 ({bullish_score}/5条件满足)'
                }

                if self.check_risk(signal):
                    signals.append(signal)

            # 生成卖出信号
            elif bearish_score >= 3:
                entry_price = analysis['current_price']
                stop_loss = entry_price * (1 + self.parameters['stop_loss_pct'])
                take_profit = entry_price * (1 - self.parameters['take_profit_pct'])

                signal = {
                    'strategy': self.name,
                    'signal': 'SELL',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strength': bearish_score,
                    'confidence': bearish_score / 5.0,
                    'reason': f'趋势跟踪卖出信号 ({bearish_score}/5条件满足)'
                }

                if self.check_risk(signal):
                    signals.append(signal)

        except Exception as e:
            logger.error(f"生成信号失败: {e}")

        return signals
