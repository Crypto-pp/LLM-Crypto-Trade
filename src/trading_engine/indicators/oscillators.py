"""
震荡指标计算模块
包括：RSI, Stochastic, CCI, Williams %R
"""

import pandas as pd
import numpy as np
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def calculate_rsi(
    data: pd.DataFrame,
    period: int = 14,
    price_col: str = 'close'
) -> pd.Series:
    """
    计算相对强弱指数 (Relative Strength Index)

    Args:
        data: 价格数据
        period: 周期，默认14
        price_col: 价格列名

    Returns:
        RSI值的Series
    """
    try:
        delta = data[price_col].diff()

        # 分离涨跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 计算平均涨跌幅
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi
    except Exception as e:
        logger.error(f"计算RSI失败: {e}")
        return pd.Series(index=data.index, dtype=float)


def calculate_stochastic(
    data: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3,
    smooth_k: int = 3
) -> Dict[str, pd.Series]:
    """
    计算随机指标 (Stochastic Oscillator)

    Returns:
        包含k和d的字典
    """
    try:
        high = data['high']
        low = data['low']
        close = data['close']

        # 计算最高价和最低价
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        # 计算%K
        k = 100 * (close - lowest_low) / (highest_high - lowest_low)

        # 平滑%K
        if smooth_k > 1:
            k = k.rolling(window=smooth_k).mean()

        # 计算%D (K的移动平均)
        d = k.rolling(window=d_period).mean()

        return {
            'k': k,
            'd': d
        }
    except Exception as e:
        logger.error(f"计算Stochastic失败: {e}")
        return {
            'k': pd.Series(index=data.index, dtype=float),
            'd': pd.Series(index=data.index, dtype=float)
        }


def calculate_cci(
    data: pd.DataFrame,
    period: int = 20
) -> pd.Series:
    """
    计算商品通道指数 (Commodity Channel Index)
    """
    try:
        # 典型价格
        tp = (data['high'] + data['low'] + data['close']) / 3

        # 移动平均
        ma = tp.rolling(window=period).mean()

        # 平均偏差
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())

        # CCI
        cci = (tp - ma) / (0.015 * mad)

        return cci
    except Exception as e:
        logger.error(f"计算CCI失败: {e}")
        return pd.Series(index=data.index, dtype=float)


def calculate_williams_r(
    data: pd.DataFrame,
    period: int = 14
) -> pd.Series:
    """
    计算威廉指标 (Williams %R)
    """
    try:
        high = data['high']
        low = data['low']
        close = data['close']

        # 计算最高价和最低价
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()

        # Williams %R
        williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)

        return williams_r
    except Exception as e:
        logger.error(f"计算Williams %R失败: {e}")
        return pd.Series(index=data.index, dtype=float)
