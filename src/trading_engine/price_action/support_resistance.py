"""
支撑阻力位识别模块
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def identify_support_resistance(
    data: pd.DataFrame,
    lookback: int = 50,
    touch_threshold: float = 0.02,
    min_touches: int = 2
) -> Dict[str, List[Dict]]:
    """
    识别支撑和阻力位

    Args:
        data: 价格数据
        lookback: 回看周期
        touch_threshold: 触及阈值（2%）
        min_touches: 最少触及次数

    Returns:
        包含support和resistance列表的字典
    """
    try:
        support_levels = []
        resistance_levels = []

        # 找出局部高低点
        highs = data['high'].values
        lows = data['low'].values

        # 识别支撑位
        for i in range(lookback, len(data)):
            price_level = lows[i]
            touch_count = 0

            # 统计触及次数
            for j in range(max(0, i-lookback), i):
                if abs(lows[j] - price_level) / price_level < touch_threshold:
                    touch_count += 1

            if touch_count >= min_touches:
                support_levels.append({
                    'price': price_level,
                    'touches': touch_count,
                    'index': i,
                    'time': data.index[i]
                })

        # 识别阻力位
        for i in range(lookback, len(data)):
            price_level = highs[i]
            touch_count = 0

            for j in range(max(0, i-lookback), i):
                if abs(highs[j] - price_level) / price_level < touch_threshold:
                    touch_count += 1

            if touch_count >= min_touches:
                resistance_levels.append({
                    'price': price_level,
                    'touches': touch_count,
                    'index': i,
                    'time': data.index[i]
                })

        # 去重并排序
        support_levels = _deduplicate_levels(support_levels, touch_threshold)
        resistance_levels = _deduplicate_levels(resistance_levels, touch_threshold)

        return {
            'support': support_levels,
            'resistance': resistance_levels
        }

    except Exception as e:
        logger.error(f"识别支撑阻力位失败: {e}")
        return {'support': [], 'resistance': []}


def calculate_sr_strength(
    price_level: float,
    data: pd.DataFrame,
    lookback: int = 100
) -> int:
    """
    计算支撑/阻力位的强度（0-100分）

    Args:
        price_level: 价格水平
        data: 价格数据
        lookback: 回看周期

    Returns:
        强度评分（0-100）
    """
    try:
        strength_score = 0

        # 1. 触及次数（最高40分）
        touch_count = _count_touches(price_level, data, lookback)
        strength_score += min(touch_count * 10, 40)

        # 2. 时间跨度（最高20分）
        time_span_days = _get_time_span(price_level, data, lookback)
        if time_span_days > 180:
            strength_score += 20
        elif time_span_days > 90:
            strength_score += 15
        elif time_span_days > 30:
            strength_score += 10

        # 3. 成交量（最高20分）
        avg_volume = _get_average_volume_at_level(price_level, data, lookback)
        overall_avg = data['volume'].mean()
        if avg_volume > overall_avg * 2:
            strength_score += 20
        elif avg_volume > overall_avg * 1.5:
            strength_score += 15
        elif avg_volume > overall_avg:
            strength_score += 10

        # 4. 是否为整数关口（最高10分）
        if _is_round_number(price_level):
            strength_score += 10

        # 5. 是否为历史极值（最高10分）
        if _is_historical_extreme(price_level, data):
            strength_score += 10

        return min(strength_score, 100)

    except Exception as e:
        logger.error(f"计算支撑阻力强度失败: {e}")
        return 0


def detect_sr_flip(
    price_level: float,
    previous_role: str,
    data: pd.DataFrame
) -> Optional[Dict]:
    """
    检测支撑阻力转换

    Args:
        price_level: 价格水平
        previous_role: 之前的角色 ('support' 或 'resistance')
        data: 价格数据

    Returns:
        转换信号字典
    """
    try:
        current_price = data['close'].iloc[-1]

        if previous_role == 'support':
            # 原支撑位被跌破
            if current_price < price_level:
                # 价格从下方回测该位置
                if _is_approaching_from_below(price_level, data):
                    return {
                        'status': 'flipped_to_resistance',
                        'signal': 'short_opportunity',
                        'entry': price_level,
                        'confidence': 0.80,
                        'description': '支撑转阻力，做空机会'
                    }

        elif previous_role == 'resistance':
            # 原阻力位被突破
            if current_price > price_level:
                # 价格从上方回测该位置
                if _is_approaching_from_above(price_level, data):
                    return {
                        'status': 'flipped_to_support',
                        'signal': 'long_opportunity',
                        'entry': price_level,
                        'confidence': 0.80,
                        'description': '阻力转支撑，做多机会'
                    }

        return None

    except Exception as e:
        logger.error(f"检测支撑阻力转换失败: {e}")
        return None


# 辅助函数

def _deduplicate_levels(levels: List[Dict], threshold: float) -> List[Dict]:
    """去除重复的价格水平"""
    if not levels:
        return []

    unique_levels = []
    sorted_levels = sorted(levels, key=lambda x: x['price'])

    current_level = sorted_levels[0]
    for level in sorted_levels[1:]:
        if abs(level['price'] - current_level['price']) / current_level['price'] > threshold:
            unique_levels.append(current_level)
            current_level = level
        else:
            # 合并相近的水平，保留触及次数更多的
            if level['touches'] > current_level['touches']:
                current_level = level

    unique_levels.append(current_level)
    return unique_levels


def _count_touches(price_level: float, data: pd.DataFrame, lookback: int) -> int:
    """统计价格触及次数"""
    threshold = 0.02
    touches = 0

    recent_data = data.iloc[-lookback:]
    for _, row in recent_data.iterrows():
        if abs(row['low'] - price_level) / price_level < threshold or \
           abs(row['high'] - price_level) / price_level < threshold:
            touches += 1

    return touches


def _get_time_span(price_level: float, data: pd.DataFrame, lookback: int) -> int:
    """获取价格水平的时间跨度（天数）"""
    threshold = 0.02
    recent_data = data.iloc[-lookback:]

    first_touch = None
    last_touch = None

    for idx, row in recent_data.iterrows():
        if abs(row['low'] - price_level) / price_level < threshold or \
           abs(row['high'] - price_level) / price_level < threshold:
            if first_touch is None:
                first_touch = idx
            last_touch = idx

    if first_touch and last_touch:
        return (last_touch - first_touch).days
    return 0


def _get_average_volume_at_level(price_level: float, data: pd.DataFrame, lookback: int) -> float:
    """获取价格水平处的平均成交量"""
    threshold = 0.02
    volumes = []

    recent_data = data.iloc[-lookback:]
    for _, row in recent_data.iterrows():
        if abs(row['low'] - price_level) / price_level < threshold or \
           abs(row['high'] - price_level) / price_level < threshold:
            volumes.append(row['volume'])

    return np.mean(volumes) if volumes else 0


def _is_round_number(price: float) -> bool:
    """判断是否为整数关口"""
    round_levels = [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000]

    for level in round_levels:
        if abs(price - level) / level < 0.01:
            return True

    return False


def _is_historical_extreme(price: float, data: pd.DataFrame) -> bool:
    """判断是否为历史极值"""
    all_time_high = data['high'].max()
    all_time_low = data['low'].min()

    return abs(price - all_time_high) / all_time_high < 0.01 or \
           abs(price - all_time_low) / all_time_low < 0.01


def _is_approaching_from_below(price_level: float, data: pd.DataFrame) -> bool:
    """判断价格是否从下方接近"""
    recent_prices = data['close'].iloc[-5:]
    return all(p < price_level for p in recent_prices[:-1]) and \
           recent_prices.iloc[-1] >= price_level * 0.98


def _is_approaching_from_above(price_level: float, data: pd.DataFrame) -> bool:
    """判断价格是否从上方接近"""
    recent_prices = data['close'].iloc[-5:]
    return all(p > price_level for p in recent_prices[:-1]) and \
           recent_prices.iloc[-1] <= price_level * 1.02
