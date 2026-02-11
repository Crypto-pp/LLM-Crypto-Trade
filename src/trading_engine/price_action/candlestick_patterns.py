"""
K线形态识别模块
识别Pin Bar, Engulfing, Inside Bar, Outside Bar, Doji, Hammer等形态
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def identify_pin_bar(candle: pd.Series, min_ratio: float = 2.0) -> Optional[Dict]:
    """
    识别Pin Bar（长影线/锤子线/射击之星）

    Args:
        candle: 单根K线数据
        min_ratio: 影线与实体的最小比率

    Returns:
        识别结果字典，如果不是Pin Bar则返回None
    """
    try:
        body = abs(candle['close'] - candle['open'])
        upper_wick = candle['high'] - max(candle['open'], candle['close'])
        lower_wick = min(candle['open'], candle['close']) - candle['low']
        total_range = candle['high'] - candle['low']

        if total_range == 0:
            return None

        # 看涨Pin Bar（锤子线）
        if lower_wick > body * min_ratio and lower_wick / total_range > 0.6:
            if upper_wick < body * 0.5:
                strength = 'very_strong' if lower_wick / body >= 5 else 'strong'
                return {
                    'type': 'bullish_pin_bar',
                    'signal': 'buy',
                    'strength': strength,
                    'confidence': 0.85,
                    'description': '看涨Pin Bar，长下影线表示买方强力反击'
                }

        # 看跌Pin Bar（射击之星）
        if upper_wick > body * min_ratio and upper_wick / total_range > 0.6:
            if lower_wick < body * 0.5:
                strength = 'very_strong' if upper_wick / body >= 5 else 'strong'
                return {
                    'type': 'bearish_pin_bar',
                    'signal': 'sell',
                    'strength': strength,
                    'confidence': 0.85,
                    'description': '看跌Pin Bar，长上影线表示卖方强力打压'
                }

        return None
    except Exception as e:
        logger.error(f"识别Pin Bar失败: {e}")
        return None


def identify_engulfing(candle1: pd.Series, candle2: pd.Series) -> Optional[Dict]:
    """
    识别吞没形态

    Args:
        candle1: 第一根K线
        candle2: 第二根K线

    Returns:
        识别结果字典
    """
    try:
        body1_top = max(candle1['open'], candle1['close'])
        body1_bottom = min(candle1['open'], candle1['close'])
        body2_top = max(candle2['open'], candle2['close'])
        body2_bottom = min(candle2['open'], candle2['close'])

        # 看涨吞没
        if candle1['close'] < candle1['open'] and candle2['close'] > candle2['open']:
            if body2_bottom < body1_bottom and body2_top > body1_top:
                volume_increase = candle2['volume'] / candle1['volume'] if candle1['volume'] > 0 else 1
                strength = 'strong' if volume_increase > 1.5 else 'moderate'
                return {
                    'type': 'bullish_engulfing',
                    'signal': 'buy',
                    'strength': strength,
                    'confidence': 0.80,
                    'description': '看涨吞没，阳线完全吞没阴线'
                }

        # 看跌吞没
        if candle1['close'] > candle1['open'] and candle2['close'] < candle2['open']:
            if body2_top > body1_top and body2_bottom < body1_bottom:
                volume_increase = candle2['volume'] / candle1['volume'] if candle1['volume'] > 0 else 1
                strength = 'strong' if volume_increase > 1.5 else 'moderate'
                return {
                    'type': 'bearish_engulfing',
                    'signal': 'sell',
                    'strength': strength,
                    'confidence': 0.80,
                    'description': '看跌吞没，阴线完全吞没阳线'
                }

        return None
    except Exception as e:
        logger.error(f"识别吞没形态失败: {e}")
        return None


def identify_inside_bar(mother_bar: pd.Series, inside_bar: pd.Series) -> Optional[Dict]:
    """
    识别内包线（Inside Bar）
    """
    try:
        if (inside_bar['high'] <= mother_bar['high'] and
            inside_bar['low'] >= mother_bar['low']):

            return {
                'type': 'inside_bar',
                'signal': 'breakout_pending',
                'mother_bar_range': mother_bar['high'] - mother_bar['low'],
                'confidence': 0.70,
                'description': '内包线，市场盘整，等待突破方向',
                'trading_plan': {
                    'buy_trigger': mother_bar['high'],
                    'sell_trigger': mother_bar['low'],
                    'stop_loss': '对侧边界'
                }
            }

        return None
    except Exception as e:
        logger.error(f"识别内包线失败: {e}")
        return None


def identify_outside_bar(inside_bar: pd.Series, outside_bar: pd.Series) -> Optional[Dict]:
    """
    识别外包线（Outside Bar）
    """
    try:
        if (outside_bar['high'] > inside_bar['high'] and
            outside_bar['low'] < inside_bar['low']):

            if outside_bar['close'] > outside_bar['open']:
                signal = 'buy'
                description = '看涨外包，买方控制市场'
            else:
                signal = 'sell'
                description = '看跌外包，卖方控制市场'

            return {
                'type': 'outside_bar',
                'signal': signal,
                'strength': 'strong',
                'confidence': 0.75,
                'description': description
            }

        return None
    except Exception as e:
        logger.error(f"识别外包线失败: {e}")
        return None


def identify_doji(candle: pd.Series, body_ratio: float = 0.1) -> Optional[Dict]:
    """
    识别十字星（Doji）
    """
    try:
        body = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']

        if total_range == 0:
            return None

        # 实体很小，占总范围的比例小于阈值
        if body / total_range < body_ratio:
            return {
                'type': 'doji',
                'signal': 'reversal_possible',
                'strength': 'moderate',
                'confidence': 0.65,
                'description': '十字星，市场犹豫不决，可能反转'
            }

        return None
    except Exception as e:
        logger.error(f"识别十字星失败: {e}")
        return None


def identify_hammer(candle: pd.Series, trend: str = 'down') -> Optional[Dict]:
    """
    识别锤子线/上吊线

    Args:
        candle: K线数据
        trend: 当前趋势 ('up' 或 'down')
    """
    try:
        body = abs(candle['close'] - candle['open'])
        lower_wick = min(candle['open'], candle['close']) - candle['low']
        upper_wick = candle['high'] - max(candle['open'], candle['close'])

        # 下影线至少是实体的2倍，上影线很短
        if lower_wick > body * 2 and upper_wick < body * 0.3:
            if trend == 'down':
                return {
                    'type': 'hammer',
                    'signal': 'buy',
                    'strength': 'strong',
                    'confidence': 0.80,
                    'description': '锤子线，下跌趋势中的看涨反转信号'
                }
            else:
                return {
                    'type': 'hanging_man',
                    'signal': 'sell',
                    'strength': 'moderate',
                    'confidence': 0.70,
                    'description': '上吊线，上涨趋势中的看跌信号'
                }

        return None
    except Exception as e:
        logger.error(f"识别锤子线失败: {e}")
        return None


def identify_trend_bar(candle: pd.Series, threshold: float = 0.6) -> Optional[Dict]:
    """
    识别趋势K线（大实体、短影线）

    趋势K线表示一方力量占据绝对优势，
    实体占总范围比例超过阈值即判定为趋势K线。

    Args:
        candle: 单根K线数据
        threshold: 实体占比阈值，默认0.6

    Returns:
        识别结果字典，非趋势K线返回 None
    """
    try:
        body = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']

        if total_range == 0:
            return None

        body_ratio = body / total_range
        if body_ratio < threshold:
            return None

        is_bullish = candle['close'] > candle['open']
        bar_type = 'bullish_trend_bar' if is_bullish else 'bearish_trend_bar'

        # 强度评估：实体占比越高越强
        if body_ratio >= 0.85:
            strength = 'very_strong'
            confidence = 0.90
        elif body_ratio >= 0.75:
            strength = 'strong'
            confidence = 0.80
        else:
            strength = 'moderate'
            confidence = 0.70

        direction = '看涨' if is_bullish else '看跌'

        return {
            'type': bar_type,
            'body_ratio': round(body_ratio, 3),
            'strength': strength,
            'confidence': confidence,
            'description': f'{direction}趋势K线，实体占比{body_ratio*100:.1f}%，{direction}力量强劲'
        }

    except Exception as e:
        logger.error(f"识别趋势K线失败: {e}")
        return None


def detect_barbed_wire(data: pd.DataFrame, lookback: int = 6) -> Optional[Dict]:
    """
    检测铁丝网形态（连续小实体K线互相重叠）

    铁丝网表示市场极度犹豫，多空双方势均力敌，
    通常出现在盘整区间，不适合交易。

    Args:
        data: 价格数据
        lookback: 检查的K线数量，默认6

    Returns:
        检测结果字典，未检测到返回 None
    """
    try:
        if len(data) < lookback:
            logger.warning(f"数据长度不足，需要至少 {lookback} 根K线")
            return None

        recent = data.iloc[-lookback:]
        bodies = abs(recent['close'] - recent['open']).values
        ranges = (recent['high'] - recent['low']).values

        # 避免除零
        valid_ranges = ranges[ranges > 0]
        if len(valid_ranges) < lookback * 0.5:
            return None

        # 计算实体占比
        body_ratios = np.where(ranges > 0, bodies / ranges, 0)
        small_body_count = np.sum(body_ratios < 0.4)

        # 至少2/3的K线是小实体
        if small_body_count < lookback * 0.66:
            return None

        # 检查高低点重叠度：相邻K线的重叠区间
        highs = recent['high'].values
        lows = recent['low'].values
        overlap_count = 0

        for i in range(1, len(highs)):
            overlap = min(highs[i], highs[i-1]) - max(lows[i], lows[i-1])
            range_avg = (ranges[i] + ranges[i-1]) / 2
            if range_avg > 0 and overlap > 0 and overlap / range_avg > 0.3:
                overlap_count += 1

        overlap_ratio = overlap_count / (lookback - 1)
        if overlap_ratio < 0.5:
            return None

        # 置信度基于小实体比例和重叠度
        confidence = min(0.90, 0.50 + small_body_count / lookback * 0.2 + overlap_ratio * 0.2)

        return {
            'type': 'barbed_wire',
            'bar_count': lookback,
            'small_body_count': int(small_body_count),
            'overlap_ratio': round(overlap_ratio, 3),
            'confidence': round(confidence, 2),
            'description': f'铁丝网形态：{lookback}根K线中{int(small_body_count)}根小实体，'
                           f'重叠度{overlap_ratio*100:.0f}%，市场犹豫不决，不宜交易'
        }

    except Exception as e:
        logger.error(f"检测铁丝网形态失败: {e}")
        return None
