"""
市场上下文构建器

将交易引擎的分析结果转为LLM可理解的结构化文本。
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from loguru import logger

from src.trading_engine.indicators import (
    calculate_ma, calculate_ema, calculate_rsi,
    calculate_macd, calculate_bollinger_bands,
    calculate_atr, calculate_adx,
)
from src.trading_engine.price_action import (
    identify_market_structure,
    identify_support_resistance,
    calculate_bull_bear_power,
    identify_pin_bar, identify_engulfing,
    identify_inside_bar, identify_doji,
    identify_hammer, identify_trend_bar,
)


def _safe_float(val, decimals: int = None) -> Optional[float]:
    """安全转换为float，保留原始精度；指定decimals时才做四舍五入"""
    if val is None:
        return None
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return None
        if decimals is not None:
            return round(f, decimals)
        return f
    except (TypeError, ValueError):
        return None


class ContextBuilder:
    """市场上下文构建器"""

    def build_market_context(
        self,
        symbol: str,
        interval: str,
        df: pd.DataFrame,
    ) -> str:
        """
        构建完整的市场上下文文本

        Args:
            symbol: 交易对
            interval: 时间周期
            df: K线数据DataFrame

        Returns:
            格式化的市场上下文文本
        """
        sections = []

        # 基本信息
        sections.append(self._build_price_section(symbol, interval, df))

        # 技术指标
        sections.append(self._build_indicators_section(df))

        # 市场结构
        sections.append(self._build_structure_section(df))

        # 支撑阻力
        sections.append(self._build_sr_section(df))

        # K线形态
        sections.append(self._build_patterns_section(df))

        # 多空力量
        sections.append(self._build_power_section(df))

        return "\n\n".join(s for s in sections if s)

    def _build_price_section(
        self, symbol: str, interval: str, df: pd.DataFrame
    ) -> str:
        """构建价格概览"""
        last = df.iloc[-1]
        prev = df.iloc[-2]
        o, h, l, c = (
            _safe_float(last["open"]),
            _safe_float(last["high"]),
            _safe_float(last["low"]),
            _safe_float(last["close"]),
        )
        vol = _safe_float(last["volume"], 2)
        change = _safe_float(
            (last["close"] - prev["close"]) / prev["close"] * 100, 2
        )

        return (
            f"## 价格概览\n"
            f"- 交易对: {symbol}\n"
            f"- 周期: {interval}\n"
            f"- 最新K线: 开{o} 高{h} 低{l} 收{c}\n"
            f"- 涨跌幅: {change}%\n"
            f"- 成交量: {vol}\n"
            f"- 数据量: {len(df)}根K线"
        )

    def _build_indicators_section(self, df: pd.DataFrame) -> str:
        """构建技术指标摘要"""
        lines = ["## 技术指标"]
        try:
            ma20 = _safe_float(calculate_ma(df, period=20).iloc[-1])
            ema20 = _safe_float(calculate_ema(df, period=20).iloc[-1])
            ma50 = _safe_float(calculate_ma(df, period=50).iloc[-1])
            lines.append(f"- MA20: {ma20}  |  EMA20: {ema20}  |  MA50: {ma50}")

            rsi = _safe_float(calculate_rsi(df, period=14).iloc[-1], 2)
            rsi_state = "超买" if rsi and rsi > 70 else ("超卖" if rsi and rsi < 30 else "中性")
            lines.append(f"- RSI(14): {rsi} ({rsi_state})")

            macd_data = calculate_macd(df)
            macd_val = _safe_float(macd_data["macd"].iloc[-1])
            signal_val = _safe_float(macd_data["signal"].iloc[-1])
            hist_val = _safe_float(macd_data["histogram"].iloc[-1])
            macd_cross = "金叉" if macd_val and signal_val and macd_val > signal_val else "死叉"
            lines.append(f"- MACD: {macd_val}  信号线: {signal_val}  柱状: {hist_val} ({macd_cross})")

            bb = calculate_bollinger_bands(df)
            bb_upper = _safe_float(bb["upper"].iloc[-1])
            bb_middle = _safe_float(bb["middle"].iloc[-1])
            bb_lower = _safe_float(bb["lower"].iloc[-1])
            lines.append(f"- 布林带: 上轨{bb_upper}  中轨{bb_middle}  下轨{bb_lower}")

            atr = _safe_float(calculate_atr(df).iloc[-1])
            lines.append(f"- ATR(14): {atr}")

            adx_data = calculate_adx(df)
            if isinstance(adx_data, dict):
                adx_val = _safe_float(adx_data.get("adx", pd.Series()).iloc[-1] if isinstance(adx_data.get("adx"), pd.Series) else adx_data.get("adx"), 2)
            else:
                adx_val = _safe_float(adx_data.iloc[-1] if hasattr(adx_data, "iloc") else None, 2)
            lines.append(f"- ADX: {adx_val}")
        except Exception as e:
            logger.warning(f"构建指标上下文失败: {e}")
            lines.append("- （部分指标计算失败）")

        return "\n".join(lines)

    def _build_structure_section(self, df: pd.DataFrame) -> str:
        """构建市场结构摘要"""
        lines = ["## 市场结构"]
        try:
            structure = identify_market_structure(df)
            if structure:
                trend = structure.get("trend", "未知")
                phase = structure.get("phase", "未知")
                lines.append(f"- 趋势方向: {trend}")
                lines.append(f"- 趋势阶段: {phase}")
                hh = structure.get("higher_highs", 0)
                hl = structure.get("higher_lows", 0)
                lh = structure.get("lower_highs", 0)
                ll = structure.get("lower_lows", 0)
                lines.append(f"- 摆动点: HH={hh} HL={hl} LH={lh} LL={ll}")
            else:
                lines.append("- 无法识别市场结构")
        except Exception as e:
            logger.warning(f"构建市场结构上下文失败: {e}")
            lines.append("- （市场结构分析失败）")
        return "\n".join(lines)

    def _build_sr_section(self, df: pd.DataFrame) -> str:
        """构建支撑阻力位摘要"""
        lines = ["## 支撑阻力位"]
        try:
            sr = identify_support_resistance(df)
            if sr:
                supports = sr.get("support", [])[:5]
                resistances = sr.get("resistance", [])[:5]
                if supports:
                    lines.append("- 支撑位:")
                    for s in supports:
                        price = _safe_float(s.get("price"))
                        touches = s.get("touches", 0)
                        lines.append(f"  - {price} (触及{touches}次)")
                if resistances:
                    lines.append("- 阻力位:")
                    for r in resistances:
                        price = _safe_float(r.get("price"))
                        touches = r.get("touches", 0)
                        lines.append(f"  - {price} (触及{touches}次)")
                if not supports and not resistances:
                    lines.append("- 未识别到明显支撑阻力位")
            else:
                lines.append("- 未识别到支撑阻力位")
        except Exception as e:
            logger.warning(f"构建支撑阻力上下文失败: {e}")
            lines.append("- （支撑阻力分析失败）")
        return "\n".join(lines)

    def _build_patterns_section(self, df: pd.DataFrame) -> str:
        """构建最近K线形态摘要"""
        lines = ["## K线形态（最近3根）"]
        try:
            detectors = [
                ("Pin Bar", identify_pin_bar),
                ("吞没形态", identify_engulfing),
                ("内包线", identify_inside_bar),
                ("十字星", identify_doji),
                ("锤子线", identify_hammer),
                ("趋势柱", identify_trend_bar),
            ]
            found = []
            for name, func in detectors:
                result = func(df)
                if result and result.get("type"):
                    conf = result.get("confidence", 0)
                    desc = result.get("description", "")
                    found.append(f"- {name}: 置信度{conf} - {desc}")

            if found:
                lines.extend(found)
            else:
                lines.append("- 最近K线未识别到显著形态")
        except Exception as e:
            logger.warning(f"构建K线形态上下文失败: {e}")
            lines.append("- （K线形态分析失败）")
        return "\n".join(lines)

    def _build_power_section(self, df: pd.DataFrame) -> str:
        """构建多空力量摘要"""
        lines = ["## 多空力量"]
        try:
            power = calculate_bull_bear_power(df)
            if power:
                bull = _safe_float(power.get("bull_power"), 2)
                bear = _safe_float(power.get("bear_power"), 2)
                ratio = _safe_float(power.get("ratio"), 2)
                dominant = power.get("dominant", "未知")
                lines.append(f"- 多头力量: {bull}")
                lines.append(f"- 空头力量: {bear}")
                lines.append(f"- 多空比: {ratio}")
                lines.append(f"- 主导方: {dominant}")
            else:
                lines.append("- 无法计算多空力量")
        except Exception as e:
            logger.warning(f"构建多空力量上下文失败: {e}")
            lines.append("- （多空力量分析失败）")
        return "\n".join(lines)
