"""
突破分析模块
识别突破-回调-再突破模式、压力蓄积、突破质量评估、
入场策略、目标计算、突破失败检测
基于"交易突破"（第13课）及相关突破概念实现
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import logging
from src.utils.math_utils import smart_round

logger = logging.getLogger(__name__)


def identify_breakout_pullback_rebreak(
    data: pd.DataFrame,
    level: float,
    lookback: int = 30
) -> Optional[Dict]:
    """
    识别突破-回调-再突破模式

    等待价格突破关键位后出现回调，然后再次突破原方向。
    该模式提供更清晰的止损位和更好的盈亏比。

    Args:
        data: 价格数据，需包含 open/high/low/close/volume 列
        level: 关键价格水平（支撑或阻力位）
        lookback: 回看周期

    Returns:
        突破-回调-再突破信号字典，未检测到则返回 None
    """
    try:
        if len(data) < lookback:
            logger.warning(f"数据长度不足，需要至少 {lookback} 根K线")
            return None

        recent = data.iloc[-lookback:]
        closes = recent["close"].values
        highs = recent["high"].values
        lows = recent["low"].values

        # 阶段1：检测初始突破
        initial_breakout = _find_initial_breakout(closes, highs, lows, level)
        if not initial_breakout:
            return None

        direction = initial_breakout["direction"]
        break_idx = initial_breakout["index"]

        # 阶段2：检测回调
        pullback = _find_pullback(closes, highs, lows, level, direction, break_idx)
        if not pullback:
            return None

        pullback_depth = pullback["depth"]
        pullback_end_idx = pullback["end_index"]

        # 阶段3：检测再突破
        rebreak = _find_rebreak(closes, highs, lows, level, direction, pullback_end_idx)
        if not rebreak:
            return None

        # 计算回调深度百分比
        breakout_range = abs(closes[break_idx] - level)
        depth_pct = pullback_depth / breakout_range if breakout_range > 0 else 0

        # 评估信号质量
        confidence = _calc_bpr_confidence(depth_pct, direction, recent, break_idx)

        if direction == "bullish":
            stop_loss = pullback["low_price"]
            description = "向上突破-回调-再突破，做多信号"
        else:
            stop_loss = pullback["high_price"]
            description = "向下突破-回调-再突破，做空信号"

        return {
            "type": "breakout_pullback_rebreak",
            "direction": direction,
            "level": level,
            "pullback_depth_pct": round(depth_pct * 100, 2),
            "rebreak_confirmed": True,
            "stop_loss": stop_loss,
            "confidence": confidence,
            "signal": "buy" if direction == "bullish" else "sell",
            "description": description
        }

    except Exception as e:
        logger.error(f"识别突破-回调-再突破失败: {e}")
        return None


def detect_pressure_accumulation(
    data: pd.DataFrame,
    lookback: int = 20
) -> Optional[Dict]:
    """
    检测突破前的压力蓄积

    价格在关键位置附近形成密集区，多空双方在此博弈。
    突破该密集区通常伴随较强动能。

    Args:
        data: 价格数据
        lookback: 回看周期

    Returns:
        压力蓄积信号字典，未检测到则返回 None
    """
    try:
        if len(data) < lookback:
            logger.warning(f"数据长度不足，需要至少 {lookback} 根K线")
            return None

        recent = data.iloc[-lookback:]
        closes = recent["close"].values
        highs = recent["high"].values
        lows = recent["low"].values
        volumes = recent["volume"].values

        # 计算密集区参数
        price_range = highs.max() - lows.min()
        avg_price = closes.mean()

        if avg_price == 0:
            return None

        # 密集度：区间宽度占均价的百分比
        consolidation_pct = (price_range / avg_price) * 100

        # 密集区判定：区间宽度小于均价的5%视为密集
        if consolidation_pct > 5.0:
            return None

        # 计算密集区上下边界
        upper_bound = float(highs.max())
        lower_bound = float(lows.min())

        # 检测触及上下边界的次数（多空博弈强度）
        touch_threshold = price_range * 0.15
        upper_touches = int(np.sum(highs >= upper_bound - touch_threshold))
        lower_touches = int(np.sum(lows <= lower_bound + touch_threshold))
        total_touches = upper_touches + lower_touches

        # 成交量趋势分析：蓄积阶段成交量通常递减，突破前可能放大
        vol_first_half = volumes[:lookback // 2].mean()
        vol_second_half = volumes[lookback // 2:].mean()
        vol_trend = "decreasing" if vol_second_half < vol_first_half else "increasing"

        # 最近几根K线的成交量是否放大（突破前兆）
        recent_vol_avg = volumes[-3:].mean()
        overall_vol_avg = volumes.mean()
        vol_surge = bool(recent_vol_avg > overall_vol_avg * 1.3)

        # 判断潜在突破方向
        bias = _determine_accumulation_bias(
            closes, highs, lows, upper_bound, lower_bound
        )

        # 蓄积强度评分
        strength_score = _calc_accumulation_strength(
            consolidation_pct, total_touches, vol_trend, vol_surge, lookback
        )

        return {
            "type": "pressure_accumulation",
            "upper_bound": upper_bound,
            "lower_bound": lower_bound,
            "consolidation_pct": round(consolidation_pct, 2),
            "upper_touches": upper_touches,
            "lower_touches": lower_touches,
            "total_touches": total_touches,
            "volume_trend": vol_trend,
            "volume_surge": vol_surge,
            "bias": bias,
            "strength_score": strength_score,
            "confidence": min(0.60 + strength_score * 0.05, 0.90),
            "description": f"价格密集区蓄积，区间宽度{consolidation_pct:.1f}%，"
                           f"多空博弈{total_touches}次，偏向{bias}"
        }

    except Exception as e:
        logger.error(f"检测压力蓄积失败: {e}")
        return None


def assess_breakout_quality(
    data: pd.DataFrame,
    breakout_info: Dict
) -> Optional[Dict]:
    """
    评估突破质量，区分真突破和假突破

    通过成交量确认、K线实体大小、后续跟进力度等维度综合评估。

    Args:
        data: 价格数据
        breakout_info: 突破信息字典，需包含 direction 和 level 字段

    Returns:
        突破质量评估字典，评估失败则返回 None
    """
    try:
        if len(data) < 5:
            logger.warning("数据长度不足，需要至少5根K线")
            return None

        direction = breakout_info.get("direction")
        level = breakout_info.get("level")

        if not direction or level is None:
            logger.warning("breakout_info 缺少 direction 或 level 字段")
            return None

        # 1. 成交量确认（突破时是否放大）
        volume_score = _assess_volume_confirmation(data)

        # 2. K线实体大小（趋势K线确认）
        body_score = _assess_candle_body(data, direction)

        # 3. 后续跟进力度
        followthrough_score = _assess_followthrough(data, direction, level)

        # 4. 突破幅度评估
        magnitude_score = _assess_breakout_magnitude(data, level, direction)

        # 综合评分（满分100）
        total_score = (
            volume_score * 0.30 +
            body_score * 0.25 +
            followthrough_score * 0.25 +
            magnitude_score * 0.20
        )

        # 判定真假突破
        if total_score >= 70:
            quality = "strong"
            is_genuine = True
            description = "强势突破，成交量和动能均确认"
        elif total_score >= 50:
            quality = "moderate"
            is_genuine = True
            description = "中等突破，部分指标确认，需观察后续"
        elif total_score >= 30:
            quality = "weak"
            is_genuine = False
            description = "弱势突破，缺乏确认，假突破概率较高"
        else:
            quality = "failed"
            is_genuine = False
            description = "突破失败，动能不足，大概率回落"

        return {
            "type": "breakout_quality",
            "quality": quality,
            "is_genuine": is_genuine,
            "total_score": round(total_score, 1),
            "volume_score": round(volume_score, 1),
            "body_score": round(body_score, 1),
            "followthrough_score": round(followthrough_score, 1),
            "magnitude_score": round(magnitude_score, 1),
            "confidence": round(total_score / 100, 2),
            "description": description
        }

    except Exception as e:
        logger.error(f"评估突破质量失败: {e}")
        return None


def identify_breakout_entry(
    data: pd.DataFrame,
    breakout_info: Dict
) -> Optional[Dict]:
    """
    突破入场策略识别

    提供三种入场方式（按保守程度排序）：
    - aggressive 激进：直接追入突破
    - moderate 中等：突破后回调入场
    - conservative 保守：突破回调再突破入场

    Args:
        data: 价格数据
        breakout_info: 突破信息字典，需包含 direction 和 level 字段

    Returns:
        入场策略字典，识别失败则返回 None
    """
    try:
        if len(data) < 10:
            logger.warning("数据长度不足，需要至少10根K线")
            return None

        direction = breakout_info.get("direction")
        level = breakout_info.get("level")

        if not direction or level is None:
            logger.warning("breakout_info 缺少 direction 或 level 字段")
            return None

        current_price = data["close"].iloc[-1]
        entries = []

        # 策略1：激进入场 - 直接追入突破
        aggressive = _calc_aggressive_entry(data, direction, level, current_price)
        if aggressive:
            entries.append(aggressive)

        # 策略2：中等入场 - 突破后回调入场
        moderate = _calc_moderate_entry(data, direction, level, current_price)
        if moderate:
            entries.append(moderate)

        # 策略3：保守入场 - 突破回调再突破入场
        conservative = _calc_conservative_entry(
            data, direction, level, current_price
        )
        if conservative:
            entries.append(conservative)

        if not entries:
            return None

        # 选择当前最适合的入场方式
        recommended = _select_best_entry(entries, data, direction)

        return {
            "type": "breakout_entry",
            "direction": direction,
            "level": level,
            "current_price": current_price,
            "entries": entries,
            "recommended": recommended,
            "confidence": recommended["confidence"],
            "description": f"突破入场策略，推荐{recommended['style_cn']}入场"
        }

    except Exception as e:
        logger.error(f"识别突破入场策略失败: {e}")
        return None


def calculate_breakout_targets(
    data: pd.DataFrame,
    breakout_info: Dict
) -> Optional[Dict]:
    """
    计算突破目标位

    基于突破前区间宽度计算第一目标、第二目标和止损位。

    Args:
        data: 价格数据
        breakout_info: 突破信息字典，需包含 direction 和 level 字段

    Returns:
        目标位字典，计算失败则返回 None
    """
    try:
        if len(data) < 10:
            logger.warning("数据长度不足，需要至少10根K线")
            return None

        direction = breakout_info.get("direction")
        level = breakout_info.get("level")

        if not direction or level is None:
            logger.warning("breakout_info 缺少 direction 或 level 字段")
            return None

        current_price = data["close"].iloc[-1]

        # 计算突破前区间宽度
        range_width = _calc_pre_breakout_range(data, level)
        if range_width <= 0:
            return None

        if direction == "bullish":
            # 向上突破目标
            target_1 = level + range_width
            target_2 = level + range_width * 1.618
            stop_loss = level - range_width * 0.3

            # 盈亏比计算
            risk = current_price - stop_loss
            reward_1 = target_1 - current_price
            reward_2 = target_2 - current_price
        else:
            # 向下突破目标
            target_1 = level - range_width
            target_2 = level - range_width * 1.618
            stop_loss = level + range_width * 0.3

            # 盈亏比计算
            risk = stop_loss - current_price
            reward_1 = current_price - target_1
            reward_2 = current_price - target_2

        rr_ratio_1 = reward_1 / risk if risk > 0 else 0
        rr_ratio_2 = reward_2 / risk if risk > 0 else 0

        return {
            "type": "breakout_targets",
            "direction": direction,
            "level": level,
            "current_price": current_price,
            "range_width": smart_round(range_width),
            "target_1": smart_round(target_1),
            "target_2": smart_round(target_2),
            "stop_loss": smart_round(stop_loss),
            "risk_reward_1": round(rr_ratio_1, 2),
            "risk_reward_2": round(rr_ratio_2, 2),
            "confidence": 0.70 if rr_ratio_1 >= 2.0 else 0.55,
            "description": f"突破目标：T1={target_1:.2f}(盈亏比{rr_ratio_1:.1f})，"
                           f"T2={target_2:.2f}(盈亏比{rr_ratio_2:.1f})，"
                           f"止损={stop_loss:.2f}"
        }

    except Exception as e:
        logger.error(f"计算突破目标失败: {e}")
        return None


def detect_breakout_failure(
    data: pd.DataFrame,
    breakout_info: Dict
) -> Optional[Dict]:
    """
    检测突破失败（假突破）

    价格突破关键位后未能维持，迅速回落到突破位以内，
    形成反向交易机会。

    Args:
        data: 价格数据
        breakout_info: 突破信息字典，需包含 direction 和 level 字段

    Returns:
        突破失败信号字典，未检测到则返回 None
    """
    try:
        if len(data) < 10:
            logger.warning("数据长度不足，需要至少10根K线")
            return None

        direction = breakout_info.get("direction")
        level = breakout_info.get("level")

        if not direction or level is None:
            logger.warning("breakout_info 缺少 direction 或 level 字段")
            return None

        closes = data["close"].values
        highs = data["high"].values
        lows = data["low"].values
        current_price = closes[-1]

        if direction == "bullish":
            # 向上突破后回落到突破位以下
            broke_above = any(h > level for h in highs[-10:-2])
            fell_back = current_price < level
            if broke_above and fell_back:
                max_above = max(highs[-10:-2]) - level
                drop_below = level - current_price
                return {
                    "type": "breakout_failure",
                    "direction": "bullish_failure",
                    "level": level,
                    "max_penetration": smart_round(max_above),
                    "current_below": smart_round(drop_below),
                    "signal": "sell",
                    "confidence": 0.75,
                    "description": "向上突破失败，价格回落至突破位下方，做空机会"
                }
        else:
            # 向下突破后反弹到突破位以上
            broke_below = any(l < level for l in lows[-10:-2])
            rose_back = current_price > level
            if broke_below and rose_back:
                max_below = level - min(lows[-10:-2])
                rise_above = current_price - level
                return {
                    "type": "breakout_failure",
                    "direction": "bearish_failure",
                    "level": level,
                    "max_penetration": smart_round(max_below),
                    "current_above": smart_round(rise_above),
                    "signal": "buy",
                    "confidence": 0.75,
                    "description": "向下突破失败，价格反弹至突破位上方，做多机会"
                }

        return None

    except Exception as e:
        logger.error(f"检测突破失败: {e}")
        return None


# ========== 私有辅助函数 ==========


def _find_initial_breakout(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    level: float
) -> Optional[Dict]:
    """检测初始突破位置"""
    for i in range(1, len(closes)):
        # 向上突破：前一根收盘在下方，当前收盘在上方
        if closes[i - 1] <= level and closes[i] > level:
            return {"direction": "bullish", "index": i}
        # 向下突破：前一根收盘在上方，当前收盘在下方
        if closes[i - 1] >= level and closes[i] < level:
            return {"direction": "bearish", "index": i}
    return None


def _find_pullback(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    level: float,
    direction: str,
    start_idx: int
) -> Optional[Dict]:
    """检测突破后的回调"""
    if start_idx + 1 >= len(closes):
        return None

    if direction == "bullish":
        # 向上突破后，价格回调接近突破位
        min_price = float("inf")
        min_idx = start_idx + 1
        for i in range(start_idx + 1, len(closes)):
            if lows[i] < min_price:
                min_price = lows[i]
                min_idx = i
            # 回调到突破位附近（距离不超过突破幅度的80%）
            breakout_range = closes[start_idx] - level
            if breakout_range > 0 and (closes[start_idx] - min_price) > breakout_range * 0.3:
                depth = closes[start_idx] - min_price
                return {
                    "depth": depth,
                    "end_index": min_idx,
                    "low_price": min_price,
                    "high_price": highs[min_idx]
                }
    else:
        # 向下突破后，价格反弹接近突破位
        max_price = float("-inf")
        max_idx = start_idx + 1
        for i in range(start_idx + 1, len(closes)):
            if highs[i] > max_price:
                max_price = highs[i]
                max_idx = i
            breakout_range = level - closes[start_idx]
            if breakout_range > 0 and (max_price - closes[start_idx]) > breakout_range * 0.3:
                depth = max_price - closes[start_idx]
                return {
                    "depth": depth,
                    "end_index": max_idx,
                    "low_price": lows[max_idx],
                    "high_price": max_price
                }
    return None


def _find_rebreak(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    level: float,
    direction: str,
    start_idx: int
) -> Optional[Dict]:
    """检测回调后的再突破"""
    if start_idx + 1 >= len(closes):
        return None

    for i in range(start_idx + 1, len(closes)):
        if direction == "bullish" and closes[i] > level:
            return {"index": i, "price": closes[i]}
        if direction == "bearish" and closes[i] < level:
            return {"index": i, "price": closes[i]}
    return None


def _calc_bpr_confidence(
    depth_pct: float,
    direction: str,
    recent: pd.DataFrame,
    break_idx: int
) -> float:
    """计算突破-回调-再突破的置信度"""
    confidence = 0.60

    # 回调深度在38%-62%之间为理想区间（斐波那契回调）
    if 0.38 <= depth_pct <= 0.62:
        confidence += 0.15
    elif 0.25 <= depth_pct <= 0.75:
        confidence += 0.08

    # 成交量确认
    volumes = recent["volume"].values
    if break_idx < len(volumes) - 1:
        break_vol = volumes[break_idx]
        avg_vol = volumes[:break_idx].mean() if break_idx > 0 else break_vol
        if break_vol > avg_vol * 1.5:
            confidence += 0.10

    return min(round(confidence, 2), 0.95)


def _determine_accumulation_bias(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    upper_bound: float,
    lower_bound: float
) -> str:
    """判断蓄积区的潜在突破方向"""
    mid_point = (upper_bound + lower_bound) / 2

    # 最近收盘价在中点上方的比例
    recent_closes = closes[-5:]
    above_mid = sum(1 for c in recent_closes if c > mid_point)

    if above_mid >= 4:
        return "bullish"
    elif above_mid <= 1:
        return "bearish"
    return "neutral"


def _calc_accumulation_strength(
    consolidation_pct: float,
    total_touches: int,
    vol_trend: str,
    vol_surge: bool,
    lookback: int
) -> float:
    """计算蓄积强度评分（0-10）"""
    score = 0.0

    # 密集度越高（区间越窄），蓄积越强
    if consolidation_pct < 2.0:
        score += 3.0
    elif consolidation_pct < 3.5:
        score += 2.0
    else:
        score += 1.0

    # 触及次数越多，博弈越激烈
    touch_ratio = total_touches / lookback
    score += min(touch_ratio * 5, 3.0)

    # 成交量递减后放大是经典蓄积信号
    if vol_trend == "decreasing" and vol_surge:
        score += 3.0
    elif vol_surge:
        score += 1.5
    elif vol_trend == "decreasing":
        score += 1.0

    return min(round(score, 1), 10.0)


def _assess_volume_confirmation(data: pd.DataFrame) -> float:
    """评估突破时的成交量确认（0-100分）"""
    volumes = data["volume"].values
    if len(volumes) < 5:
        return 50.0

    breakout_vol = volumes[-1]
    avg_vol = volumes[:-1].mean()

    if avg_vol == 0:
        return 50.0

    ratio = breakout_vol / avg_vol
    if ratio >= 3.0:
        return 100.0
    elif ratio >= 2.0:
        return 85.0
    elif ratio >= 1.5:
        return 70.0
    elif ratio >= 1.0:
        return 50.0
    return 30.0


def _assess_candle_body(data: pd.DataFrame, direction: str) -> float:
    """评估突破K线的实体大小（0-100分）"""
    last = data.iloc[-1]
    body = abs(last["close"] - last["open"])
    total_range = last["high"] - last["low"]

    if total_range == 0:
        return 30.0

    body_ratio = body / total_range

    # 趋势方向确认
    if direction == "bullish" and last["close"] < last["open"]:
        return 20.0
    if direction == "bearish" and last["close"] > last["open"]:
        return 20.0

    if body_ratio >= 0.7:
        return 95.0
    elif body_ratio >= 0.5:
        return 75.0
    elif body_ratio >= 0.3:
        return 55.0
    return 35.0


def _assess_followthrough(
    data: pd.DataFrame,
    direction: str,
    level: float
) -> float:
    """评估突破后的跟进力度（0-100分）"""
    if len(data) < 3:
        return 50.0

    closes = data["close"].values

    if direction == "bullish":
        # 突破后连续收盘在突破位上方
        above_count = sum(1 for c in closes[-3:] if c > level)
        # 收盘价是否逐步走高
        rising = all(
            closes[i] >= closes[i - 1]
            for i in range(-2, 0)
            if abs(i) < len(closes)
        )
    else:
        above_count = sum(1 for c in closes[-3:] if c < level)
        rising = all(
            closes[i] <= closes[i - 1]
            for i in range(-2, 0)
            if abs(i) < len(closes)
        )

    score = above_count * 25.0
    if rising:
        score += 25.0

    return min(score, 100.0)


def _assess_breakout_magnitude(
    data: pd.DataFrame,
    level: float,
    direction: str
) -> float:
    """评估突破幅度（0-100分）"""
    current_price = data["close"].iloc[-1]
    atr = _simple_atr(data, 14)

    if atr == 0:
        return 50.0

    distance = abs(current_price - level)
    atr_multiple = distance / atr

    if atr_multiple >= 2.0:
        return 95.0
    elif atr_multiple >= 1.5:
        return 80.0
    elif atr_multiple >= 1.0:
        return 65.0
    elif atr_multiple >= 0.5:
        return 50.0
    return 30.0


def _simple_atr(data: pd.DataFrame, period: int = 14) -> float:
    """简易ATR计算"""
    if len(data) < period:
        period = len(data)
    if period == 0:
        return 0.0

    highs = data["high"].values[-period:]
    lows = data["low"].values[-period:]
    closes = data["close"].values[-period:]

    tr_values = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )
        tr_values.append(tr)

    return float(np.mean(tr_values)) if tr_values else 0.0


def _calc_aggressive_entry(
    data: pd.DataFrame,
    direction: str,
    level: float,
    current_price: float
) -> Optional[Dict]:
    """计算激进入场策略"""
    atr = _simple_atr(data, 14)
    if atr == 0:
        return None

    if direction == "bullish":
        entry = current_price
        stop_loss = level - atr * 0.5
        target = entry + atr * 2.0
    else:
        entry = current_price
        stop_loss = level + atr * 0.5
        target = entry - atr * 2.0

    risk = abs(entry - stop_loss)
    reward = abs(target - entry)
    rr = reward / risk if risk > 0 else 0

    return {
        "style": "aggressive",
        "style_cn": "激进",
        "entry": smart_round(entry),
        "stop_loss": smart_round(stop_loss),
        "target": smart_round(target),
        "risk_reward": round(rr, 2),
        "confidence": 0.60
    }


def _calc_moderate_entry(
    data: pd.DataFrame,
    direction: str,
    level: float,
    current_price: float
) -> Optional[Dict]:
    """计算中等入场策略（回调入场）"""
    atr = _simple_atr(data, 14)
    if atr == 0:
        return None

    if direction == "bullish":
        entry = level + atr * 0.2
        stop_loss = level - atr * 0.5
        target = entry + atr * 2.5
    else:
        entry = level - atr * 0.2
        stop_loss = level + atr * 0.5
        target = entry - atr * 2.5

    risk = abs(entry - stop_loss)
    reward = abs(target - entry)
    rr = reward / risk if risk > 0 else 0

    return {
        "style": "moderate",
        "style_cn": "中等",
        "entry": smart_round(entry),
        "stop_loss": smart_round(stop_loss),
        "target": smart_round(target),
        "risk_reward": round(rr, 2),
        "confidence": 0.72
    }


def _calc_conservative_entry(
    data: pd.DataFrame,
    direction: str,
    level: float,
    current_price: float
) -> Optional[Dict]:
    """计算保守入场策略（突破-回调-再突破入场）"""
    atr = _simple_atr(data, 14)
    if atr == 0:
        return None

    if direction == "bullish":
        entry = level + atr * 0.5
        stop_loss = level - atr * 0.3
        target = entry + atr * 3.0
    else:
        entry = level - atr * 0.5
        stop_loss = level + atr * 0.3
        target = entry - atr * 3.0

    risk = abs(entry - stop_loss)
    reward = abs(target - entry)
    rr = reward / risk if risk > 0 else 0

    return {
        "style": "conservative",
        "style_cn": "保守",
        "entry": smart_round(entry),
        "stop_loss": smart_round(stop_loss),
        "target": smart_round(target),
        "risk_reward": round(rr, 2),
        "confidence": 0.82
    }


def _select_best_entry(
    entries: List[Dict],
    data: pd.DataFrame,
    direction: str
) -> Dict:
    """选择当前最适合的入场方式"""
    current_price = data["close"].iloc[-1]

    # 按盈亏比和置信度综合排序
    scored = []
    for entry in entries:
        rr = entry.get("risk_reward", 0)
        conf = entry.get("confidence", 0)
        combined = rr * 0.4 + conf * 10 * 0.6
        scored.append((combined, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def _calc_pre_breakout_range(
    data: pd.DataFrame,
    level: float,
    lookback: int = 20
) -> float:
    """计算突破前的价格区间宽度"""
    if len(data) < lookback:
        lookback = len(data)

    recent = data.iloc[-lookback:]
    range_high = recent["high"].max()
    range_low = recent["low"].min()

    return float(range_high - range_low)
