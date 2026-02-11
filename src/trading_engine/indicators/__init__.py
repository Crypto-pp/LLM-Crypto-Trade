"""
技术指标计算模块
"""

from .basic import (
    calculate_ma,
    calculate_ema,
    calculate_sma,
    calculate_wma,
    calculate_vwap
)

from .trend import (
    calculate_macd,
    calculate_adx,
    calculate_parabolic_sar,
    calculate_ichimoku
)

from .oscillators import (
    calculate_rsi,
    calculate_stochastic,
    calculate_cci,
    calculate_williams_r
)

from .volatility import (
    calculate_bollinger_bands,
    calculate_atr,
    calculate_standard_deviation,
    calculate_keltner_channels
)

from .volume import (
    calculate_obv,
    calculate_volume_ratio,
    calculate_mfi,
    calculate_volume_vwap
)

from .indicator_manager import IndicatorManager

__all__ = [
    # Basic
    'calculate_ma',
    'calculate_ema',
    'calculate_sma',
    'calculate_wma',
    'calculate_vwap',

    # Trend
    'calculate_macd',
    'calculate_adx',
    'calculate_parabolic_sar',
    'calculate_ichimoku',

    # Oscillators
    'calculate_rsi',
    'calculate_stochastic',
    'calculate_cci',
    'calculate_williams_r',

    # Volatility
    'calculate_bollinger_bands',
    'calculate_atr',
    'calculate_standard_deviation',
    'calculate_keltner_channels',

    # Volume
    'calculate_obv',
    'calculate_volume_ratio',
    'calculate_mfi',
    'calculate_volume_vwap',

    # Manager
    'IndicatorManager',
]
