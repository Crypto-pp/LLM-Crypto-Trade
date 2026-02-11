"""
价格行为新模块单元测试

覆盖 breakout_analysis、bull_bear_power、retracement、reversal_patterns
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ========== 测试 Fixtures ==========


@pytest.fixture
def sample_ohlcv():
    """生成标准OHLCV测试数据（上升趋势）"""
    np.random.seed(42)
    n = 50
    dates = pd.date_range(start="2024-01-01", periods=n, freq="1h")

    base = 100.0
    closes = base + np.cumsum(np.random.normal(0.3, 1.0, n))
    opens = closes - np.random.uniform(-0.5, 0.5, n)
    highs = np.maximum(opens, closes) + np.random.uniform(0.2, 1.5, n)
    lows = np.minimum(opens, closes) - np.random.uniform(0.2, 1.5, n)
    volumes = np.random.uniform(1000, 10000, n)

    return pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    }, index=dates)


@pytest.fixture
def downtrend_data():
    """生成下降趋势测试数据"""
    np.random.seed(123)
    n = 50
    dates = pd.date_range(start="2024-01-01", periods=n, freq="1h")

    base = 200.0
    closes = base + np.cumsum(np.random.normal(-0.4, 0.8, n))
    opens = closes + np.random.uniform(-0.3, 0.3, n)
    highs = np.maximum(opens, closes) + np.random.uniform(0.1, 1.0, n)
    lows = np.minimum(opens, closes) - np.random.uniform(0.1, 1.0, n)
    volumes = np.random.uniform(800, 8000, n)

    return pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    }, index=dates)


@pytest.fixture
def consolidation_data():
    """生成窄幅盘整测试数据（用于压力蓄积检测）"""
    np.random.seed(99)
    n = 30
    dates = pd.date_range(start="2024-01-01", periods=n, freq="1h")

    base = 100.0
    closes = base + np.random.normal(0, 0.3, n)
    opens = closes + np.random.uniform(-0.2, 0.2, n)
    highs = np.maximum(opens, closes) + np.random.uniform(0.05, 0.3, n)
    lows = np.minimum(opens, closes) - np.random.uniform(0.05, 0.3, n)
    volumes = np.random.uniform(500, 5000, n)

    return pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    }, index=dates)


@pytest.fixture
def short_data():
    """生成不足长度的测试数据（用于边界条件测试）"""
    dates = pd.date_range(start="2024-01-01", periods=3, freq="1h")
    return pd.DataFrame({
        "open": [100, 101, 102],
        "high": [102, 103, 104],
        "low": [99, 100, 101],
        "close": [101, 102, 103],
        "volume": [1000, 1100, 1200],
    }, index=dates)


# ========== breakout_analysis 测试 ==========


class TestBreakoutAnalysis:
    """突破分析模块测试"""

    def test_breakout_pullback_rebreak_bullish(self, sample_ohlcv):
        """测试向上突破-回调-再突破识别"""
        from src.trading_engine.price_action.breakout_analysis import (
            identify_breakout_pullback_rebreak,
        )
        level = sample_ohlcv["close"].iloc[10]
        result = identify_breakout_pullback_rebreak(
            sample_ohlcv, level, lookback=30
        )
        if result is not None:
            assert result["type"] == "breakout_pullback_rebreak"
            assert result["direction"] in ("bullish", "bearish")
            assert 0 <= result["confidence"] <= 1.0

    def test_breakout_pullback_rebreak_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.breakout_analysis import (
            identify_breakout_pullback_rebreak,
        )
        result = identify_breakout_pullback_rebreak(
            short_data, 100.0, lookback=30
        )
        assert result is None

    def test_pressure_accumulation(self, consolidation_data):
        """测试压力蓄积检测"""
        from src.trading_engine.price_action.breakout_analysis import (
            detect_pressure_accumulation,
        )
        result = detect_pressure_accumulation(
            consolidation_data, lookback=20
        )
        if result is not None:
            assert result["type"] == "pressure_accumulation"
            assert result["upper_bound"] > result["lower_bound"]
            assert result["bias"] in ("bullish", "bearish", "neutral")

    def test_pressure_accumulation_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.breakout_analysis import (
            detect_pressure_accumulation,
        )
        result = detect_pressure_accumulation(short_data, lookback=20)
        assert result is None

    def test_assess_breakout_quality(self, sample_ohlcv):
        """测试突破质量评估"""
        from src.trading_engine.price_action.breakout_analysis import (
            assess_breakout_quality,
        )
        info = {"direction": "bullish", "level": 105.0}
        result = assess_breakout_quality(sample_ohlcv, info)
        if result is not None:
            assert result["type"] == "breakout_quality"
            assert result["quality"] in (
                "strong", "moderate", "weak", "failed"
            )
            assert isinstance(result["is_genuine"], bool)
            assert 0 <= result["total_score"] <= 100

    def test_assess_breakout_quality_missing_fields(self, sample_ohlcv):
        """测试缺少必要字段时返回 None"""
        from src.trading_engine.price_action.breakout_analysis import (
            assess_breakout_quality,
        )
        result = assess_breakout_quality(sample_ohlcv, {})
        assert result is None

    def test_breakout_entry(self, sample_ohlcv):
        """测试突破入场策略"""
        from src.trading_engine.price_action.breakout_analysis import (
            identify_breakout_entry,
        )
        info = {"direction": "bullish", "level": 105.0}
        result = identify_breakout_entry(sample_ohlcv, info)
        if result is not None:
            assert result["type"] == "breakout_entry"
            assert "entries" in result
            assert "recommended" in result
            assert len(result["entries"]) > 0

    def test_breakout_targets(self, sample_ohlcv):
        """测试突破目标位计算"""
        from src.trading_engine.price_action.breakout_analysis import (
            calculate_breakout_targets,
        )
        info = {"direction": "bullish", "level": 105.0}
        result = calculate_breakout_targets(sample_ohlcv, info)
        if result is not None:
            assert result["type"] == "breakout_targets"
            assert result["target_1"] > result["level"]
            assert result["target_2"] > result["target_1"]
            assert result["risk_reward_1"] >= 0

    def test_breakout_failure(self, sample_ohlcv):
        """测试突破失败检测"""
        from src.trading_engine.price_action.breakout_analysis import (
            detect_breakout_failure,
        )
        info = {"direction": "bullish", "level": 999.0}
        result = detect_breakout_failure(sample_ohlcv, info)
        # 价格远低于 level，不应检测到向上突破失败
        if result is not None:
            assert result["type"] == "breakout_failure"
            assert "signal" in result


# ========== bull_bear_power 测试 ==========


class TestBullBearPower:
    """多空力量分析模块测试"""

    def test_calculate_bull_bear_power(self, sample_ohlcv):
        """测试多空力量计算"""
        from src.trading_engine.price_action.bull_bear_power import (
            calculate_bull_bear_power,
        )
        result = calculate_bull_bear_power(sample_ohlcv, period=13)
        assert result is not None
        assert result["type"] == "bull_bear_power"
        assert "bull_power" in result
        assert "bear_power" in result
        assert "net_power" in result
        assert result["dominant"] in (
            "strong_bull", "bull", "bear", "strong_bear", "neutral"
        )

    def test_calculate_bull_bear_power_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.bull_bear_power import (
            calculate_bull_bear_power,
        )
        result = calculate_bull_bear_power(short_data, period=13)
        assert result is None

    def test_compare_bull_bear_strength(self, sample_ohlcv):
        """测试多空力量对比"""
        from src.trading_engine.price_action.bull_bear_power import (
            compare_bull_bear_strength,
        )
        result = compare_bull_bear_strength(sample_ohlcv, lookback=20)
        assert result is not None
        assert result["type"] == "bull_bear_comparison"
        assert 0 <= result["bull_ratio"] <= 1.0
        assert -100 <= result["score"] <= 100
        assert result["bias"] in ("bullish", "bearish", "neutral")

    def test_assess_trend_strength(self, sample_ohlcv):
        """测试趋势强度评估"""
        from src.trading_engine.price_action.bull_bear_power import (
            assess_trend_strength,
        )
        result = assess_trend_strength(sample_ohlcv, period=20)
        assert result is not None
        assert result["type"] == "trend_strength"
        assert result["direction"] in ("bullish", "bearish", "neutral")
        assert result["strength"] in (
            "very_strong", "strong", "moderate", "weak"
        )
        assert 0 <= result["total_score"] <= 100

    def test_assess_trend_strength_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.bull_bear_power import (
            assess_trend_strength,
        )
        result = assess_trend_strength(short_data, period=20)
        assert result is None

    def test_detect_bull_bear_transition(self, sample_ohlcv):
        """测试多空转换检测"""
        from src.trading_engine.price_action.bull_bear_power import (
            detect_bull_bear_transition,
        )
        result = detect_bull_bear_transition(sample_ohlcv)
        # 转换信号不一定出现，但不应抛出异常
        if result is not None:
            assert result["type"] == "bull_bear_transition"
            assert result["signal"] in ("buy", "sell")
            assert 0 <= result["confidence"] <= 1.0

    def test_detect_bull_bear_transition_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.bull_bear_power import (
            detect_bull_bear_transition,
        )
        result = detect_bull_bear_transition(short_data)
        assert result is None

    def test_calculate_comprehensive_power(self, sample_ohlcv):
        """测试综合力量评分"""
        from src.trading_engine.price_action.bull_bear_power import (
            calculate_comprehensive_power,
        )
        result = calculate_comprehensive_power(sample_ohlcv, period=20)
        assert result is not None
        assert result["type"] == "comprehensive_power"
        assert "final_score" in result
        assert "bull_bear_score" in result
        assert result["verdict"] in (
            "strong_bullish", "mild_bullish", "neutral",
            "mild_bearish", "strong_bearish"
        )
        assert result["signal"] in ("buy", "sell", "hold")


# ========== retracement 测试 ==========


class TestRetracement:
    """回调分析模块测试"""

    def test_identify_fibonacci_retracement_bullish(self, sample_ohlcv):
        """测试看涨斐波那契回调识别"""
        from src.trading_engine.price_action.retracement import (
            identify_fibonacci_retracement,
        )
        swing_low = float(sample_ohlcv["low"].min())
        swing_high = float(sample_ohlcv["high"].max())
        result = identify_fibonacci_retracement(
            sample_ohlcv, swing_high, swing_low, "bullish"
        )
        assert result is not None
        assert result["type"] == "fibonacci_retracement"
        assert result["direction"] == "bullish"
        assert "fib_levels" in result
        assert len(result["fib_levels"]) == 5
        assert 0 <= result["depth_pct"] <= 100

    def test_fibonacci_retracement_invalid_swing(self, sample_ohlcv):
        """测试摆动高低点无效时返回 None"""
        from src.trading_engine.price_action.retracement import (
            identify_fibonacci_retracement,
        )
        # swing_high <= swing_low 应返回 None
        result = identify_fibonacci_retracement(
            sample_ohlcv, 100.0, 200.0, "bullish"
        )
        assert result is None

    def test_assess_retracement_depth(self, sample_ohlcv):
        """测试回调深度评估"""
        from src.trading_engine.price_action.retracement import (
            assess_retracement_depth,
        )
        result = assess_retracement_depth(
            sample_ohlcv, "bullish", lookback=30
        )
        assert result is not None
        assert result["type"] == "retracement_depth"
        assert result["category"] in (
            "minimal", "shallow", "moderate", "deep", "very_deep"
        )
        assert 0 <= result["depth_pct"] <= 100

    def test_assess_retracement_depth_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.retracement import (
            assess_retracement_depth,
        )
        result = assess_retracement_depth(short_data, "bullish", lookback=30)
        assert result is None

    def test_calculate_retracement_entry(self, sample_ohlcv):
        """测试回调入场策略计算"""
        from src.trading_engine.price_action.retracement import (
            calculate_retracement_entry,
        )
        swing_low = float(sample_ohlcv["low"].min())
        swing_high = float(sample_ohlcv["high"].max())
        result = calculate_retracement_entry(
            sample_ohlcv, swing_high, swing_low, "bullish"
        )
        assert result is not None
        assert result["type"] == "retracement_entry"
        assert result["entry_level"] in ("fib_382", "fib_500", "fib_618")
        assert result["risk_reward"] >= 0
        assert len(result["all_entries"]) == 3

    def test_calculate_multi_level_targets(self, sample_ohlcv):
        """测试多级回调目标计算"""
        from src.trading_engine.price_action.retracement import (
            calculate_multi_level_targets,
        )
        swing_low = float(sample_ohlcv["low"].min())
        swing_high = float(sample_ohlcv["high"].max())
        result = calculate_multi_level_targets(
            sample_ohlcv, swing_high, swing_low, "bullish"
        )
        assert result is not None
        assert result["type"] == "multi_level_targets"
        assert len(result["retracement_targets"]) == 5
        assert len(result["extension_targets"]) == 5
        assert "take_profit" in result
        assert "tp1" in result["take_profit"]
        assert "tp2" in result["take_profit"]
        assert "tp3" in result["take_profit"]

    def test_multi_level_targets_invalid_swing(self, sample_ohlcv):
        """测试摆动高低点无效时返回 None"""
        from src.trading_engine.price_action.retracement import (
            calculate_multi_level_targets,
        )
        result = calculate_multi_level_targets(
            sample_ohlcv, 50.0, 200.0, "bullish"
        )
        assert result is None


# ========== reversal_patterns 测试 ==========


class TestReversalPatterns:
    """反转形态识别模块测试"""

    def test_check_reversal_conditions(self, sample_ohlcv):
        """测试反转条件检查"""
        from src.trading_engine.price_action.reversal_patterns import (
            check_reversal_conditions,
        )
        result = check_reversal_conditions(
            sample_ohlcv, "bullish", lookback=20
        )
        assert result is not None
        assert result["type"] == "reversal_conditions"
        assert result["readiness"] in ("high", "moderate", "low")
        assert 0 <= result["total_score"] <= 100
        assert isinstance(result["conditions_met"], list)

    def test_check_reversal_conditions_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.reversal_patterns import (
            check_reversal_conditions,
        )
        result = check_reversal_conditions(short_data, "bullish", lookback=20)
        assert result is None

    def test_identify_three_push_wedge(self, sample_ohlcv):
        """测试三推楔形识别"""
        from src.trading_engine.price_action.reversal_patterns import (
            identify_three_push_wedge,
        )
        result = identify_three_push_wedge(sample_ohlcv, lookback=30)
        # 三推楔形不一定出现，但不应抛出异常
        if result is not None:
            assert result["type"] == "three_push_wedge"
            assert result["signal"] in ("buy", "sell")
            assert 0 <= result["confidence"] <= 1.0

    def test_identify_climax_reversal(self, sample_ohlcv):
        """测试高潮反转识别"""
        from src.trading_engine.price_action.reversal_patterns import (
            identify_climax_reversal,
        )
        result = identify_climax_reversal(sample_ohlcv, lookback=20)
        # 高潮反转需要极端放量，随机数据不一定触发
        if result is not None:
            assert result["type"] == "climax_reversal"
            assert result["signal"] in ("buy", "sell")
            assert result["range_ratio"] >= 2.0
            assert result["volume_ratio"] >= 2.0

    def test_identify_ending_flag(self, sample_ohlcv):
        """测试末端旗形识别"""
        from src.trading_engine.price_action.reversal_patterns import (
            identify_ending_flag,
        )
        result = identify_ending_flag(sample_ohlcv, lookback=25)
        if result is not None:
            assert result["type"] == "ending_flag"
            assert result["signal"] in ("buy", "sell")
            assert 0 <= result["confidence"] <= 1.0

    def test_assess_reversal_probability(self, sample_ohlcv):
        """测试反转概率评估"""
        from src.trading_engine.price_action.reversal_patterns import (
            assess_reversal_probability,
        )
        result = assess_reversal_probability(
            sample_ohlcv, "bullish", lookback=30
        )
        assert result is not None
        assert result["type"] == "reversal_probability"
        assert 0 <= result["probability"] <= 1.0
        assert "signals_count" in result

    def test_assess_reversal_probability_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.reversal_patterns import (
            assess_reversal_probability,
        )
        result = assess_reversal_probability(
            short_data, "bullish", lookback=30
        )
        assert result is None

    def test_reversal_conditions_bearish(self, downtrend_data):
        """测试空头趋势下的反转条件检查"""
        from src.trading_engine.price_action.reversal_patterns import (
            check_reversal_conditions,
        )
        result = check_reversal_conditions(
            downtrend_data, "bearish", lookback=20
        )
        assert result is not None
        assert result["current_trend"] == "bearish"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ========== candlestick_patterns 新增功能测试 ==========


class TestCandlestickPatternsNew:
    """K线形态新增功能测试"""

    def test_identify_trend_bar_bullish(self):
        """测试看涨趋势K线识别"""
        from src.trading_engine.price_action.candlestick_patterns import (
            identify_trend_bar,
        )
        # 大阳线：实体占比高
        candle = pd.Series({
            "open": 100.0, "high": 110.5, "low": 99.5,
            "close": 110.0, "volume": 5000
        })
        result = identify_trend_bar(candle, threshold=0.6)
        assert result is not None
        assert result["type"] == "bullish_trend_bar"
        assert result["body_ratio"] > 0.6
        assert 0 < result["confidence"] <= 1.0

    def test_identify_trend_bar_bearish(self):
        """测试看跌趋势K线识别"""
        from src.trading_engine.price_action.candlestick_patterns import (
            identify_trend_bar,
        )
        candle = pd.Series({
            "open": 110.0, "high": 110.5, "low": 99.5,
            "close": 100.0, "volume": 5000
        })
        result = identify_trend_bar(candle, threshold=0.6)
        assert result is not None
        assert result["type"] == "bearish_trend_bar"

    def test_identify_trend_bar_small_body(self):
        """测试小实体K线不被识别为趋势K线"""
        from src.trading_engine.price_action.candlestick_patterns import (
            identify_trend_bar,
        )
        candle = pd.Series({
            "open": 100.0, "high": 105.0, "low": 95.0,
            "close": 100.5, "volume": 5000
        })
        result = identify_trend_bar(candle, threshold=0.6)
        assert result is None

    def test_detect_barbed_wire(self, consolidation_data):
        """测试铁丝网形态检测"""
        from src.trading_engine.price_action.candlestick_patterns import (
            detect_barbed_wire,
        )
        result = detect_barbed_wire(consolidation_data, lookback=6)
        # 盘整数据可能触发铁丝网
        if result is not None:
            assert result["type"] == "barbed_wire"
            assert result["bar_count"] == 6
            assert 0 < result["confidence"] <= 1.0

    def test_detect_barbed_wire_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.candlestick_patterns import (
            detect_barbed_wire,
        )
        result = detect_barbed_wire(short_data, lookback=10)
        assert result is None


# ========== retracement 新增功能测试 ==========


class TestRetracementNew:
    """回调分析新增功能测试"""

    def test_count_pullback_bars_bullish(self, sample_ohlcv):
        """测试看涨趋势中的回调K线统计"""
        from src.trading_engine.price_action.retracement import (
            count_pullback_bars,
        )
        result = count_pullback_bars(sample_ohlcv, "bullish", lookback=30)
        assert result is not None
        assert result["type"] == "bar_counting"
        assert result["direction"] == "bullish"
        assert result["count"] >= 0
        assert result["avg_count"] >= 0
        assert isinstance(result["is_exhausted"], bool)

    def test_count_pullback_bars_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.retracement import (
            count_pullback_bars,
        )
        result = count_pullback_bars(short_data, "bullish", lookback=30)
        assert result is None

    def test_identify_complex_pullback(self, sample_ohlcv):
        """测试复杂回调识别"""
        from src.trading_engine.price_action.retracement import (
            identify_complex_pullback,
        )
        result = identify_complex_pullback(sample_ohlcv, "bullish", lookback=40)
        if result is not None:
            assert result["type"] == "complex_pullback"
            assert result["legs_count"] >= 2
            assert result["pattern"] in (
                "two_leg_pullback", "three_leg_pullback", "trading_range"
            )
            assert 0 < result["confidence"] <= 1.0

    def test_identify_complex_pullback_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.retracement import (
            identify_complex_pullback,
        )
        result = identify_complex_pullback(short_data, "bullish", lookback=40)
        assert result is None

    def test_identify_abcd_pattern(self, sample_ohlcv):
        """测试AB=CD形态识别"""
        from src.trading_engine.price_action.retracement import (
            identify_abcd_pattern,
        )
        result = identify_abcd_pattern(sample_ohlcv, "bullish", lookback=40)
        # AB=CD形态不一定出现，但不应抛出异常
        if result is not None:
            assert result["type"] == "abcd_pattern"
            assert "points" in result
            assert "A" in result["points"]
            assert "B" in result["points"]
            assert "C" in result["points"]
            assert "D_projected" in result["points"]
            assert 0 < result["symmetry_ratio"] <= 1.5
            assert 0 < result["confidence"] <= 1.0

    def test_identify_abcd_pattern_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.retracement import (
            identify_abcd_pattern,
        )
        result = identify_abcd_pattern(short_data, "bullish", lookback=40)
        assert result is None


# ========== market_structure 新增功能测试 ==========


class TestMarketStructureNew:
    """市场结构新增功能测试"""

    def test_identify_trend_phase(self, sample_ohlcv):
        """测试趋势阶段判断"""
        from src.trading_engine.price_action.market_structure import (
            identify_trend_phase,
        )
        result = identify_trend_phase(sample_ohlcv, lookback=40)
        assert result is not None
        assert result["type"] == "trend_phase"
        assert result["phase"] in ("early", "middle", "late")
        assert result["trend_direction"] in ("bullish", "bearish")
        assert isinstance(result["characteristics"], list)
        assert len(result["characteristics"]) > 0
        assert 0 < result["confidence"] <= 1.0

    def test_identify_trend_phase_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.market_structure import (
            identify_trend_phase,
        )
        result = identify_trend_phase(short_data, lookback=50)
        assert result is None


# ========== trading_range 测试 ==========


class TestTradingRange:
    """交易区间模块测试"""

    def test_identify_trading_range(self, consolidation_data):
        """测试交易区间识别"""
        from src.trading_engine.price_action.trading_range import (
            identify_trading_range,
        )
        result = identify_trading_range(consolidation_data, lookback=20)
        if result is not None:
            assert result["type"] == "trading_range"
            assert result["upper_bound"] > result["lower_bound"]
            assert result["upper_touches"] >= 2
            assert result["lower_touches"] >= 2
            assert 0 < result["confidence"] <= 1.0

    def test_identify_trading_range_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.trading_range import (
            identify_trading_range,
        )
        result = identify_trading_range(short_data, lookback=50)
        assert result is None

    def test_assess_range_position(self, sample_ohlcv):
        """测试区间位置评估"""
        from src.trading_engine.price_action.trading_range import (
            assess_range_position,
        )
        upper = float(sample_ohlcv["high"].max())
        lower = float(sample_ohlcv["low"].min())
        result = assess_range_position(sample_ohlcv, upper, lower)
        assert result is not None
        assert result["type"] == "range_position"
        assert result["position"] in ("upper", "middle", "lower")
        assert result["bias"] in ("bullish", "bearish", "neutral")
        assert 0 <= result["relative_position"] <= 1.0

    def test_assess_range_position_invalid(self, sample_ohlcv):
        """测试无效边界时返回 None"""
        from src.trading_engine.price_action.trading_range import (
            assess_range_position,
        )
        result = assess_range_position(sample_ohlcv, 50.0, 100.0)
        assert result is None

    def test_detect_range_breakout(self, sample_ohlcv):
        """测试区间突破检测"""
        from src.trading_engine.price_action.trading_range import (
            detect_range_breakout,
        )
        # 设置一个低于当前价格的区间，应检测到向上突破
        lower = float(sample_ohlcv["low"].min())
        upper = lower + 2.0
        result = detect_range_breakout(sample_ohlcv, upper, lower, lookback=10)
        if result is not None:
            assert result["type"] == "range_breakout"
            assert result["direction"] in ("bullish", "bearish")
            assert isinstance(result["is_genuine"], bool)
            assert 0 < result["confidence"] <= 1.0

    def test_detect_range_breakout_no_break(self, sample_ohlcv):
        """测试价格在区间内时返回 None"""
        from src.trading_engine.price_action.trading_range import (
            detect_range_breakout,
        )
        # 设置一个包含当前价格的宽区间
        upper = float(sample_ohlcv["high"].max()) + 100
        lower = float(sample_ohlcv["low"].min()) - 100
        result = detect_range_breakout(sample_ohlcv, upper, lower, lookback=10)
        assert result is None


# ========== macd_auxiliary 测试 ==========


class TestMacdAuxiliary:
    """MACD辅助分析模块测试"""

    @pytest.fixture
    def macd_data(self):
        """生成足够长的MACD测试数据（需要26根预热）"""
        np.random.seed(77)
        n = 80
        dates = pd.date_range(start="2024-01-01", periods=n, freq="1h")
        base = 100.0
        closes = base + np.cumsum(np.random.normal(0.2, 1.0, n))
        opens = closes - np.random.uniform(-0.5, 0.5, n)
        highs = np.maximum(opens, closes) + np.random.uniform(0.2, 1.5, n)
        lows = np.minimum(opens, closes) - np.random.uniform(0.2, 1.5, n)
        volumes = np.random.uniform(1000, 10000, n)
        return pd.DataFrame({
            "open": opens, "high": highs, "low": lows,
            "close": closes, "volume": volumes,
        }, index=dates)

    def test_detect_macd_divergence(self, macd_data):
        """测试MACD背离检测"""
        from src.trading_engine.price_action.macd_auxiliary import (
            detect_macd_divergence,
        )
        result = detect_macd_divergence(macd_data, lookback=30)
        # 背离不一定出现，但不应抛出异常
        if result is not None:
            assert result["type"] == "macd_divergence"
            assert result["divergence_type"] in ("bullish", "bearish")
            assert 0 < result["confidence"] <= 1.0

    def test_detect_macd_divergence_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.macd_auxiliary import (
            detect_macd_divergence,
        )
        result = detect_macd_divergence(short_data, lookback=30)
        assert result is None

    def test_confirm_trend_with_macd(self, macd_data):
        """测试MACD趋势确认"""
        from src.trading_engine.price_action.macd_auxiliary import (
            confirm_trend_with_macd,
        )
        result = confirm_trend_with_macd(macd_data)
        assert result is not None
        assert result["type"] == "macd_trend_confirmation"
        assert result["trend"] in ("bullish", "bearish", "neutral")
        assert isinstance(result["macd_above_signal"], bool)
        assert result["histogram_trend"] in (
            "strengthening", "weakening", "mixed", "insufficient_data"
        )
        assert 0 < result["confidence"] <= 1.0

    def test_confirm_trend_with_macd_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.macd_auxiliary import (
            confirm_trend_with_macd,
        )
        result = confirm_trend_with_macd(short_data)
        assert result is None

    def test_detect_macd_momentum_shift(self, macd_data):
        """测试MACD动能转换检测"""
        from src.trading_engine.price_action.macd_auxiliary import (
            detect_macd_momentum_shift,
        )
        result = detect_macd_momentum_shift(macd_data, lookback=20)
        # 动能转换不一定出现，但不应抛出异常
        if result is not None:
            assert result["type"] == "macd_momentum_shift"
            assert result["shift_type"] in (
                "bearish_to_bullish", "bullish_to_bearish",
                "bullish_weakening", "bearish_weakening"
            )
            assert isinstance(result["zero_cross"], bool)
            assert 0 < result["confidence"] <= 1.0

    def test_detect_macd_momentum_shift_short_data(self, short_data):
        """测试数据不足时返回 None"""
        from src.trading_engine.price_action.macd_auxiliary import (
            detect_macd_momentum_shift,
        )
        result = detect_macd_momentum_shift(short_data, lookback=20)
        assert result is None
