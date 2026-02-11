"""
交易区间分析模块
识别交易区间、评估区间位置、检测区间突破
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

from src.utils.math_utils import smart_round

logger = logging.getLogger(__name__)


def identify_trading_range(
    data: pd.DataFrame,
    lookback: int = 50
) -> Optional[Dict]:
    """
    交易区间识别：价格在上下边界间反复运动

    通过统计价格触及上下边界的次数来确认区间，
    至少2次触及上边界和2次触及下边界才判定为有效区间。

    Args:
        data: 价格数据
        lookback: 回看周期

    Returns:
        交易区间字典，未检测到返回 None
    """
    try:
        if len(data) < lookback:
            logger.warning(f"数据长度不足，需要至少 {lookback} 根K线")
            return None

        recent = data.iloc[-lookback:]
        highs = recent['high'].values
        lows = recent['low'].values
        closes = recent['close'].values

        # 计算区间边界（使用百分位数避免极端值干扰）
        upper_bound = float(np.percentile(highs, 90))
        lower_bound = float(np.percentile(lows, 10))
        range_width = upper_bound - lower_bound

        if range_width <= 0:
            return None

        # 定义触及边界的容差（区间宽度的10%）
        tolerance = range_width * 0.10

        # 统计触及上下边界的次数
        upper_touches = 0
        lower_touches = 0

        for i in range(len(highs)):
            if highs[i] >= upper_bound - tolerance:
                upper_touches += 1
            if lows[i] <= lower_bound + tolerance:
                lower_touches += 1

        # 至少各2次触及才确认为交易区间
        if upper_touches < 2 or lower_touches < 2:
            return None

        # 计算区间宽度百分比
        mid_price = (upper_bound + lower_bound) / 2
        width_pct = range_width / mid_price * 100

        # 置信度基于触及次数
        total_touches = upper_touches + lower_touches
        confidence = min(0.90, 0.55 + total_touches * 0.03)

        return {
            "type": "trading_range",
            "upper_bound": smart_round(upper_bound),
            "lower_bound": smart_round(lower_bound),
            "width": smart_round(range_width),
            "width_pct": round(width_pct, 2),
            "upper_touches": upper_touches,
            "lower_touches": lower_touches,
            "total_touches": total_touches,
            "confidence": round(confidence, 2),
            "description": f"交易区间：{smart_round(lower_bound)}-{smart_round(upper_bound)}，"
                           f"宽度{width_pct:.1f}%，"
                           f"上边界触及{upper_touches}次，下边界触及{lower_touches}次"
        }

    except Exception as e:
        logger.error(f"识别交易区间失败: {e}")
        return None


def assess_range_position(
    data: pd.DataFrame,
    upper: float,
    lower: float
) -> Optional[Dict]:
    """
    区间位置评估：当前价格在区间中的位置

    Args:
        data: 价格数据
        upper: 区间上边界
        lower: 区间下边界

    Returns:
        区间位置评估字典
    """
    try:
        if upper <= lower:
            logger.warning("上边界必须大于下边界")
            return None

        current_price = float(data['close'].iloc[-1])
        range_width = upper - lower

        # 计算相对位置（0=下边界，1=上边界）
        relative_pos = (current_price - lower) / range_width
        relative_pos = max(0.0, min(relative_pos, 1.0))

        # 判断位置区域
        if relative_pos >= 0.75:
            position = "upper"
            bias = "bearish"
            description = "价格处于区间上部，偏向看跌"
        elif relative_pos <= 0.25:
            position = "lower"
            bias = "bullish"
            description = "价格处于区间下部，偏向看涨"
        else:
            position = "middle"
            bias = "neutral"
            description = "价格处于区间中部，方向不明"

        confidence = 0.70 if position == "middle" else 0.80

        return {
            "type": "range_position",
            "current_price": smart_round(current_price),
            "upper": smart_round(upper),
            "lower": smart_round(lower),
            "relative_position": round(relative_pos, 3),
            "position": position,
            "bias": bias,
            "confidence": confidence,
            "description": description
        }

    except Exception as e:
        logger.error(f"评估区间位置失败: {e}")
        return None


def detect_range_breakout(
    data: pd.DataFrame,
    upper: float,
    lower: float,
    lookback: int = 10
) -> Optional[Dict]:
    """
    区间突破检测：价格是否有效突破区间边界

    通过收盘价突破、成交量放大、突破幅度来判断突破有效性。

    Args:
        data: 价格数据
        upper: 区间上边界
        lower: 区间下边界
        lookback: 回看周期

    Returns:
        区间突破字典，未检测到返回 None
    """
    try:
        if upper <= lower:
            logger.warning("上边界必须大于下边界")
            return None

        if len(data) < lookback:
            logger.warning(f"数据长度不足，需要至少 {lookback} 根K线")
            return None

        current_close = float(data['close'].iloc[-1])
        current_volume = float(data['volume'].iloc[-1])
        avg_volume = float(data['volume'].iloc[-lookback:].mean())
        range_width = upper - lower

        direction = None
        breakout_distance = 0.0

        if current_close > upper:
            direction = "bullish"
            breakout_distance = current_close - upper
        elif current_close < lower:
            direction = "bearish"
            breakout_distance = lower - current_close

        if direction is None:
            return None

        # 突破幅度占区间宽度的比例
        breakout_pct = breakout_distance / range_width * 100 if range_width > 0 else 0

        # 成交量确认
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        volume_confirmed = volume_ratio > 1.3

        # 判断突破是否真实
        is_genuine = breakout_pct > 1.0 and volume_confirmed

        # 置信度
        confidence = 0.50
        if breakout_pct > 2.0:
            confidence += 0.15
        if volume_confirmed:
            confidence += 0.15
        if breakout_pct > 5.0:
            confidence += 0.10
        confidence = min(0.90, confidence)

        direction_cn = "向上" if direction == "bullish" else "向下"

        return {
            "type": "range_breakout",
            "direction": direction,
            "breakout_distance": smart_round(breakout_distance),
            "breakout_pct": round(breakout_pct, 2),
            "volume_ratio": round(volume_ratio, 2),
            "volume_confirmed": volume_confirmed,
            "is_genuine": is_genuine,
            "confidence": round(confidence, 2),
            "description": f"{direction_cn}突破区间，"
                           f"突破幅度{breakout_pct:.1f}%，"
                           f"量比{volume_ratio:.1f}，"
                           f"{'有效突破' if is_genuine else '可能假突破'}"
        }

    except Exception as e:
        logger.error(f"检测区间突破失败: {e}")
        return None
