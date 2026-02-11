"""
回调分析模块
实现斐波那契回调识别、回调深度评估、回调入场策略、
回调质量评分、多级回调目标计算
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import logging
from src.utils.math_utils import smart_round

logger = logging.getLogger(__name__)

# 斐波那契关键回调比率
FIB_LEVELS = [0.236, 0.382, 0.500, 0.618, 0.786]


def identify_fibonacci_retracement(
    data: pd.DataFrame,
    swing_high: float,
    swing_low: float,
    direction: str = "bullish"
) -> Optional[Dict]:
    """
    识别斐波那契回调位

    根据摆动高低点计算斐波那契回调水平，
    并判断当前价格处于哪个回调区间。

    Args:
        data: 价格数据，需包含 close 列
        swing_high: 摆动高点价格
        swing_low: 摆动低点价格
        direction: 趋势方向 ('bullish' 或 'bearish')

    Returns:
        斐波那契回调分析字典，识别失败则返回 None
    """
    try:
        if swing_high <= swing_low:
            logger.warning("摆动高点必须大于摆动低点")
            return None

        current_price = data["close"].iloc[-1]
        price_range = swing_high - swing_low

        # 计算各斐波那契回调位
        fib_prices = {}
        for level in FIB_LEVELS:
            if direction == "bullish":
                fib_prices[level] = swing_high - price_range * level
            else:
                fib_prices[level] = swing_low + price_range * level

        # 判断当前价格所在的回调区间
        current_level = _find_current_fib_zone(
            current_price, fib_prices, direction
        )

        # 计算回调深度百分比
        if direction == "bullish":
            depth_pct = (swing_high - current_price) / price_range
        else:
            depth_pct = (current_price - swing_low) / price_range

        depth_pct = max(0, min(depth_pct, 1.0))

        # 评估回调质量
        quality = _assess_retracement_quality(depth_pct, data)

        return {
            "type": "fibonacci_retracement",
            "direction": direction,
            "swing_high": swing_high,
            "swing_low": swing_low,
            "fib_levels": {
                str(k): smart_round(v) for k, v in fib_prices.items()
            },
            "current_price": current_price,
            "current_zone": current_level,
            "depth_pct": round(depth_pct * 100, 2),
            "quality": quality,
            "confidence": quality["score"] / 100,
            "description": f"斐波那契回调至{depth_pct*100:.1f}%，"
                           f"当前处于{current_level}区间"
        }

    except Exception as e:
        logger.error(f"识别斐波那契回调失败: {e}")
        return None


def assess_retracement_depth(
    data: pd.DataFrame,
    trend_direction: str = "bullish",
    lookback: int = 30
) -> Optional[Dict]:
    """
    评估回调深度，判断回调是否健康

    浅回调（<38.2%）表示趋势强劲；
    中等回调（38.2%-61.8%）为理想入场区间；
    深回调（>61.8%）可能预示趋势减弱。

    Args:
        data: 价格数据
        trend_direction: 趋势方向
        lookback: 回看周期

    Returns:
        回调深度评估字典
    """
    try:
        if len(data) < lookback:
            logger.warning(f"数据长度不足，需要至少 {lookback} 根K线")
            return None

        recent = data.iloc[-lookback:]
        highs = recent["high"].values
        lows = recent["low"].values
        closes = recent["close"].values

        swing_high = float(highs.max())
        swing_low = float(lows.min())
        price_range = swing_high - swing_low

        if price_range == 0:
            return None

        current_price = closes[-1]

        if trend_direction == "bullish":
            depth = (swing_high - current_price) / price_range
        else:
            depth = (current_price - swing_low) / price_range

        depth = max(0, min(depth, 1.0))

        # 分类回调深度
        if depth < 0.236:
            category = "minimal"
            health = "very_strong_trend"
            description = "极浅回调，趋势极强，追入风险较高"
        elif depth < 0.382:
            category = "shallow"
            health = "strong_trend"
            description = "浅回调，趋势强劲，可考虑入场"
        elif depth < 0.618:
            category = "moderate"
            health = "healthy"
            description = "中等回调，理想入场区间"
        elif depth < 0.786:
            category = "deep"
            health = "weakening"
            description = "深回调，趋势可能减弱"
        else:
            category = "very_deep"
            health = "potential_reversal"
            description = "极深回调，趋势可能反转"

        # 置信度基于回调深度
        confidence = 0.85 if category == "moderate" else 0.65

        return {
            "type": "retracement_depth",
            "direction": trend_direction,
            "depth_pct": round(depth * 100, 2),
            "category": category,
            "health": health,
            "swing_high": swing_high,
            "swing_low": swing_low,
            "confidence": confidence,
            "description": description
        }

    except Exception as e:
        logger.error(f"评估回调深度失败: {e}")
        return None


def calculate_retracement_entry(
    data: pd.DataFrame,
    swing_high: float,
    swing_low: float,
    direction: str = "bullish"
) -> Optional[Dict]:
    """
    计算回调入场策略

    在斐波那契关键回调位设置入场点、止损和目标。

    Args:
        data: 价格数据
        swing_high: 摆动高点
        swing_low: 摆动低点
        direction: 趋势方向

    Returns:
        回调入场策略字典
    """
    try:
        if swing_high <= swing_low:
            return None

        price_range = swing_high - swing_low
        current_price = data["close"].iloc[-1]

        if direction == "bullish":
            # 做多：在回调位买入
            entry_382 = swing_high - price_range * 0.382
            entry_500 = swing_high - price_range * 0.500
            entry_618 = swing_high - price_range * 0.618
            stop_loss = swing_low - price_range * 0.1
            target = swing_high + price_range * 0.618
        else:
            # 做空：在反弹位卖出
            entry_382 = swing_low + price_range * 0.382
            entry_500 = swing_low + price_range * 0.500
            entry_618 = swing_low + price_range * 0.618
            stop_loss = swing_high + price_range * 0.1
            target = swing_low - price_range * 0.618

        # 选择最接近当前价格的入场位
        entries = [
            ("fib_382", entry_382, 0.75),
            ("fib_500", entry_500, 0.80),
            ("fib_618", entry_618, 0.85),
        ]

        best = min(
            entries,
            key=lambda e: abs(e[1] - current_price)
        )

        risk = abs(best[1] - stop_loss)
        reward = abs(target - best[1])
        rr = reward / risk if risk > 0 else 0

        return {
            "type": "retracement_entry",
            "direction": direction,
            "entry_level": best[0],
            "entry_price": smart_round(best[1]),
            "stop_loss": smart_round(stop_loss),
            "target": smart_round(target),
            "risk_reward": round(rr, 2),
            "confidence": best[2],
            "all_entries": [
                {"level": n, "price": smart_round(p)}
                for n, p, _ in entries
            ],
            "description": f"回调入场于{best[0]}位"
                           f"({best[1]:.2f})，"
                           f"盈亏比{rr:.1f}"
        }

    except Exception as e:
        logger.error(f"计算回调入场失败: {e}")
        return None


def calculate_multi_level_targets(
    data: pd.DataFrame,
    swing_high: float,
    swing_low: float,
    direction: str = "bullish"
) -> Optional[Dict]:
    """
    计算多级回调目标价位

    基于斐波那契回调位和扩展位，计算多级目标价格，
    包括回调目标（入场区域）和扩展目标（获利区域）。

    Args:
        data: 价格数据，需包含 close 列
        swing_high: 摆动高点价格
        swing_low: 摆动低点价格
        direction: 趋势方向 ('bullish' 或 'bearish')

    Returns:
        多级目标字典，计算失败则返回 None
    """
    try:
        if swing_high <= swing_low:
            logger.warning("摆动高点必须大于摆动低点")
            return None

        current_price = data["close"].iloc[-1]
        price_range = swing_high - swing_low

        # 斐波那契回调位（入场区域）
        retracement_levels = [0.236, 0.382, 0.500, 0.618, 0.786]
        # 斐波那契扩展位（获利区域）
        extension_levels = [1.000, 1.272, 1.618, 2.000, 2.618]

        retracement_targets = []
        extension_targets = []

        for level in retracement_levels:
            if direction == "bullish":
                price = swing_high - price_range * level
            else:
                price = swing_low + price_range * level

            retracement_targets.append({
                "level": level,
                "price": smart_round(price),
                "label": f"回调{level*100:.1f}%"
            })

        for level in extension_levels:
            if direction == "bullish":
                price = swing_high + price_range * (level - 1.0)
            else:
                price = swing_low - price_range * (level - 1.0)

            extension_targets.append({
                "level": level,
                "price": smart_round(price),
                "label": f"扩展{level*100:.1f}%"
            })

        # 找到当前价格最接近的回调位
        nearest = min(
            retracement_targets,
            key=lambda t: abs(t["price"] - current_price)
        )

        # 推荐的入场和获利目标
        if direction == "bullish":
            entry_zone = [
                t for t in retracement_targets
                if 0.382 <= t["level"] <= 0.618
            ]
            tp1 = swing_high
            tp2 = extension_targets[1]["price"]  # 1.272 扩展
            tp3 = extension_targets[2]["price"]  # 1.618 扩展
        else:
            entry_zone = [
                t for t in retracement_targets
                if 0.382 <= t["level"] <= 0.618
            ]
            tp1 = swing_low
            tp2 = extension_targets[1]["price"]
            tp3 = extension_targets[2]["price"]

        return {
            "type": "multi_level_targets",
            "direction": direction,
            "swing_high": swing_high,
            "swing_low": swing_low,
            "current_price": current_price,
            "retracement_targets": retracement_targets,
            "extension_targets": extension_targets,
            "nearest_level": nearest,
            "entry_zone": entry_zone,
            "take_profit": {
                "tp1": smart_round(tp1),
                "tp2": smart_round(tp2),
                "tp3": smart_round(tp3),
            },
            "confidence": 0.72,
            "description": (
                f"多级目标：入场区间"
                f"{entry_zone[0]['price']}-{entry_zone[-1]['price']}，"
                f"目标T1={tp1:.2f} T2={tp2:.2f} T3={tp3:.2f}"
            ) if entry_zone else "无有效入场区间"
        }

    except Exception as e:
        logger.error(f"计算多级回调目标失败: {e}")
        return None


# ========== 私有辅助函数 ==========


def _find_current_fib_zone(
    current_price: float,
    fib_prices: Dict[float, float],
    direction: str
) -> str:
    """判断当前价格所在的斐波那契区间"""
    sorted_levels = sorted(fib_prices.items(), key=lambda x: x[1])

    if direction == "bullish":
        sorted_levels = sorted(
            fib_prices.items(), key=lambda x: x[1], reverse=True
        )

    for i, (level, price) in enumerate(sorted_levels):
        if direction == "bullish" and current_price >= price:
            return f"above_{level}"
        if direction == "bearish" and current_price <= price:
            return f"below_{level}"

    return "beyond_0.786"


def _assess_retracement_quality(
    depth_pct: float,
    data: pd.DataFrame
) -> Dict:
    """评估回调质量"""
    score = 50

    # 回调深度评分：38.2%-61.8%为理想区间
    if 0.382 <= depth_pct <= 0.618:
        score += 30
    elif 0.236 <= depth_pct <= 0.786:
        score += 15

    # 成交量分析：回调时成交量递减为健康信号
    if len(data) >= 5:
        volumes = data["volume"].values
        recent_vol = volumes[-3:].mean()
        prior_vol = volumes[-6:-3].mean() if len(volumes) >= 6 else volumes.mean()
        if prior_vol > 0 and recent_vol < prior_vol * 0.8:
            score += 10

        # 逐根递减检测：检查最近5根K线成交量是否逐步递减
        if len(volumes) >= 5:
            last5 = volumes[-5:]
            decreasing_count = sum(
                1 for i in range(1, len(last5)) if last5[i] < last5[i - 1]
            )
            if decreasing_count >= 3:
                score += 5
            if decreasing_count >= 4:
                score += 5

            # 递减斜率评分：用线性回归斜率衡量递减速度
            x = np.arange(len(last5), dtype=float)
            if last5.std() > 0:
                slope = np.polyfit(x, last5, 1)[0]
                avg_vol = last5.mean()
                if avg_vol > 0:
                    norm_slope = slope / avg_vol
                    if norm_slope < -0.05:
                        score += 5

    score = min(score, 100)

    if score >= 80:
        label = "excellent"
    elif score >= 60:
        label = "good"
    elif score >= 40:
        label = "fair"
    else:
        label = "poor"

    return {"score": score, "label": label}


def count_pullback_bars(
    data: pd.DataFrame,
    direction: str = "bullish",
    lookback: int = 30
) -> Optional[Dict]:
    """
    数K线功能：统计回调中连续反向K线数量

    上升趋势中统计连续阴线数，下降趋势中统计连续阳线数，
    与历史平均对比判断回调是否耗尽。

    Args:
        data: 价格数据
        direction: 趋势方向 ('bullish' 或 'bearish')
        lookback: 回看周期

    Returns:
        回调K线统计字典，数据不足返回 None
    """
    try:
        if len(data) < lookback:
            logger.warning(f"数据长度不足，需要至少 {lookback} 根K线")
            return None

        recent = data.iloc[-lookback:]
        closes = recent['close'].values
        opens = recent['open'].values

        # 判断每根K线是阳线还是阴线
        is_bearish = closes < opens
        is_bullish = closes > opens

        # 统计当前连续反向K线数
        if direction == "bullish":
            target = is_bearish
        else:
            target = is_bullish

        # 从最后一根K线往前数连续反向K线
        current_count = 0
        for i in range(len(target) - 1, -1, -1):
            if target[i]:
                current_count += 1
            else:
                break

        # 统计历史上所有连续反向K线段的长度
        segments = []
        seg_len = 0
        for i in range(len(target)):
            if target[i]:
                seg_len += 1
            else:
                if seg_len > 0:
                    segments.append(seg_len)
                seg_len = 0
        if seg_len > 0:
            segments.append(seg_len)

        avg_count = np.mean(segments) if segments else 0
        max_count = max(segments) if segments else 0

        # 判断回调是否耗尽
        is_exhausted = bool(current_count >= avg_count * 1.5) if avg_count > 0 else False

        if avg_count > 0:
            confidence = min(0.85, 0.50 + current_count / (avg_count * 2) * 0.35)
        else:
            confidence = 0.50

        label = '阴线' if direction == "bullish" else '阳线'

        return {
            "type": "bar_counting",
            "direction": direction,
            "count": current_count,
            "avg_count": round(avg_count, 1),
            "max_count": max_count,
            "is_exhausted": is_exhausted,
            "confidence": round(confidence, 2),
            "description": f"当前连续{current_count}根{label}，"
                           f"历史平均{avg_count:.1f}根，"
                           f"{'回调可能耗尽' if is_exhausted else '回调仍在进行'}"
        }

    except Exception as e:
        logger.error(f"统计回调K线失败: {e}")
        return None


def identify_complex_pullback(
    data: pd.DataFrame,
    direction: str = "bullish",
    lookback: int = 40
) -> Optional[Dict]:
    """
    复杂回调/多腿回调识别

    检测回调中的多个波段（legs），判断是否形成小型区间。
    复杂回调通常包含2-3个波段，每个波段有独立的高低点。

    Args:
        data: 价格数据
        direction: 趋势方向 ('bullish' 或 'bearish')
        lookback: 回看周期

    Returns:
        复杂回调分析字典，未检测到返回 None
    """
    try:
        if len(data) < lookback:
            logger.warning(f"数据长度不足，需要至少 {lookback} 根K线")
            return None

        recent = data.iloc[-lookback:]
        closes = recent['close'].values
        highs = recent['high'].values
        lows = recent['low'].values

        # 查找局部极值点来识别波段
        legs = []
        window = max(3, lookback // 10)

        swing_points = []
        for i in range(window, len(closes) - window):
            if highs[i] == max(highs[i - window:i + window + 1]):
                swing_points.append(('high', i, highs[i]))
            if lows[i] == min(lows[i - window:i + window + 1]):
                swing_points.append(('low', i, lows[i]))

        # 按索引排序并去重相邻同类型点
        swing_points.sort(key=lambda x: x[1])
        filtered = []
        for pt in swing_points:
            if not filtered or filtered[-1][0] != pt[0]:
                filtered.append(pt)

        # 统计波段数（高-低或低-高的交替）
        legs_count = max(0, len(filtered) - 1)

        if legs_count < 2:
            return None

        # 判断是否形成小型区间
        range_high = max(p[2] for p in filtered if p[0] == 'high') if any(p[0] == 'high' for p in filtered) else highs.max()
        range_low = min(p[2] for p in filtered if p[0] == 'low') if any(p[0] == 'low' for p in filtered) else lows.min()
        range_width = range_high - range_low

        avg_price = closes.mean()
        range_pct = range_width / avg_price * 100 if avg_price > 0 else 0

        # 判断形态
        if legs_count >= 4:
            pattern = "trading_range"
        elif legs_count == 3:
            pattern = "three_leg_pullback"
        else:
            pattern = "two_leg_pullback"

        confidence = min(0.85, 0.50 + legs_count * 0.08)

        return {
            "type": "complex_pullback",
            "direction": direction,
            "legs_count": legs_count,
            "pattern": pattern,
            "range_high": smart_round(range_high),
            "range_low": smart_round(range_low),
            "range_pct": round(range_pct, 2),
            "swing_points": len(filtered),
            "confidence": round(confidence, 2),
            "description": f"复杂回调：{legs_count}个波段，"
                           f"形态为{pattern}，"
                           f"区间宽度{range_pct:.1f}%"
        }

    except Exception as e:
        logger.error(f"识别复杂回调失败: {e}")
        return None


def identify_abcd_pattern(
    data: pd.DataFrame,
    direction: str = "bullish",
    lookback: int = 40
) -> Optional[Dict]:
    """
    AB=CD形态识别：两腿回调，第二腿长度约等于第一腿

    AB=CD是经典的对称回调形态，当CD腿长度接近AB腿时，
    预示回调可能结束，趋势即将恢复。

    Args:
        data: 价格数据
        direction: 趋势方向 ('bullish' 或 'bearish')
        lookback: 回看周期

    Returns:
        AB=CD形态字典，未检测到返回 None
    """
    try:
        if len(data) < lookback:
            logger.warning(f"数据长度不足，需要至少 {lookback} 根K线")
            return None

        recent = data.iloc[-lookback:]
        highs = recent['high'].values
        lows = recent['low'].values

        # 查找摆动点
        window = max(3, lookback // 10)
        swing_highs = []
        swing_lows = []

        for i in range(window, len(highs) - window):
            if highs[i] == max(highs[i - window:i + window + 1]):
                swing_highs.append((i, highs[i]))
            if lows[i] == min(lows[i - window:i + window + 1]):
                swing_lows.append((i, lows[i]))

        if direction == "bullish":
            # 看涨AB=CD：A(低)->B(高)->C(低)->D(高预期)
            if len(swing_lows) < 2 or len(swing_highs) < 1:
                return None

            a_idx, a_price = swing_lows[-2]
            c_idx, c_price = swing_lows[-1]

            # 找A和C之间的高点作为B
            b_candidates = [
                (idx, p) for idx, p in swing_highs
                if a_idx < idx < c_idx
            ]
            if not b_candidates:
                return None
            b_idx, b_price = max(b_candidates, key=lambda x: x[1])

            ab_length = b_price - a_price
            bc_length = b_price - c_price

            if ab_length <= 0 or bc_length <= 0:
                return None

            # D点预测
            d_price = c_price + ab_length
        else:
            # 看跌AB=CD：A(高)->B(低)->C(高)->D(低预期)
            if len(swing_highs) < 2 or len(swing_lows) < 1:
                return None

            a_idx, a_price = swing_highs[-2]
            c_idx, c_price = swing_highs[-1]

            b_candidates = [
                (idx, p) for idx, p in swing_lows
                if a_idx < idx < c_idx
            ]
            if not b_candidates:
                return None
            b_idx, b_price = min(b_candidates, key=lambda x: x[1])

            ab_length = a_price - b_price
            bc_length = c_price - b_price

            if ab_length <= 0 or bc_length <= 0:
                return None

            d_price = c_price - ab_length

        # 对称比率：CD/AB 越接近1越对称
        symmetry_ratio = bc_length / ab_length if ab_length > 0 else 0

        # 对称比率在0.618-1.0之间为有效AB=CD
        if symmetry_ratio < 0.5 or symmetry_ratio > 1.5:
            return None

        # 置信度基于对称性
        sym_diff = abs(1.0 - symmetry_ratio)
        if sym_diff < 0.1:
            confidence = 0.85
        elif sym_diff < 0.2:
            confidence = 0.75
        else:
            confidence = 0.65

        return {
            "type": "abcd_pattern",
            "direction": direction,
            "points": {
                "A": smart_round(a_price),
                "B": smart_round(b_price),
                "C": smart_round(c_price),
                "D_projected": smart_round(d_price),
            },
            "ab_length": smart_round(ab_length),
            "bc_length": smart_round(bc_length),
            "symmetry_ratio": round(symmetry_ratio, 3),
            "confidence": confidence,
            "description": f"AB=CD形态，对称比率{symmetry_ratio:.2f}，"
                           f"D点预测价位{d_price:.2f}"
        }

    except Exception as e:
        logger.error(f"识别AB=CD形态失败: {e}")
        return None
