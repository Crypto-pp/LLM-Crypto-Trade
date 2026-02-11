"""
市场结构分析模块
识别Higher Highs/Lower Lows、趋势判断、结构破坏检测
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


def find_swing_highs_lows(
    data: pd.DataFrame,
    lookback: int = 5
) -> Dict[str, List[Dict]]:
    """
    查找摆动高点和低点

    Args:
        data: 价格数据
        lookback: 左右查看的K线数量

    Returns:
        包含swing_highs和swing_lows的字典
    """
    try:
        swing_highs = []
        swing_lows = []

        high_values = data['high'].values
        low_values = data['low'].values

        for i in range(lookback, len(data) - lookback):
            # 摆动高点
            if high_values[i] == max(high_values[i-lookback:i+lookback+1]):
                swing_highs.append({
                    'index': i,
                    'price': high_values[i],
                    'time': data.index[i]
                })

            # 摆动低点
            if low_values[i] == min(low_values[i-lookback:i+lookback+1]):
                swing_lows.append({
                    'index': i,
                    'price': low_values[i],
                    'time': data.index[i]
                })

        return {
            'swing_highs': swing_highs,
            'swing_lows': swing_lows
        }

    except Exception as e:
        logger.error(f"查找摆动高低点失败: {e}")
        return {'swing_highs': [], 'swing_lows': []}


def identify_market_structure(data: pd.DataFrame) -> Optional[Dict]:
    """
    识别市场结构

    Returns:
        市场结构分析结果
    """
    try:
        swings = find_swing_highs_lows(data)
        swing_highs = swings['swing_highs']
        swing_lows = swings['swing_lows']

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return None

        # 分析最近的高点和低点
        recent_highs = swing_highs[-2:]
        recent_lows = swing_lows[-2:]

        hh = recent_highs[1]['price'] > recent_highs[0]['price']  # Higher High
        hl = recent_lows[1]['price'] > recent_lows[0]['price']    # Higher Low
        lh = recent_highs[1]['price'] < recent_highs[0]['price']  # Lower High
        ll = recent_lows[1]['price'] < recent_lows[0]['price']    # Lower Low

        if hh and hl:
            return {
                'structure': 'uptrend',
                'description': 'HH + HL，上升趋势',
                'bias': 'bullish',
                'strategy': 'buy_dips',
                'confidence': 0.80
            }
        elif lh and ll:
            return {
                'structure': 'downtrend',
                'description': 'LH + LL，下降趋势',
                'bias': 'bearish',
                'strategy': 'sell_rallies',
                'confidence': 0.80
            }
        else:
            return {
                'structure': 'ranging',
                'description': '震荡区间',
                'bias': 'neutral',
                'strategy': 'range_trading',
                'confidence': 0.65
            }

    except Exception as e:
        logger.error(f"识别市场结构失败: {e}")
        return None


def detect_structure_break(data: pd.DataFrame) -> Optional[Dict]:
    """
    检测结构破坏信号

    Returns:
        结构破坏信号字典
    """
    try:
        current_structure = identify_market_structure(data)

        if not current_structure:
            return None

        swings = find_swing_highs_lows(data)
        swing_highs = swings['swing_highs']
        swing_lows = swings['swing_lows']

        if current_structure['structure'] == 'uptrend':
            # 上升趋势中，如果出现Lower Low，结构破坏
            if len(swing_lows) >= 2:
                recent_lows = swing_lows[-2:]
                if recent_lows[1]['price'] < recent_lows[0]['price']:
                    return {
                        'break_type': 'uptrend_broken',
                        'signal': 'potential_reversal_to_downtrend',
                        'action': 'exit_longs_or_prepare_shorts',
                        'confidence': 0.75,
                        'description': '上升趋势结构破坏，可能反转'
                    }

        elif current_structure['structure'] == 'downtrend':
            # 下降趋势中，如果出现Higher High，结构破坏
            if len(swing_highs) >= 2:
                recent_highs = swing_highs[-2:]
                if recent_highs[1]['price'] > recent_highs[0]['price']:
                    return {
                        'break_type': 'downtrend_broken',
                        'signal': 'potential_reversal_to_uptrend',
                        'action': 'exit_shorts_or_prepare_longs',
                        'confidence': 0.75,
                        'description': '下降趋势结构破坏，可能反转'
                    }

        return None

    except Exception as e:
        logger.error(f"检测结构破坏失败: {e}")
        return None


def identify_trend_phase(
    data: pd.DataFrame,
    lookback: int = 50
) -> Optional[Dict]:
    """
    趋势阶段判断：初期/中期/末期

    基于K线实体变化、影线增长、动能衰减信号，
    判断当前趋势处于哪个阶段。

    Args:
        data: 价格数据
        lookback: 回看周期

    Returns:
        趋势阶段分析字典，数据不足返回 None
    """
    try:
        if len(data) < lookback:
            logger.warning(f"数据长度不足，需要至少 {lookback} 根K线")
            return None

        recent = data.iloc[-lookback:]
        closes = recent['close'].values
        opens = recent['open'].values
        highs = recent['high'].values
        lows = recent['low'].values

        # 判断趋势方向
        first_half = closes[:lookback // 2]
        second_half = closes[lookback // 2:]
        trend_direction = "bullish" if second_half.mean() > first_half.mean() else "bearish"

        # 将数据分为三段分析
        seg_len = lookback // 3
        seg1 = slice(0, seg_len)
        seg2 = slice(seg_len, seg_len * 2)
        seg3 = slice(seg_len * 2, None)

        # 指标1：实体大小变化
        bodies = np.abs(closes - opens)
        body_avg = [bodies[seg1].mean(), bodies[seg2].mean(), bodies[seg3].mean()]

        # 指标2：影线长度变化
        upper_wicks = highs - np.maximum(closes, opens)
        lower_wicks = np.minimum(closes, opens) - lows
        total_wicks = upper_wicks + lower_wicks
        wick_avg = [total_wicks[seg1].mean(), total_wicks[seg2].mean(), total_wicks[seg3].mean()]

        # 指标3：价格变化速率（动能）
        price_changes = np.abs(np.diff(closes))
        pc_seg_len = len(price_changes) // 3
        momentum = [
            price_changes[:pc_seg_len].mean(),
            price_changes[pc_seg_len:pc_seg_len * 2].mean(),
            price_changes[pc_seg_len * 2:].mean(),
        ]

        characteristics = []

        # 判断阶段
        # 初期：实体递增、影线短、动能增强
        # 中期：实体稳定、影线适中、动能稳定
        # 末期：实体递减、影线增长、动能衰减

        body_trend = _calc_trend(body_avg)
        wick_trend = _calc_trend(wick_avg)
        momentum_trend = _calc_trend(momentum)

        late_score = 0

        if body_trend < -0.1:
            late_score += 1
            characteristics.append("实体递减")
        elif body_trend > 0.1:
            characteristics.append("实体递增")
        else:
            characteristics.append("实体稳定")

        if wick_trend > 0.1:
            late_score += 1
            characteristics.append("影线增长")
        elif wick_trend < -0.1:
            characteristics.append("影线缩短")
        else:
            characteristics.append("影线稳定")

        if momentum_trend < -0.1:
            late_score += 1
            characteristics.append("动能衰减")
        elif momentum_trend > 0.1:
            characteristics.append("动能增强")
        else:
            characteristics.append("动能稳定")

        if late_score >= 2:
            phase = "late"
            confidence = 0.75
        elif late_score == 0 and body_trend > 0 and momentum_trend > 0:
            phase = "early"
            confidence = 0.70
        else:
            phase = "middle"
            confidence = 0.65

        phase_cn = {"early": "初期", "middle": "中期", "late": "末期"}

        return {
            "type": "trend_phase",
            "trend_direction": trend_direction,
            "phase": phase,
            "characteristics": characteristics,
            "body_trend": round(body_trend, 3),
            "wick_trend": round(wick_trend, 3),
            "momentum_trend": round(momentum_trend, 3),
            "confidence": confidence,
            "description": f"{trend_direction}趋势{phase_cn[phase]}，"
                           f"特征：{'、'.join(characteristics)}"
        }

    except Exception as e:
        logger.error(f"识别趋势阶段失败: {e}")
        return None


def _calc_trend(values: list) -> float:
    """计算三段数据的趋势方向（归一化斜率）"""
    if len(values) < 2:
        return 0.0
    avg = np.mean(values)
    if avg == 0:
        return 0.0
    x = np.arange(len(values), dtype=float)
    slope = np.polyfit(x, values, 1)[0]
    return slope / avg
