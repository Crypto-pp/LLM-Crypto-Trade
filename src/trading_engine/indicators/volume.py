"""
成交量指标计算模块
包括：OBV, Volume Ratio, MFI, VWAP
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def calculate_obv(data: pd.DataFrame) -> pd.Series:
    """
    计算能量潮指标 (On Balance Volume)
    """
    try:
        close = data['close']
        volume = data['volume']

        obv = pd.Series(index=data.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]

        for i in range(1, len(data)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]

        return obv
    except Exception as e:
        logger.error(f"计算OBV失败: {e}")
        return pd.Series(index=data.index, dtype=float)


def calculate_volume_ratio(
    data: pd.DataFrame,
    period: int = 20
) -> pd.Series:
    """
    计算成交量比率 (Volume Ratio)
    """
    try:
        volume = data['volume']
        avg_volume = volume.rolling(window=period).mean()
        volume_ratio = volume / avg_volume

        return volume_ratio
    except Exception as e:
        logger.error(f"计算Volume Ratio失败: {e}")
        return pd.Series(index=data.index, dtype=float)


def calculate_mfi(
    data: pd.DataFrame,
    period: int = 14
) -> pd.Series:
    """
    计算资金流量指数 (Money Flow Index)
    """
    try:
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        money_flow = typical_price * data['volume']

        # 分离正负资金流
        positive_flow = pd.Series(0.0, index=data.index)
        negative_flow = pd.Series(0.0, index=data.index)

        for i in range(1, len(data)):
            if typical_price.iloc[i] > typical_price.iloc[i-1]:
                positive_flow.iloc[i] = money_flow.iloc[i]
            elif typical_price.iloc[i] < typical_price.iloc[i-1]:
                negative_flow.iloc[i] = money_flow.iloc[i]

        # 计算资金流比率
        positive_mf = positive_flow.rolling(window=period).sum()
        negative_mf = negative_flow.rolling(window=period).sum()

        mfi = 100 - (100 / (1 + positive_mf / negative_mf))

        return mfi
    except Exception as e:
        logger.error(f"计算MFI失败: {e}")
        return pd.Series(index=data.index, dtype=float)


def calculate_volume_vwap(data: pd.DataFrame) -> pd.Series:
    """
    计算成交量加权平均价格 (VWAP)
    与basic.py中的calculate_vwap相同
    """
    try:
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        vwap = (typical_price * data['volume']).cumsum() / data['volume'].cumsum()
        return vwap
    except Exception as e:
        logger.error(f"计算VWAP失败: {e}")
        return pd.Series(index=data.index, dtype=float)
