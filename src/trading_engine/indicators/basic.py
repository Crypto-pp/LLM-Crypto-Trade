"""
基础技术指标计算模块
包括：MA, EMA, SMA, WMA, VWAP
"""

import pandas as pd
import numpy as np
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)


def calculate_ma(data: pd.DataFrame, period: int = 20, price_col: str = 'close') -> pd.Series:
    """
    计算简单移动平均线 (Moving Average)

    Args:
        data: 包含价格数据的DataFrame
        period: 周期
        price_col: 价格列名

    Returns:
        MA值的Series
    """
    try:
        return data[price_col].rolling(window=period).mean()
    except Exception as e:
        logger.error(f"计算MA失败: {e}")
        return pd.Series(index=data.index, dtype=float)


def calculate_sma(data: pd.DataFrame, period: int = 20, price_col: str = 'close') -> pd.Series:
    """
    计算简单移动平均线 (Simple Moving Average)
    与MA相同
    """
    return calculate_ma(data, period, price_col)


def calculate_ema(data: pd.DataFrame, period: int = 20, price_col: str = 'close') -> pd.Series:
    """
    计算指数移动平均线 (Exponential Moving Average)

    Args:
        data: 包含价格数据的DataFrame
        period: 周期
        price_col: 价格列名

    Returns:
        EMA值的Series
    """
    try:
        return data[price_col].ewm(span=period, adjust=False).mean()
    except Exception as e:
        logger.error(f"计算EMA失败: {e}")
        return pd.Series(index=data.index, dtype=float)


def calculate_wma(data: pd.DataFrame, period: int = 20, price_col: str = 'close') -> pd.Series:
    """
    计算加权移动平均线 (Weighted Moving Average)

    Args:
        data: 包含价格数据的DataFrame
        period: 周期
        price_col: 价格列名

    Returns:
        WMA值的Series
    """
    try:
        weights = np.arange(1, period + 1)

        def wma(prices):
            if len(prices) < period:
                return np.nan
            return np.dot(prices[-period:], weights) / weights.sum()

        return data[price_col].rolling(window=period).apply(wma, raw=True)
    except Exception as e:
        logger.error(f"计算WMA失败: {e}")
        return pd.Series(index=data.index, dtype=float)


def calculate_vwap(data: pd.DataFrame) -> pd.Series:
    """
    计算成交量加权平均价格 (Volume Weighted Average Price)

    Args:
        data: 包含价格和成交量数据的DataFrame

    Returns:
        VWAP值的Series
    """
    try:
        # 典型价格 = (最高价 + 最低价 + 收盘价) / 3
        typical_price = (data['high'] + data['low'] + data['close']) / 3

        # VWAP = Σ(典型价格 × 成交量) / Σ成交量
        vwap = (typical_price * data['volume']).cumsum() / data['volume'].cumsum()

        return vwap
    except Exception as e:
        logger.error(f"计算VWAP失败: {e}")
        return pd.Series(index=data.index, dtype=float)
