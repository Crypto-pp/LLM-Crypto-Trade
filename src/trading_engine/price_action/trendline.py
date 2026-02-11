"""
趋势线识别模块
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging

from .market_structure import find_swing_highs_lows

logger = logging.getLogger(__name__)


def draw_trendline(
    data: pd.DataFrame,
    line_type: str = 'support',
    lookback: int = 50
) -> Optional[Dict]:
    """
    绘制趋势线

    Args:
        data: 价格数据
        line_type: 'support' 或 'resistance'
        lookback: 回看周期

    Returns:
        趋势线参数字典
    """
    try:
        swings = find_swing_highs_lows(data, lookback=5)
        if line_type == 'support':
            points = swings['swing_lows'][-lookback:]
        else:
            points = swings['swing_highs'][-lookback:]

        if len(points) < 2:
            return None

        # 计算趋势线斜率和截距
        x = np.array([p['index'] for p in points])
        y = np.array([p['price'] for p in points])

        slope, intercept = np.polyfit(x, y, 1)

        return {
            'slope': slope,
            'intercept': intercept,
            'touch_points': len(points),
            'strength': _calculate_trendline_strength(points, slope, intercept),
            'type': line_type
        }

    except Exception as e:
        logger.error(f"绘制趋势线失败: {e}")
        return None


def identify_channel(data: pd.DataFrame, lookback: int = 50) -> Optional[Dict]:
    """
    识别价格通道

    Returns:
        通道参数字典
    """
    try:
        support_line = draw_trendline(data, 'support', lookback)
        resistance_line = draw_trendline(data, 'resistance', lookback)

        if not support_line or not resistance_line:
            return None

        # 检查是否平行
        slope_diff = abs(support_line['slope'] - resistance_line['slope'])

        if slope_diff < 0.01:  # 斜率差异<1%
            return {
                'type': 'parallel_channel',
                'support': support_line,
                'resistance': resistance_line,
                'width': _calculate_channel_width(support_line, resistance_line, data),
                'confidence': 0.75,
                'trading_strategy': {
                    'buy': 'near_support_line',
                    'sell': 'near_resistance_line',
                    'stop_loss': 'outside_channel'
                }
            }

        return None

    except Exception as e:
        logger.error(f"识别通道失败: {e}")
        return None


def detect_trendline_break(
    data: pd.DataFrame,
    trendline: Dict,
    confirmation_bars: int = 2
) -> Optional[Dict]:
    """
    检测趋势线突破

    Args:
        data: 价格数据
        trendline: 趋势线参数
        confirmation_bars: 确认K线数量

    Returns:
        突破信号字典
    """
    try:
        recent_data = data.iloc[-confirmation_bars:]

        for i, (idx, row) in enumerate(recent_data.iterrows()):
            trendline_value = trendline['slope'] * len(data) + trendline['intercept']

            # 向上突破
            if row['close'] > trendline_value:
                volume_ratio = row['volume'] / data['volume'].mean()

                if volume_ratio > 1.5:
                    return {
                        'break_type': 'upside_break',
                        'signal': 'buy',
                        'confidence': 0.75,
                        'volume_confirmation': True,
                        'description': '向上突破趋势线，看涨信号'
                    }

            # 向下突破
            elif row['close'] < trendline_value:
                volume_ratio = row['volume'] / data['volume'].mean()

                if volume_ratio > 1.5:
                    return {
                        'break_type': 'downside_break',
                        'signal': 'sell',
                        'confidence': 0.75,
                        'volume_confirmation': True,
                        'description': '向下突破趋势线，看跌信号'
                    }

        return None

    except Exception as e:
        logger.error(f"检测趋势线突破失败: {e}")
        return None


# 辅助函数

def _calculate_trendline_strength(points: list, slope: float, intercept: float) -> str:
    """计算趋势线强度"""
    if len(points) >= 5:
        return 'very_strong'
    elif len(points) >= 3:
        return 'strong'
    else:
        return 'moderate'


def _calculate_channel_width(support: Dict, resistance: Dict, data: pd.DataFrame) -> float:
    """计算通道宽度"""
    current_idx = len(data) - 1
    support_value = support['slope'] * current_idx + support['intercept']
    resistance_value = resistance['slope'] * current_idx + resistance['intercept']

    return abs(resistance_value - support_value) / support_value * 100
