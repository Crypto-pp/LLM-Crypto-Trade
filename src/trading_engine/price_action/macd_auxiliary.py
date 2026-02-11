"""
MACD辅助分析模块
提供MACD背离检测、趋势确认、动能转换分析
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

from src.utils.math_utils import smart_round
from ..indicators.trend import calculate_macd

logger = logging.getLogger(__name__)


def detect_macd_divergence(
    data: pd.DataFrame,
    lookback: int = 30
) -> Optional[Dict]:
    """
    MACD背离检测：价格创新高/低但MACD未同步

    看涨背离：价格创新低但MACD未创新低
    看跌背离：价格创新高但MACD未创新高

    Args:
        data: 价格数据
        lookback: 回看周期

    Returns:
        背离检测字典，未检测到返回 None
    """
    try:
        if len(data) < lookback + 26:
            logger.warning("数据长度不足，MACD需要至少26根预热K线")
            return None

        macd_data = calculate_macd(data)
        macd_line = macd_data['macd'].values

        recent = data.iloc[-lookback:]
        recent_macd = macd_line[-lookback:]
        closes = recent['close'].values

        # 将数据分为前半段和后半段
        half = lookback // 2
        first_half_close = closes[:half]
        second_half_close = closes[half:]
        first_half_macd = recent_macd[:half]
        second_half_macd = recent_macd[half:]

        # 看涨背离：价格创新低但MACD未创新低
        price_lower_low = second_half_close.min() < first_half_close.min()
        macd_higher_low = second_half_macd.min() > first_half_macd.min()

        if price_lower_low and macd_higher_low:
            confidence = 0.75
            return {
                "type": "macd_divergence",
                "divergence_type": "bullish",
                "price_low_1": smart_round(float(first_half_close.min())),
                "price_low_2": smart_round(float(second_half_close.min())),
                "macd_low_1": smart_round(float(first_half_macd.min())),
                "macd_low_2": smart_round(float(second_half_macd.min())),
                "confidence": confidence,
                "description": "看涨背离：价格创新低但MACD未创新低，"
                               "下跌动能减弱，可能反转向上"
            }

        # 看跌背离：价格创新高但MACD未创新高
        price_higher_high = second_half_close.max() > first_half_close.max()
        macd_lower_high = second_half_macd.max() < first_half_macd.max()

        if price_higher_high and macd_lower_high:
            confidence = 0.75
            return {
                "type": "macd_divergence",
                "divergence_type": "bearish",
                "price_high_1": smart_round(float(first_half_close.max())),
                "price_high_2": smart_round(float(second_half_close.max())),
                "macd_high_1": smart_round(float(first_half_macd.max())),
                "macd_high_2": smart_round(float(second_half_macd.max())),
                "confidence": confidence,
                "description": "看跌背离：价格创新高但MACD未创新高，"
                               "上涨动能减弱，可能反转向下"
            }

        return None

    except Exception as e:
        logger.error(f"检测MACD背离失败: {e}")
        return None


def confirm_trend_with_macd(data: pd.DataFrame) -> Optional[Dict]:
    """
    MACD趋势确认：零轴穿越确认趋势方向

    MACD线在零轴上方表示多头趋势，下方表示空头趋势，
    柱状图方向进一步确认趋势强度。

    Args:
        data: 价格数据

    Returns:
        趋势确认字典，数据不足返回 None
    """
    try:
        if len(data) < 30:
            logger.warning("数据长度不足，需要至少30根K线")
            return None

        macd_data = calculate_macd(data)
        macd_line = macd_data['macd'].values
        signal_line = macd_data['signal'].values
        histogram = macd_data['histogram'].values

        current_macd = macd_line[-1]
        current_signal = signal_line[-1]
        current_hist = histogram[-1]

        # 判断趋势方向
        if current_macd > 0:
            trend = "bullish"
        elif current_macd < 0:
            trend = "bearish"
        else:
            trend = "neutral"

        # 柱状图趋势（最近5根）
        recent_hist = histogram[-5:]
        if len(recent_hist) >= 2:
            hist_increasing = all(
                recent_hist[i] > recent_hist[i - 1]
                for i in range(1, len(recent_hist))
            )
            hist_decreasing = all(
                recent_hist[i] < recent_hist[i - 1]
                for i in range(1, len(recent_hist))
            )

            if hist_increasing:
                histogram_trend = "strengthening"
            elif hist_decreasing:
                histogram_trend = "weakening"
            else:
                histogram_trend = "mixed"
        else:
            histogram_trend = "insufficient_data"

        # MACD与信号线的关系
        macd_above_signal = current_macd > current_signal

        # 置信度
        confidence = 0.60
        if trend != "neutral":
            confidence += 0.10
        if (trend == "bullish" and macd_above_signal) or \
           (trend == "bearish" and not macd_above_signal):
            confidence += 0.10
        if histogram_trend == "strengthening" and trend == "bullish":
            confidence += 0.05
        elif histogram_trend == "weakening" and trend == "bearish":
            confidence += 0.05

        trend_cn = {"bullish": "多头", "bearish": "空头", "neutral": "中性"}

        return {
            "type": "macd_trend_confirmation",
            "trend": trend,
            "macd_value": smart_round(float(current_macd)),
            "signal_value": smart_round(float(current_signal)),
            "histogram_value": smart_round(float(current_hist)),
            "macd_above_signal": bool(macd_above_signal),
            "histogram_trend": histogram_trend,
            "confidence": round(confidence, 2),
            "description": f"MACD确认{trend_cn[trend]}趋势，"
                           f"柱状图{histogram_trend}，"
                           f"MACD{'高于' if macd_above_signal else '低于'}信号线"
        }

    except Exception as e:
        logger.error(f"MACD趋势确认失败: {e}")
        return None


def detect_macd_momentum_shift(
    data: pd.DataFrame,
    lookback: int = 20
) -> Optional[Dict]:
    """
    MACD动能转换：柱状图变化确认力量转换

    通过柱状图从正转负或从负转正来检测动能转换，
    柱状图连续缩小也预示动能即将转换。

    Args:
        data: 价格数据
        lookback: 回看周期

    Returns:
        动能转换字典，未检测到返回 None
    """
    try:
        if len(data) < lookback + 26:
            logger.warning("数据长度不足，MACD需要至少26根预热K线")
            return None

        macd_data = calculate_macd(data)
        histogram = macd_data['histogram'].values

        recent_hist = histogram[-lookback:]

        # 检测零轴穿越（柱状图符号变化）
        current = recent_hist[-1]
        previous = recent_hist[-2]

        zero_cross = False
        shift_type = None

        if previous <= 0 < current:
            zero_cross = True
            shift_type = "bearish_to_bullish"
        elif previous >= 0 > current:
            zero_cross = True
            shift_type = "bullish_to_bearish"

        if not zero_cross:
            # 检测柱状图连续缩小（动能衰减）
            if len(recent_hist) >= 5:
                last5 = recent_hist[-5:]
                abs_last5 = np.abs(last5)

                shrinking_count = sum(
                    1 for i in range(1, len(abs_last5))
                    if abs_last5[i] < abs_last5[i - 1]
                )

                if shrinking_count >= 3:
                    if current > 0:
                        shift_type = "bullish_weakening"
                    else:
                        shift_type = "bearish_weakening"
                else:
                    return None
            else:
                return None

        # 置信度
        if zero_cross:
            confidence = 0.75
        else:
            confidence = 0.60

        shift_cn = {
            "bearish_to_bullish": "空转多",
            "bullish_to_bearish": "多转空",
            "bullish_weakening": "多头动能衰减",
            "bearish_weakening": "空头动能衰减",
        }

        return {
            "type": "macd_momentum_shift",
            "shift_type": shift_type,
            "zero_cross": zero_cross,
            "current_histogram": smart_round(float(current)),
            "previous_histogram": smart_round(float(previous)),
            "confidence": confidence,
            "description": f"MACD动能转换：{shift_cn.get(shift_type, shift_type)}，"
                           f"柱状图{'穿越零轴' if zero_cross else '持续缩小'}"
        }

    except Exception as e:
        logger.error(f"检测MACD动能转换失败: {e}")
        return None
