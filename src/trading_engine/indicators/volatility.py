"""
波动率指标计算模块
包括：Bollinger Bands, ATR, Standard Deviation, Keltner Channels
"""

import pandas as pd
import numpy as np
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def calculate_bollinger_bands(
    data: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0,
    price_col: str = 'close'
) -> Dict[str, pd.Series]:
    """
    计算布林带 (Bollinger Bands)

    Returns:
        包含upper, middle, lower的字典
    """
    try:
        # 中轨 = 简单移动平均
        middle = data[price_col].rolling(window=period).mean()

        # 标准差
        std = data[price_col].rolling(window=period).std()

        # 上轨和下轨
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        # 带宽
        bandwidth = (upper - lower) / middle * 100

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'bandwidth': bandwidth
        }
    except Exception as e:
        logger.error(f"计算Bollinger Bands失败: {e}")
        return {
            'upper': pd.Series(index=data.index, dtype=float),
            'middle': pd.Series(index=data.index, dtype=float),
            'lower': pd.Series(index=data.index, dtype=float),
            'bandwidth': pd.Series(index=data.index, dtype=float)
        }


def calculate_atr(
    data: pd.DataFrame,
    period: int = 14
) -> pd.Series:
    """
    计算真实波动幅度 (Average True Range)
    """
    try:
        high = data['high']
        low = data['low']
        close = data['close']

        # 计算TR
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR = TR的移动平均
        atr = tr.rolling(window=period).mean()

        return atr
    except Exception as e:
        logger.error(f"计算ATR失败: {e}")
        return pd.Series(index=data.index, dtype=float)


def calculate_standard_deviation(
    data: pd.DataFrame,
    period: int = 20,
    price_col: str = 'close'
) -> pd.Series:
    """
    计算标准差 (Standard Deviation)
    """
    try:
        return data[price_col].rolling(window=period).std()
    except Exception as e:
        logger.error(f"计算标准差失败: {e}")
        return pd.Series(index=data.index, dtype=float)


def calculate_keltner_channels(
    data: pd.DataFrame,
    period: int = 20,
    atr_period: int = 10,
    multiplier: float = 2.0
) -> Dict[str, pd.Series]:
    """
    计算肯特纳通道 (Keltner Channels)

    Returns:
        包含upper, middle, lower的字典
    """
    try:
        # 中线 = EMA
        middle = data['close'].ewm(span=period, adjust=False).mean()

        # ATR
        atr = calculate_atr(data, atr_period)

        # 上下轨
        upper = middle + (atr * multiplier)
        lower = middle - (atr * multiplier)

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }
    except Exception as e:
        logger.error(f"计算Keltner Channels失败: {e}")
        return {
            'upper': pd.Series(index=data.index, dtype=float),
            'middle': pd.Series(index=data.index, dtype=float),
            'lower': pd.Series(index=data.index, dtype=float)
        }
