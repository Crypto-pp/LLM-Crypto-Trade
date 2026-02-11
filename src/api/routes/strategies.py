"""
策略API路由

通过 ccxt 获取真实K线数据，执行策略分析并返回交易信号。
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from loguru import logger
import ccxt

from src.trading_engine.strategies import (
    TrendFollowingStrategy,
    MeanReversionStrategy,
    MomentumStrategy,
)
from src.utils.math_utils import smart_round
from src.services.signal_store import SignalStore

router = APIRouter(tags=["strategies"])

_signal_store = SignalStore()


def _sanitize(obj):
    """递归将 numpy/pandas 类型转为原生 Python 类型"""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(item) for item in obj]
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        val = float(obj)
        return smart_round(val) if not np.isnan(val) else 0.0
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return obj


def _fetch_ohlcv_df(symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
    """从 Binance 获取K线数据并转为 DataFrame"""
    try:
        exchange = ccxt.binance({"enableRateLimit": True, "timeout": 15000})
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=interval, limit=limit)
        if not ohlcv:
            raise ValueError(f"未获取到 {symbol} 的K线数据")
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        return df
    except Exception as e:
        logger.error(f"获取K线数据失败: {symbol} {interval} - {e}")
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {e}")


@router.get("/strategies")
async def list_strategies():
    """获取策略列表"""
    strategies = [
        {
            "name": "趋势跟踪",
            "description": "基于MA/EMA和MACD的趋势跟踪策略",
            "parameters": {
                "short_ma": 20,
                "long_ma": 50,
                "adx_threshold": 25
            }
        },
        {
            "name": "均值回归",
            "description": "基于布林带和RSI的均值回归策略",
            "parameters": {
                "bb_period": 20,
                "rsi_oversold": 30,
                "rsi_overbought": 70
            }
        },
        {
            "name": "动量策略",
            "description": "追踪强势币种的动量策略",
            "parameters": {
                "momentum_period": 10,
                "roc_period": 12
            }
        }
    ]

    return {
        "strategies": strategies,
        "total": len(strategies)
    }


@router.post("/strategies/{strategy_name}/analyze")
async def analyze_strategy(
    strategy_name: str,
    symbol: str = Query(..., description="交易对"),
    interval: str = Query("1h", description="时间周期"),
):
    """执行策略分析，使用真实交易所K线数据"""
    try:
        strategies = {
            "趋势跟踪": TrendFollowingStrategy(),
            "均值回归": MeanReversionStrategy(),
            "动量策略": MomentumStrategy(),
        }

        if strategy_name not in strategies:
            raise HTTPException(status_code=404, detail="策略不存在")

        strategy = strategies[strategy_name]
        data = _fetch_ohlcv_df(symbol, interval, limit=200)

        analysis = strategy.analyze(data)
        signals = strategy.generate_signals(data, analysis)

        return _sanitize({
            "strategy": strategy_name,
            "symbol": symbol,
            "interval": interval,
            "analysis": analysis,
            "signals": signals,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"策略分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals")
async def get_signals(
    symbol: str = Query(None, description="交易对"),
    strategy: str = Query(None, description="策略名称"),
    limit: int = Query(10, description="返回数量")
):
    """获取交易信号（从 SignalStore 读取真实信号）"""
    try:
        signals = _signal_store.get_signals(
            symbol=symbol, strategy=strategy, limit=limit
        )
        return {
            "signals": signals,
            "total": len(signals)
        }

    except Exception as e:
        logger.error(f"获取信号失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
