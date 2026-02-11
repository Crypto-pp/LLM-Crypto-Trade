"""
技术分析API路由

通过 ccxt 获取真实K线数据，调用 trading_engine 计算指标和识别形态。
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from loguru import logger
import ccxt

from src.trading_engine.indicators import (
    calculate_ma, calculate_ema, calculate_macd,
    calculate_rsi, calculate_bollinger_bands,
)
from src.trading_engine.price_action import (
    identify_support_resistance,
    identify_market_structure,
)
from src.utils.math_utils import smart_round

router = APIRouter(tags=["technical_analysis"])

# 复用 market_data 的交易所配置
EXCHANGES = {
    "binance": ccxt.binance,
    "okx": ccxt.okx,
}


def _to_float(val) -> float:
    """将 numpy/pandas 数值转为原生 Python float，自动适配小价格精度"""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return 0.0
    return smart_round(float(val))


def _fetch_ohlcv_df(symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
    """从 Binance 获取K线数据并转为 DataFrame"""
    try:
        ex = EXCHANGES.get("binance")
        if not ex:
            raise ValueError("交易所不可用")
        exchange = ex({"enableRateLimit": True, "timeout": 15000})
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=interval, limit=limit)
        if not ohlcv:
            raise ValueError(f"未获取到 {symbol} 的K线数据")
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        return df
    except Exception as e:
        logger.error(f"获取K线数据失败: {symbol} {interval} - {e}")
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {e}")


def _sanitize_dict(obj):
    """递归将字典中的 numpy/pandas 类型转为原生 Python 类型"""
    if isinstance(obj, dict):
        return {k: _sanitize_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_dict(item) for item in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return smart_round(float(obj))
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return obj


@router.get("/indicators")
async def calculate_indicators(
    symbol: str = Query(..., description="交易对 (BTC/USDT)"),
    interval: str = Query("1h", description="时间周期"),
    indicators: List[str] = Query(..., description="指标列表"),
):
    """计算技术指标，使用真实交易所K线数据"""
    try:
        data = _fetch_ohlcv_df(symbol, interval, limit=200)
        results = {}

        for ind in indicators:
            if ind == "ma":
                series = calculate_ma(data, period=20)
                results["ma"] = _to_float(series.iloc[-1])
            elif ind == "ema":
                series = calculate_ema(data, period=20)
                results["ema"] = _to_float(series.iloc[-1])
            elif ind == "rsi":
                series = calculate_rsi(data, period=14)
                results["rsi"] = _to_float(series.iloc[-1])
            elif ind == "macd":
                macd = calculate_macd(data)
                results["macd"] = {
                    "macd": _to_float(macd["macd"].iloc[-1]),
                    "signal": _to_float(macd["signal"].iloc[-1]),
                    "histogram": _to_float(macd["histogram"].iloc[-1]),
                }
            elif ind == "bollinger":
                bb = calculate_bollinger_bands(data)
                results["bollinger"] = {
                    "upper": _to_float(bb["upper"].iloc[-1]),
                    "middle": _to_float(bb["middle"].iloc[-1]),
                    "lower": _to_float(bb["lower"].iloc[-1]),
                }

        return {
            "symbol": symbol,
            "interval": interval,
            "indicators": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns")
async def identify_patterns(
    symbol: str = Query(..., description="交易对"),
    interval: str = Query("1h", description="时间周期"),
):
    """识别价格行为模式，使用真实K线数据"""
    try:
        data = _fetch_ohlcv_df(symbol, interval, limit=200)
        structure = identify_market_structure(data)

        # 确保返回值可 JSON 序列化
        safe_structure = _sanitize_dict(structure) if structure else {}

        return {
            "symbol": symbol,
            "interval": interval,
            "market_structure": safe_structure,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"识别形态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/support-resistance")
async def get_support_resistance(
    symbol: str = Query(..., description="交易对"),
    interval: str = Query("1h", description="时间周期"),
):
    """获取支撑阻力位，使用真实K线数据"""
    try:
        data = _fetch_ohlcv_df(symbol, interval, limit=200)
        sr_levels = identify_support_resistance(data)

        if not sr_levels:
            return {
                "symbol": symbol,
                "interval": interval,
                "support_levels": [],
                "resistance_levels": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        supports = [
            {"price": _to_float(lv["price"]), "touches": int(lv["touches"])}
            for lv in sr_levels.get("support", [])[:5]
        ]
        resistances = [
            {"price": _to_float(lv["price"]), "touches": int(lv["touches"])}
            for lv in sr_levels.get("resistance", [])[:5]
        ]

        return {
            "symbol": symbol,
            "interval": interval,
            "support_levels": supports,
            "resistance_levels": resistances,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取支撑阻力位失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
