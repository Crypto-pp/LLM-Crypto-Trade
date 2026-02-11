"""
趋势指标计算模块
包括：MACD, ADX, Parabolic SAR, Ichimoku Cloud
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_macd(
    data: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    price_col: str = 'close'
) -> Dict[str, pd.Series]:
    """
    计算MACD指标 (Moving Average Convergence Divergence)

    Returns:
        包含macd, signal, histogram的字典
    """
    try:
        # 计算快速和慢速EMA
        ema_fast = data[price_col].ewm(span=fast_period, adjust=False).mean()
        ema_slow = data[price_col].ewm(span=slow_period, adjust=False).mean()

        # MACD线 = 快速EMA - 慢速EMA
        macd_line = ema_fast - ema_slow

        # 信号线 = MACD的EMA
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # 柱状图 = MACD - 信号线
        histogram = macd_line - signal_line

        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    except Exception as e:
        logger.error(f"计算MACD失败: {e}")
        return {
            'macd': pd.Series(index=data.index, dtype=float),
            'signal': pd.Series(index=data.index, dtype=float),
            'histogram': pd.Series(index=data.index, dtype=float)
        }


def calculate_adx(
    data: pd.DataFrame,
    period: int = 14
) -> Dict[str, pd.Series]:
    """
    计算ADX指标 (Average Directional Index)

    Returns:
        包含adx, plus_di, minus_di的字典
    """
    try:
        high = data['high']
        low = data['low']
        close = data['close']

        # 计算+DM和-DM
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        # 计算TR (True Range)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 计算ATR
        atr = tr.rolling(window=period).mean()

        # 计算+DI和-DI
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        # 计算DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)

        # 计算ADX
        adx = dx.rolling(window=period).mean()

        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        }
    except Exception as e:
        logger.error(f"计算ADX失败: {e}")
        return {
            'adx': pd.Series(index=data.index, dtype=float),
            'plus_di': pd.Series(index=data.index, dtype=float),
            'minus_di': pd.Series(index=data.index, dtype=float)
        }


def calculate_parabolic_sar(
    data: pd.DataFrame,
    af_start: float = 0.02,
    af_increment: float = 0.02,
    af_max: float = 0.2
) -> pd.Series:
    """
    计算抛物线转向指标 (Parabolic SAR)
    """
    try:
        high = data['high'].values
        low = data['low'].values

        sar = np.zeros(len(data))
        trend = np.zeros(len(data))
        af = np.zeros(len(data))
        ep = np.zeros(len(data))

        # 初始化
        sar[0] = low[0]
        trend[0] = 1  # 1=上升, -1=下降
        af[0] = af_start
        ep[0] = high[0]

        for i in range(1, len(data)):
            # 计算SAR
            sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])

            # 检查趋势反转
            if trend[i-1] == 1:  # 上升趋势
                if low[i] < sar[i]:
                    trend[i] = -1
                    sar[i] = ep[i-1]
                    ep[i] = low[i]
                    af[i] = af_start
                else:
                    trend[i] = 1
                    if high[i] > ep[i-1]:
                        ep[i] = high[i]
                        af[i] = min(af[i-1] + af_increment, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]
            else:  # 下降趋势
                if high[i] > sar[i]:
                    trend[i] = 1
                    sar[i] = ep[i-1]
                    ep[i] = high[i]
                    af[i] = af_start
                else:
                    trend[i] = -1
                    if low[i] < ep[i-1]:
                        ep[i] = low[i]
                        af[i] = min(af[i-1] + af_increment, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]

        return pd.Series(sar, index=data.index)
    except Exception as e:
        logger.error(f"计算Parabolic SAR失败: {e}")
        return pd.Series(index=data.index, dtype=float)


def calculate_ichimoku(
    data: pd.DataFrame,
    tenkan_period: int = 9,
    kijun_period: int = 26,
    senkou_b_period: int = 52,
    displacement: int = 26
) -> Dict[str, pd.Series]:
    """
    计算一目均衡表 (Ichimoku Cloud)

    Returns:
        包含tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span的字典
    """
    try:
        high = data['high']
        low = data['low']
        close = data['close']

        # 转换线 (Tenkan-sen) = (9日最高 + 9日最低) / 2
        tenkan_sen = (high.rolling(window=tenkan_period).max() +
                      low.rolling(window=tenkan_period).min()) / 2

        # 基准线 (Kijun-sen) = (26日最高 + 26日最低) / 2
        kijun_sen = (high.rolling(window=kijun_period).max() +
                     low.rolling(window=kijun_period).min()) / 2

        # 先行带A (Senkou Span A) = (转换线 + 基准线) / 2，向前位移26期
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)

        # 先行带B (Senkou Span B) = (52日最高 + 52日最低) / 2，向前位移26期
        senkou_span_b = ((high.rolling(window=senkou_b_period).max() +
                          low.rolling(window=senkou_b_period).min()) / 2).shift(displacement)

        # 迟行线 (Chikou Span) = 收盘价，向后位移26期
        chikou_span = close.shift(-displacement)

        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span
        }
    except Exception as e:
        logger.error(f"计算Ichimoku失败: {e}")
        return {
            'tenkan_sen': pd.Series(index=data.index, dtype=float),
            'kijun_sen': pd.Series(index=data.index, dtype=float),
            'senkou_span_a': pd.Series(index=data.index, dtype=float),
            'senkou_span_b': pd.Series(index=data.index, dtype=float),
            'chikou_span': pd.Series(index=data.index, dtype=float)
        }
