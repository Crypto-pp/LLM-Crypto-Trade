"""
图表形态识别模块
识别双顶/双底、头肩顶/头肩底、三角形、旗形等形态
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import logging

from .market_structure import find_swing_highs_lows

logger = logging.getLogger(__name__)


def find_peaks(data: pd.DataFrame, lookback: int = 50) -> List[Dict]:
    """查找价格峰值（委托给统一的摆动点查找函数）"""
    swings = find_swing_highs_lows(data, lookback=lookback)
    return swings['swing_highs']


def find_troughs(data: pd.DataFrame, lookback: int = 50) -> List[Dict]:
    """查找价格谷值（委托给统一的摆动点查找函数）"""
    swings = find_swing_highs_lows(data, lookback=lookback)
    return swings['swing_lows']


def identify_double_top_bottom(
    data: pd.DataFrame,
    lookback: int = 50,
    price_tolerance: float = 0.03
) -> Optional[Dict]:
    """
    识别双顶/双底形态

    Args:
        data: 价格数据
        lookback: 回看周期
        price_tolerance: 价格容差（3%）
    """
    try:
        peaks = find_peaks(data, lookback)

        if len(peaks) >= 2:
            peak1, peak2 = peaks[-2], peaks[-1]
            price_diff = abs(peak1['price'] - peak2['price']) / peak1['price']

            if price_diff < price_tolerance:
                # 找到两个峰值之间的谷值
                trough_data = data.iloc[peak1['index']:peak2['index']]
                if len(trough_data) > 0:
                    trough_price = trough_data['low'].min()
                    pullback = (peak1['price'] - trough_price) / peak1['price']

                    if pullback > 0.05:  # 回调超过5%
                        neckline = trough_price
                        current_price = data['close'].iloc[-1]

                        if current_price < neckline:
                            return {
                                'type': 'double_top',
                                'signal': 'sell',
                                'neckline': neckline,
                                'target': neckline - (peak1['price'] - neckline),
                                'stop_loss': peak2['price'],
                                'confidence': 0.75,
                                'description': '双顶形态，跌破颈线确认'
                            }

        # 检查双底
        troughs = find_troughs(data, lookback)

        if len(troughs) >= 2:
            trough1, trough2 = troughs[-2], troughs[-1]
            price_diff = abs(trough1['price'] - trough2['price']) / trough1['price']

            if price_diff < price_tolerance:
                peak_data = data.iloc[trough1['index']:trough2['index']]
                if len(peak_data) > 0:
                    peak_price = peak_data['high'].max()
                    rally = (peak_price - trough1['price']) / trough1['price']

                    if rally > 0.05:
                        neckline = peak_price
                        current_price = data['close'].iloc[-1]

                        if current_price > neckline:
                            return {
                                'type': 'double_bottom',
                                'signal': 'buy',
                                'neckline': neckline,
                                'target': neckline + (neckline - trough1['price']),
                                'stop_loss': trough2['price'],
                                'confidence': 0.75,
                                'description': '双底形态，突破颈线确认'
                            }

        return None
    except Exception as e:
        logger.error(f"识别双顶/双底失败: {e}")
        return None


def identify_head_shoulders(
    data: pd.DataFrame,
    lookback: int = 100
) -> Optional[Dict]:
    """识别头肩顶/头肩底形态"""
    try:
        peaks = find_peaks(data, lookback // 3)

        if len(peaks) >= 3:
            left_shoulder, head, right_shoulder = peaks[-3:]

            # 检查头肩顶
            if (head['price'] > left_shoulder['price'] and
                head['price'] > right_shoulder['price'] and
                abs(left_shoulder['price'] - right_shoulder['price']) / left_shoulder['price'] < 0.05):

                return {
                    'type': 'head_and_shoulders_top',
                    'signal': 'sell',
                    'confidence': 0.80,
                    'description': '头肩顶形态，强烈看跌信号'
                }

        troughs = find_troughs(data, lookback // 3)

        if len(troughs) >= 3:
            left_shoulder, head, right_shoulder = troughs[-3:]

            # 检查头肩底
            if (head['price'] < left_shoulder['price'] and
                head['price'] < right_shoulder['price'] and
                abs(left_shoulder['price'] - right_shoulder['price']) / left_shoulder['price'] < 0.05):

                return {
                    'type': 'head_and_shoulders_bottom',
                    'signal': 'buy',
                    'confidence': 0.80,
                    'description': '头肩底形态，强烈看涨信号'
                }

        return None
    except Exception as e:
        logger.error(f"识别头肩形态失败: {e}")
        return None


def identify_triangle(
    data: pd.DataFrame,
    lookback: int = 50
) -> Optional[Dict]:
    """识别三角形整理形态"""
    try:
        highs = find_peaks(data, lookback // 5)
        lows = find_troughs(data, lookback // 5)

        if len(highs) < 2 or len(lows) < 2:
            return None

        # 计算高点和低点的趋势
        high_prices = [h['price'] for h in highs[-3:]]
        low_prices = [l['price'] for l in lows[-3:]]

        high_trend = np.polyfit(range(len(high_prices)), high_prices, 1)[0]
        low_trend = np.polyfit(range(len(low_prices)), low_prices, 1)[0]

        # 上升三角形：水平阻力 + 上升支撑
        if abs(high_trend) < 0.001 and low_trend > 0.01:
            return {
                'type': 'ascending_triangle',
                'signal': 'bullish_breakout_expected',
                'resistance': highs[-1]['price'],
                'confidence': 0.75,
                'description': '上升三角形，看涨突破预期'
            }

        # 下降三角形：水平支撑 + 下降阻力
        if abs(low_trend) < 0.001 and high_trend < -0.01:
            return {
                'type': 'descending_triangle',
                'signal': 'bearish_breakdown_expected',
                'support': lows[-1]['price'],
                'confidence': 0.75,
                'description': '下降三角形，看跌突破预期'
            }

        # 对称三角形
        if low_trend > 0.01 and high_trend < -0.01:
            return {
                'type': 'symmetrical_triangle',
                'signal': 'breakout_pending',
                'confidence': 0.65,
                'description': '对称三角形，等待突破方向'
            }

        return None
    except Exception as e:
        logger.error(f"识别三角形失败: {e}")
        return None


def identify_flag(
    data: pd.DataFrame,
    lookback: int = 30
) -> Optional[Dict]:
    """识别旗形整理形态"""
    try:
        if len(data) < lookback:
            return None

        # 识别旗杆：快速大幅移动
        pole_data = data.iloc[-lookback:-10]
        pole_move = (pole_data['close'].iloc[-1] - pole_data['close'].iloc[0]) / pole_data['close'].iloc[0]

        if abs(pole_move) > 0.10:  # 旗杆涨跌幅>10%
            # 识别旗面：窄幅整理
            flag_data = data.iloc[-10:]
            flag_range = (flag_data['high'].max() - flag_data['low'].min()) / flag_data['low'].min()

            if flag_range < 0.05:  # 整理幅度<5%
                if pole_move > 0:  # 上升旗形
                    return {
                        'type': 'bull_flag',
                        'signal': 'buy_on_breakout',
                        'breakout_level': flag_data['high'].max(),
                        'target': data['close'].iloc[-1] + abs(pole_move * data['close'].iloc[-1]),
                        'confidence': 0.70,
                        'description': '上升旗形，看涨延续形态'
                    }
                else:  # 下降旗形
                    return {
                        'type': 'bear_flag',
                        'signal': 'sell_on_breakdown',
                        'breakdown_level': flag_data['low'].min(),
                        'target': data['close'].iloc[-1] - abs(pole_move * data['close'].iloc[-1]),
                        'confidence': 0.70,
                        'description': '下降旗形，看跌延续形态'
                    }

        return None
    except Exception as e:
        logger.error(f"识别旗形失败: {e}")
        return None
