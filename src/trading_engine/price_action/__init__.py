"""
价格行为识别模块
"""

from .candlestick_patterns import (
    identify_pin_bar,
    identify_engulfing,
    identify_inside_bar,
    identify_outside_bar,
    identify_doji,
    identify_hammer,
    identify_trend_bar,
    detect_barbed_wire
)

from .chart_patterns import (
    identify_double_top_bottom,
    identify_head_shoulders,
    identify_triangle,
    identify_flag
)

from .support_resistance import (
    identify_support_resistance,
    calculate_sr_strength,
    detect_sr_flip
)

from .trendline import (
    draw_trendline,
    identify_channel,
    detect_trendline_break
)

from .market_structure import (
    identify_market_structure,
    detect_structure_break,
    find_swing_highs_lows,
    identify_trend_phase
)

from .breakout_analysis import (
    identify_breakout_pullback_rebreak,
    detect_pressure_accumulation,
    assess_breakout_quality,
    identify_breakout_entry,
    calculate_breakout_targets,
    detect_breakout_failure
)

from .bull_bear_power import (
    calculate_bull_bear_power,
    compare_bull_bear_strength,
    assess_trend_strength,
    detect_bull_bear_transition,
    calculate_comprehensive_power
)

from .retracement import (
    identify_fibonacci_retracement,
    assess_retracement_depth,
    calculate_retracement_entry,
    calculate_multi_level_targets,
    count_pullback_bars,
    identify_complex_pullback,
    identify_abcd_pattern
)

from .reversal_patterns import (
    check_reversal_conditions,
    identify_three_push_wedge,
    identify_climax_reversal,
    identify_ending_flag,
    assess_reversal_probability
)

from .trading_range import (
    identify_trading_range,
    assess_range_position,
    detect_range_breakout
)

from .macd_auxiliary import (
    detect_macd_divergence,
    confirm_trend_with_macd,
    detect_macd_momentum_shift
)

__all__ = [
    # Candlestick patterns
    'identify_pin_bar',
    'identify_engulfing',
    'identify_inside_bar',
    'identify_outside_bar',
    'identify_doji',
    'identify_hammer',
    'identify_trend_bar',
    'detect_barbed_wire',

    # Chart patterns
    'identify_double_top_bottom',
    'identify_head_shoulders',
    'identify_triangle',
    'identify_flag',

    # Support/Resistance
    'identify_support_resistance',
    'calculate_sr_strength',
    'detect_sr_flip',

    # Trendline
    'draw_trendline',
    'identify_channel',
    'detect_trendline_break',

    # Market structure
    'identify_market_structure',
    'detect_structure_break',
    'find_swing_highs_lows',
    'identify_trend_phase',

    # Breakout analysis
    'identify_breakout_pullback_rebreak',
    'detect_pressure_accumulation',
    'assess_breakout_quality',
    'identify_breakout_entry',
    'calculate_breakout_targets',
    'detect_breakout_failure',

    # Bull/Bear power
    'calculate_bull_bear_power',
    'compare_bull_bear_strength',
    'assess_trend_strength',
    'detect_bull_bear_transition',
    'calculate_comprehensive_power',

    # Retracement
    'identify_fibonacci_retracement',
    'assess_retracement_depth',
    'calculate_retracement_entry',
    'calculate_multi_level_targets',
    'count_pullback_bars',
    'identify_complex_pullback',
    'identify_abcd_pattern',

    # Reversal patterns
    'check_reversal_conditions',
    'identify_three_push_wedge',
    'identify_climax_reversal',
    'identify_ending_flag',
    'assess_reversal_probability',

    # Trading range
    'identify_trading_range',
    'assess_range_position',
    'detect_range_breakout',

    # MACD auxiliary
    'detect_macd_divergence',
    'confirm_trend_with_macd',
    'detect_macd_momentum_shift',
]
