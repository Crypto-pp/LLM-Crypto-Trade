"""
高级反转形态识别模块
实现反转条件检查、三推楔形、高潮反转、末端旗形、反转概率评估
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


def check_reversal_conditions(
    data: pd.DataFrame,
    current_trend: str = "bullish",
    lookback: int = 20
) -> Optional[Dict]:
    """
    检查反转条件是否满足

    综合评估趋势疲劳、动能衰减、成交量异常等信号，
    判断当前趋势是否具备反转条件。

    Args:
        data: 价格数据
        current_trend: 当前趋势方向
        lookback: 回看周期

    Returns:
        反转条件评估字典
    """
    try:
        if len(data) < lookback:
            logger.warning(
                f"数据长度不足，需要至少 {lookback} 根K线"
            )
            return None

        recent = data.iloc[-lookback:]
        closes = recent["close"].values
        volumes = recent["volume"].values

        conditions_met = []
        total_score = 0

        # 条件1：趋势疲劳（动能递减）
        momentum_score = _check_momentum_fatigue(
            closes, current_trend
        )
        if momentum_score > 50:
            conditions_met.append("momentum_fatigue")
        total_score += momentum_score * 0.30

        # 条件2：成交量背离
        vol_score = _check_volume_divergence(
            closes, volumes, current_trend
        )
        if vol_score > 50:
            conditions_met.append("volume_divergence")
        total_score += vol_score * 0.25

        # 条件3：极端K线形态
        candle_score = _check_extreme_candles(
            recent, current_trend
        )
        if candle_score > 50:
            conditions_met.append("extreme_candles")
        total_score += candle_score * 0.25

        # 条件4：价格结构变化
        struct_score = _check_structure_shift(
            closes, current_trend
        )
        if struct_score > 50:
            conditions_met.append("structure_shift")
        total_score += struct_score * 0.20

        # 综合判定
        if total_score >= 70:
            readiness = "high"
            description = "反转条件充分，高概率反转"
        elif total_score >= 50:
            readiness = "moderate"
            description = "部分反转条件满足，需观察确认"
        else:
            readiness = "low"
            description = "反转条件不足，趋势可能延续"

        return {
            "type": "reversal_conditions",
            "current_trend": current_trend,
            "readiness": readiness,
            "total_score": round(total_score, 1),
            "conditions_met": conditions_met,
            "conditions_count": len(conditions_met),
            "confidence": round(total_score / 100, 2),
            "description": description
        }

    except Exception as e:
        logger.error(f"检查反转条件失败: {e}")
        return None


def identify_three_push_wedge(
    data: pd.DataFrame,
    lookback: int = 30
) -> Optional[Dict]:
    """
    识别三推楔形反转形态

    价格连续三次推高（或推低），每次推进幅度递减，
    形成楔形收敛结构，预示趋势即将反转。

    Args:
        data: 价格数据
        lookback: 回看周期

    Returns:
        三推楔形信号字典
    """
    try:
        if len(data) < lookback:
            return None

        recent = data.iloc[-lookback:]
        highs = recent["high"].values
        lows = recent["low"].values

        # 检测三推向上（看跌反转）
        result = _detect_three_pushes(highs, lows, "up")
        if result:
            pushes = result["pushes"]
            return {
                "type": "three_push_wedge",
                "direction": "bearish_reversal",
                "push_1": round(pushes[0], 2),
                "push_2": round(pushes[1], 2),
                "push_3": round(pushes[2], 2),
                "signal": "sell",
                "confidence": result["confidence"],
                "description": "三推向上楔形，动能递减，看跌反转"
            }

        # 检测三推向下（看涨反转）
        result = _detect_three_pushes(highs, lows, "down")
        if result:
            pushes = result["pushes"]
            return {
                "type": "three_push_wedge",
                "direction": "bullish_reversal",
                "push_1": round(pushes[0], 2),
                "push_2": round(pushes[1], 2),
                "push_3": round(pushes[2], 2),
                "signal": "buy",
                "confidence": result["confidence"],
                "description": "三推向下楔形，动能递减，看涨反转"
            }

        return None

    except Exception as e:
        logger.error(f"识别三推楔形失败: {e}")
        return None


def identify_climax_reversal(
    data: pd.DataFrame,
    lookback: int = 20
) -> Optional[Dict]:
    """
    识别高潮反转形态

    趋势末端出现极端放量和大幅波动，
    表示最后一批追随者入场，随后趋势反转。

    Args:
        data: 价格数据
        lookback: 回看周期

    Returns:
        高潮反转信号字典
    """
    try:
        if len(data) < lookback:
            return None

        recent = data.iloc[-lookback:]
        closes = recent["close"].values
        volumes = recent["volume"].values
        highs = recent["high"].values
        lows = recent["low"].values

        # 计算最近K线的波动幅度
        last_range = highs[-1] - lows[-1]
        avg_range = np.mean(highs - lows)

        # 计算成交量异常
        last_vol = volumes[-1]
        avg_vol = volumes[:-1].mean()

        if avg_range == 0 or avg_vol == 0:
            return None

        range_ratio = last_range / avg_range
        vol_ratio = last_vol / avg_vol

        # 高潮条件：波动幅度和成交量同时异常放大
        if range_ratio < 2.0 or vol_ratio < 2.0:
            return None

        # 判断方向
        if closes[-1] > closes[-2]:
            direction = "bullish_climax"
            signal = "sell"
            desc = "看涨高潮，极端放量上涨后可能反转下跌"
        else:
            direction = "bearish_climax"
            signal = "buy"
            desc = "看跌高潮，极端放量下跌后可能反转上涨"

        confidence = min(
            0.60 + (range_ratio - 2) * 0.05 + (vol_ratio - 2) * 0.05,
            0.90
        )

        return {
            "type": "climax_reversal",
            "direction": direction,
            "range_ratio": round(range_ratio, 2),
            "volume_ratio": round(vol_ratio, 2),
            "signal": signal,
            "confidence": round(confidence, 2),
            "description": desc
        }

    except Exception as e:
        logger.error(f"识别高潮反转失败: {e}")
        return None


def identify_ending_flag(
    data: pd.DataFrame,
    lookback: int = 25
) -> Optional[Dict]:
    """
    识别末端旗形（趋势末端的旗形整理）

    趋势末端出现的旗形整理，与正常旗形不同，
    突破方向往往与原趋势相反，形成反转信号。

    Args:
        data: 价格数据
        lookback: 回看周期

    Returns:
        末端旗形信号字典
    """
    try:
        if len(data) < lookback:
            return None

        recent = data.iloc[-lookback:]
        closes = recent["close"].values
        highs = recent["high"].values
        lows = recent["low"].values

        # 判断前半段趋势方向
        mid = lookback // 2
        first_half = closes[:mid]
        second_half = closes[mid:]

        trend_up = first_half[-1] > first_half[0]
        trend_down = first_half[-1] < first_half[0]

        if not (trend_up or trend_down):
            return None

        # 后半段是否形成旗形整理（区间收窄）
        second_range = highs[mid:].max() - lows[mid:].min()
        first_range = highs[:mid].max() - lows[:mid].min()

        if first_range == 0:
            return None

        narrowing = second_range / first_range

        # 旗形条件：后半段区间明显收窄
        if narrowing > 0.5:
            return None

        if trend_up:
            signal = "sell"
            direction = "bearish_ending_flag"
            desc = "上升趋势末端旗形，可能向下突破反转"
        else:
            signal = "buy"
            direction = "bullish_ending_flag"
            desc = "下降趋势末端旗形，可能向上突破反转"

        confidence = round(0.65 + (0.5 - narrowing) * 0.3, 2)

        return {
            "type": "ending_flag",
            "direction": direction,
            "narrowing_ratio": round(narrowing, 2),
            "signal": signal,
            "confidence": min(confidence, 0.85),
            "description": desc
        }

    except Exception as e:
        logger.error(f"识别末端旗形失败: {e}")
        return None


def assess_reversal_probability(
    data: pd.DataFrame,
    current_trend: str = "bullish",
    lookback: int = 30
) -> Optional[Dict]:
    """
    综合评估反转概率

    汇总多种反转信号，给出综合反转概率评分。

    Args:
        data: 价格数据
        current_trend: 当前趋势方向
        lookback: 回看周期

    Returns:
        反转概率评估字典
    """
    try:
        if len(data) < lookback:
            return None

        signals_found = []

        # 检查反转条件
        conditions = check_reversal_conditions(
            data, current_trend, lookback
        )
        if conditions and conditions["readiness"] != "low":
            signals_found.append({
                "signal": "reversal_conditions",
                "score": conditions["total_score"]
            })

        # 检查三推楔形
        wedge = identify_three_push_wedge(data, lookback)
        if wedge:
            signals_found.append({
                "signal": "three_push_wedge",
                "score": wedge["confidence"] * 100
            })

        # 检查高潮反转
        climax = identify_climax_reversal(data, lookback)
        if climax:
            signals_found.append({
                "signal": "climax_reversal",
                "score": climax["confidence"] * 100
            })

        # 检查末端旗形
        flag = identify_ending_flag(data, lookback)
        if flag:
            signals_found.append({
                "signal": "ending_flag",
                "score": flag["confidence"] * 100
            })

        if not signals_found:
            return {
                "type": "reversal_probability",
                "probability": 0.15,
                "signals_count": 0,
                "description": "未检测到反转信号，趋势可能延续"
            }

        avg_score = np.mean([s["score"] for s in signals_found])
        count_bonus = min(len(signals_found) * 5, 15)
        probability = min((avg_score + count_bonus) / 100, 0.95)

        return {
            "type": "reversal_probability",
            "current_trend": current_trend,
            "probability": round(probability, 2),
            "signals_count": len(signals_found),
            "signals": signals_found,
            "confidence": round(probability, 2),
            "description": f"反转概率{probability*100:.0f}%，"
                           f"检测到{len(signals_found)}个反转信号"
        }

    except Exception as e:
        logger.error(f"评估反转概率失败: {e}")
        return None


# ========== 私有辅助函数 ==========


def _check_momentum_fatigue(
    closes: np.ndarray,
    current_trend: str
) -> float:
    """检测动能疲劳（0-100分）"""
    if len(closes) < 6:
        return 30.0

    # 将数据分为三段，比较每段的涨跌幅
    third = len(closes) // 3
    seg1 = closes[third] - closes[0]
    seg2 = closes[2 * third] - closes[third]
    seg3 = closes[-1] - closes[2 * third]

    if current_trend == "bullish":
        # 上升趋势中，涨幅递减为疲劳信号
        if seg1 > 0 and seg2 > 0 and seg3 > 0:
            if seg3 < seg2 < seg1:
                return 85.0
            elif seg3 < seg1:
                return 65.0
        elif seg3 <= 0 and seg1 > 0:
            return 90.0
    else:
        # 下降趋势中，跌幅递减为疲劳信号
        if seg1 < 0 and seg2 < 0 and seg3 < 0:
            if seg3 > seg2 > seg1:
                return 85.0
            elif seg3 > seg1:
                return 65.0
        elif seg3 >= 0 and seg1 < 0:
            return 90.0

    return 30.0


def _check_volume_divergence(
    closes: np.ndarray,
    volumes: np.ndarray,
    current_trend: str
) -> float:
    """检测成交量背离（0-100分）"""
    if len(closes) < 6:
        return 30.0

    mid = len(closes) // 2
    first_vol = volumes[:mid].mean()
    second_vol = volumes[mid:].mean()

    if first_vol == 0:
        return 30.0

    vol_change = (second_vol - first_vol) / first_vol

    if current_trend == "bullish":
        price_rising = closes[-1] > closes[0]
        vol_declining = vol_change < -0.2
        if price_rising and vol_declining:
            return 80.0
        elif price_rising and vol_change < 0:
            return 55.0
    else:
        price_falling = closes[-1] < closes[0]
        vol_declining = vol_change < -0.2
        if price_falling and vol_declining:
            return 80.0
        elif price_falling and vol_change < 0:
            return 55.0

    return 25.0


def _check_extreme_candles(
    recent: pd.DataFrame,
    current_trend: str
) -> float:
    """检测极端K线形态（0-100分）"""
    try:
        last = recent.iloc[-1]
        body = abs(last["close"] - last["open"])
        total_range = last["high"] - last["low"]

        if total_range == 0:
            return 20.0

        body_ratio = body / total_range
        upper_wick = last["high"] - max(last["open"], last["close"])
        lower_wick = min(last["open"], last["close"]) - last["low"]

        # 长影线反转信号
        if current_trend == "bullish":
            if upper_wick > body * 2:
                return 80.0
        else:
            if lower_wick > body * 2:
                return 80.0

        # 十字星
        if body_ratio < 0.1:
            return 60.0

        return 20.0
    except Exception:
        return 20.0


def _check_structure_shift(
    closes: np.ndarray,
    current_trend: str
) -> float:
    """检测价格结构变化（0-100分）"""
    if len(closes) < 10:
        return 25.0

    # 找最近的摆动高低点
    mid = len(closes) // 2

    if current_trend == "bullish":
        # 上升趋势中，检测是否出现更低的高点
        first_high = max(closes[:mid])
        second_high = max(closes[mid:])
        if second_high < first_high:
            return 75.0
    else:
        # 下降趋势中，检测是否出现更高的低点
        first_low = min(closes[:mid])
        second_low = min(closes[mid:])
        if second_low > first_low:
            return 75.0

    return 25.0


def _detect_three_pushes(
    highs: np.ndarray,
    lows: np.ndarray,
    direction: str
) -> Optional[Dict]:
    """检测三推形态"""
    if len(highs) < 10:
        return None

    # 将数据分为三段
    third = len(highs) // 3
    seg1 = highs[:third] if direction == "up" else lows[:third]
    seg2 = highs[third:2*third] if direction == "up" else lows[third:2*third]
    seg3 = highs[2*third:] if direction == "up" else lows[2*third:]

    if direction == "up":
        p1 = float(seg1.max())
        p2 = float(seg2.max())
        p3 = float(seg3.max())

        # 三次推高，但幅度递减
        if p3 > p2 > p1:
            push1 = p2 - p1
            push2 = p3 - p2
            if push2 < push1:
                confidence = round(
                    0.65 + (1 - push2 / push1) * 0.2, 2
                )
                return {
                    "pushes": [p1, p2, p3],
                    "confidence": min(confidence, 0.88)
                }
    else:
        p1 = float(seg1.min())
        p2 = float(seg2.min())
        p3 = float(seg3.min())

        # 三次推低，但幅度递减
        if p3 < p2 < p1:
            push1 = p1 - p2
            push2 = p2 - p3
            if push2 < push1:
                confidence = round(
                    0.65 + (1 - push2 / push1) * 0.2, 2
                )
                return {
                    "pushes": [p1, p2, p3],
                    "confidence": min(confidence, 0.88)
                }

    return None
