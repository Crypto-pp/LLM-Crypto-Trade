"""
多空力量分析模块
实现多空力量计算、力量对比、趋势强度评估、
多空转换检测、综合力量评分
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import logging
from src.utils.math_utils import smart_round

logger = logging.getLogger(__name__)


def calculate_bull_bear_power(
    data: pd.DataFrame,
    period: int = 13
) -> Optional[Dict]:
    """
    计算多空力量指标

    基于K线实体、影线和成交量综合评估多空双方力量。
    多头力量 = 最高价 - EMA；空头力量 = 最低价 - EMA。

    Args:
        data: 价格数据，需包含 high/low/close 列
        period: EMA周期

    Returns:
        多空力量指标字典
    """
    try:
        if len(data) < period:
            logger.warning(
                f"数据长度不足，需要至少 {period} 根K线"
            )
            return None

        closes = data["close"].values
        highs = data["high"].values
        lows = data["low"].values

        # 计算EMA
        ema = _calc_ema(closes, period)
        if ema is None:
            return None

        current_ema = ema[-1]

        # 多头力量：最高价与EMA的距离
        bull_power = float(highs[-1] - current_ema)
        # 空头力量：最低价与EMA的距离
        bear_power = float(lows[-1] - current_ema)

        # 净力量
        net_power = bull_power + bear_power

        # 判断主导方
        if bull_power > 0 and bear_power > 0:
            dominant = "strong_bull"
            desc = "强势多头，价格完全在EMA上方"
        elif bull_power > 0 and bear_power < 0:
            if abs(bull_power) > abs(bear_power):
                dominant = "bull"
                desc = "多头主导，但空头有抵抗"
            else:
                dominant = "bear"
                desc = "空头主导，但多头有抵抗"
        elif bull_power < 0 and bear_power < 0:
            dominant = "strong_bear"
            desc = "强势空头，价格完全在EMA下方"
        else:
            dominant = "neutral"
            desc = "多空均衡"

        return {
            "type": "bull_bear_power",
            "bull_power": smart_round(bull_power),
            "bear_power": smart_round(bear_power),
            "net_power": smart_round(net_power),
            "ema": smart_round(current_ema),
            "dominant": dominant,
            "confidence": 0.70,
            "description": desc
        }

    except Exception as e:
        logger.error(f"计算多空力量失败: {e}")
        return None


def compare_bull_bear_strength(
    data: pd.DataFrame,
    lookback: int = 20
) -> Optional[Dict]:
    """
    对比多空力量强度

    通过分析K线实体方向、影线比例和成交量分布，
    量化多空双方的相对强度。

    Args:
        data: 价格数据
        lookback: 回看周期

    Returns:
        多空力量对比字典
    """
    try:
        if len(data) < lookback:
            logger.warning(
                f"数据长度不足，需要至少 {lookback} 根K线"
            )
            return None

        recent = data.iloc[-lookback:]

        # 统计阳线和阴线
        bull_candles = 0
        bear_candles = 0
        bull_body_sum = 0.0
        bear_body_sum = 0.0

        for _, row in recent.iterrows():
            body = row["close"] - row["open"]
            if body > 0:
                bull_candles += 1
                bull_body_sum += body
            elif body < 0:
                bear_candles += 1
                bear_body_sum += abs(body)

        total = bull_candles + bear_candles
        if total == 0:
            return None

        # 多头占比
        bull_ratio = bull_candles / total
        # 力量对比（实体大小）
        total_body = bull_body_sum + bear_body_sum
        bull_strength = (
            bull_body_sum / total_body if total_body > 0 else 0.5
        )

        # 综合评分（-100到+100）
        score = (bull_strength - 0.5) * 200

        if score > 30:
            bias = "bullish"
            desc = f"多头占优，力量评分{score:.0f}"
        elif score < -30:
            bias = "bearish"
            desc = f"空头占优，力量评分{score:.0f}"
        else:
            bias = "neutral"
            desc = f"多空均衡，力量评分{score:.0f}"

        return {
            "type": "bull_bear_comparison",
            "bull_candles": bull_candles,
            "bear_candles": bear_candles,
            "bull_ratio": round(bull_ratio, 2),
            "bull_strength": round(bull_strength, 2),
            "score": round(score, 1),
            "bias": bias,
            "confidence": 0.70,
            "description": desc
        }

    except Exception as e:
        logger.error(f"对比多空力量失败: {e}")
        return None


def assess_trend_strength(
    data: pd.DataFrame,
    period: int = 20
) -> Optional[Dict]:
    """
    评估趋势强度

    通过多空力量的持续性、价格与EMA的偏离度、
    连续同向K线数量等维度综合评估当前趋势的强弱。

    Args:
        data: 价格数据，需包含 high/low/close/volume 列
        period: 评估周期

    Returns:
        趋势强度评估字典
    """
    try:
        if len(data) < period:
            logger.warning(
                f"数据长度不足，需要至少 {period} 根K线"
            )
            return None

        recent = data.iloc[-period:]
        closes = recent["close"].values
        highs = recent["high"].values
        lows = recent["low"].values

        ema = _calc_ema(closes, period)
        if ema is None:
            return None

        current_ema = ema[-1]
        current_price = closes[-1]

        # 维度1：价格与EMA的偏离度
        deviation = (current_price - current_ema) / current_ema * 100
        deviation_score = min(abs(deviation) * 10, 100)

        # 维度2：连续同向K线数量
        consecutive = _count_consecutive_direction(closes)
        consecutive_score = min(consecutive * 15, 100)

        # 维度3：高低点趋势（HH/HL 或 LH/LL）
        structure_score = _assess_hl_structure(highs, lows)

        # 维度4：价格斜率
        slope = (closes[-1] - closes[0]) / closes[0] * 100
        slope_score = min(abs(slope) * 5, 100)

        # 综合评分
        total = (
            deviation_score * 0.25 +
            consecutive_score * 0.25 +
            structure_score * 0.30 +
            slope_score * 0.20
        )

        # 判断趋势方向和强度
        if deviation > 0:
            direction = "bullish"
        elif deviation < 0:
            direction = "bearish"
        else:
            direction = "neutral"

        if total >= 75:
            strength = "very_strong"
            desc = f"极强{direction}趋势，强度评分{total:.0f}"
        elif total >= 55:
            strength = "strong"
            desc = f"强{direction}趋势，强度评分{total:.0f}"
        elif total >= 35:
            strength = "moderate"
            desc = f"中等{direction}趋势，强度评分{total:.0f}"
        else:
            strength = "weak"
            desc = f"弱趋势或无趋势，强度评分{total:.0f}"

        return {
            "type": "trend_strength",
            "direction": direction,
            "strength": strength,
            "total_score": round(total, 1),
            "deviation_pct": round(deviation, 2),
            "consecutive_candles": consecutive,
            "structure_score": round(structure_score, 1),
            "confidence": round(total / 100, 2),
            "description": desc
        }

    except Exception as e:
        logger.error(f"评估趋势强度失败: {e}")
        return None


def detect_bull_bear_transition(
    data: pd.DataFrame,
    short_period: int = 7,
    long_period: int = 21
) -> Optional[Dict]:
    """
    检测多空转换信号

    通过短期与长期多空力量的交叉变化，
    识别多头转空头或空头转多头的转换时刻。

    Args:
        data: 价格数据，需包含 high/low/close 列
        short_period: 短期EMA周期
        long_period: 长期EMA周期

    Returns:
        多空转换信号字典
    """
    try:
        if len(data) < long_period + 2:
            logger.warning(
                f"数据长度不足，需要至少 {long_period + 2} 根K线"
            )
            return None

        closes = data["close"].values
        highs = data["high"].values
        lows = data["low"].values

        short_ema = _calc_ema(closes, short_period)
        long_ema = _calc_ema(closes, long_period)

        if short_ema is None or long_ema is None:
            return None

        # 当前和前一根K线的多空力量差
        curr_bull = highs[-1] - short_ema[-1]
        curr_bear = lows[-1] - short_ema[-1]
        curr_net = curr_bull + curr_bear

        prev_bull = highs[-2] - short_ema[-2]
        prev_bear = lows[-2] - short_ema[-2]
        prev_net = prev_bull + prev_bear

        # EMA交叉检测
        curr_diff = short_ema[-1] - long_ema[-1]
        prev_diff = short_ema[-2] - long_ema[-2]

        transition = None

        # 金叉：短期EMA上穿长期EMA
        if prev_diff <= 0 and curr_diff > 0:
            transition = "bearish_to_bullish"
            signal = "buy"
            desc = "空转多，短期EMA上穿长期EMA，多头力量增强"
            confidence = 0.75

        # 死叉：短期EMA下穿长期EMA
        elif prev_diff >= 0 and curr_diff < 0:
            transition = "bullish_to_bearish"
            signal = "sell"
            desc = "多转空，短期EMA下穿长期EMA，空头力量增强"
            confidence = 0.75

        # 净力量翻转
        elif prev_net <= 0 and curr_net > 0:
            transition = "power_shift_bullish"
            signal = "buy"
            desc = "净力量由负转正，多头开始主导"
            confidence = 0.65

        elif prev_net >= 0 and curr_net < 0:
            transition = "power_shift_bearish"
            signal = "sell"
            desc = "净力量由正转负，空头开始主导"
            confidence = 0.65

        if transition is None:
            return None

        return {
            "type": "bull_bear_transition",
            "transition": transition,
            "signal": signal,
            "short_ema": smart_round(short_ema[-1]),
            "long_ema": smart_round(long_ema[-1]),
            "net_power": smart_round(curr_net),
            "prev_net_power": smart_round(prev_net),
            "confidence": confidence,
            "description": desc
        }

    except Exception as e:
        logger.error(f"检测多空转换失败: {e}")
        return None


def calculate_comprehensive_power(
    data: pd.DataFrame,
    period: int = 20
) -> Optional[Dict]:
    """
    综合力量评分

    汇总多空力量、力量对比、趋势强度和转换信号，
    给出综合多空力量评分和交易建议。

    Args:
        data: 价格数据，需包含 high/low/close/volume 列
        period: 评估周期

    Returns:
        综合力量评分字典
    """
    try:
        if len(data) < period:
            logger.warning(
                f"数据长度不足，需要至少 {period} 根K线"
            )
            return None

        components = []

        # 组件1：多空力量指标
        power = calculate_bull_bear_power(data, min(13, period))
        if power:
            power_score = 50.0
            if power["dominant"] == "strong_bull":
                power_score = 90.0
            elif power["dominant"] == "bull":
                power_score = 70.0
            elif power["dominant"] == "bear":
                power_score = 30.0
            elif power["dominant"] == "strong_bear":
                power_score = 10.0
            components.append({
                "name": "bull_bear_power",
                "score": power_score,
                "weight": 0.30
            })

        # 组件2：力量对比
        comparison = compare_bull_bear_strength(data, period)
        if comparison:
            # score 范围 -100 到 +100，映射到 0-100
            comp_score = (comparison["score"] + 100) / 2
            components.append({
                "name": "strength_comparison",
                "score": comp_score,
                "weight": 0.25
            })

        # 组件3：趋势强度
        trend = assess_trend_strength(data, period)
        if trend:
            trend_score = trend["total_score"]
            if trend["direction"] == "bearish":
                trend_score = 100 - trend_score
            components.append({
                "name": "trend_strength",
                "score": trend_score,
                "weight": 0.30
            })

        # 组件4：转换信号加成
        transition = detect_bull_bear_transition(data)
        if transition:
            if "bullish" in transition["transition"]:
                trans_score = 80.0
            else:
                trans_score = 20.0
            components.append({
                "name": "transition_signal",
                "score": trans_score,
                "weight": 0.15
            })

        if not components:
            return None

        # 加权综合评分
        total_weight = sum(c["weight"] for c in components)
        weighted_sum = sum(
            c["score"] * c["weight"] for c in components
        )
        final_score = weighted_sum / total_weight

        # 映射到 -100 ~ +100 的多空评分
        bull_bear_score = (final_score - 50) * 2

        if bull_bear_score > 40:
            verdict = "strong_bullish"
            signal = "buy"
            desc = f"综合多头强势，评分{bull_bear_score:+.0f}"
        elif bull_bear_score > 10:
            verdict = "mild_bullish"
            signal = "buy"
            desc = f"温和多头，评分{bull_bear_score:+.0f}"
        elif bull_bear_score > -10:
            verdict = "neutral"
            signal = "hold"
            desc = f"多空均衡，评分{bull_bear_score:+.0f}"
        elif bull_bear_score > -40:
            verdict = "mild_bearish"
            signal = "sell"
            desc = f"温和空头，评分{bull_bear_score:+.0f}"
        else:
            verdict = "strong_bearish"
            signal = "sell"
            desc = f"综合空头强势，评分{bull_bear_score:+.0f}"

        return {
            "type": "comprehensive_power",
            "final_score": round(final_score, 1),
            "bull_bear_score": round(bull_bear_score, 1),
            "verdict": verdict,
            "signal": signal,
            "components": components,
            "confidence": round(abs(bull_bear_score) / 100, 2),
            "description": desc
        }

    except Exception as e:
        logger.error(f"计算综合力量评分失败: {e}")
        return None


# ========== 私有辅助函数 ==========


def _calc_ema(
    values: np.ndarray,
    period: int
) -> Optional[np.ndarray]:
    """计算指数移动平均线"""
    if len(values) < period:
        return None

    multiplier = 2.0 / (period + 1)
    ema = np.zeros(len(values))
    ema[period - 1] = np.mean(values[:period])

    for i in range(period, len(values)):
        ema[i] = (values[i] - ema[i - 1]) * multiplier + ema[i - 1]

    # 前 period-1 个值用 SMA 填充以避免零值干扰
    for i in range(period - 1):
        ema[i] = np.mean(values[:i + 1])

    return ema


def _count_consecutive_direction(closes: np.ndarray) -> int:
    """从末尾向前计算连续同向K线数量"""
    if len(closes) < 2:
        return 0

    count = 1
    last_dir = closes[-1] > closes[-2]

    for i in range(len(closes) - 2, 0, -1):
        current_dir = closes[i] > closes[i - 1]
        if current_dir == last_dir:
            count += 1
        else:
            break

    return count


def _assess_hl_structure(
    highs: np.ndarray,
    lows: np.ndarray
) -> float:
    """
    评估高低点结构（0-100分）

    HH+HL 模式得高分（上升趋势），
    LH+LL 模式也得高分（下降趋势），
    混合模式得低分。
    """
    if len(highs) < 6:
        return 40.0

    third = len(highs) // 3
    seg1_high = highs[:third].max()
    seg2_high = highs[third:2 * third].max()
    seg3_high = highs[2 * third:].max()

    seg1_low = lows[:third].min()
    seg2_low = lows[third:2 * third].min()
    seg3_low = lows[2 * third:].min()

    # 上升结构：递增高点 + 递增低点
    hh = seg3_high > seg2_high > seg1_high
    hl = seg3_low > seg2_low > seg1_low

    # 下降结构：递减高点 + 递减低点
    lh = seg3_high < seg2_high < seg1_high
    ll = seg3_low < seg2_low < seg1_low

    if (hh and hl) or (lh and ll):
        return 90.0
    elif hh or hl or lh or ll:
        return 60.0

    return 30.0
