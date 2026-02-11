"""
市场数据API路由

通过 ccxt 直接从交易所获取实时行情和K线数据。
"""

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from loguru import logger
import time
import ccxt

router = APIRouter(tags=["market_data"])

# 支持的交易所映射
EXCHANGES = {
    "binance": {"name": "Binance", "class": ccxt.binance, "enabled": True},
    "okx": {"name": "OKX", "class": ccxt.okx, "enabled": True},
}


def _get_exchange(exchange_id: str) -> ccxt.Exchange:
    """获取交易所实例"""
    info = EXCHANGES.get(exchange_id)
    if not info or not info["enabled"]:
        raise HTTPException(status_code=400, detail=f"不支持的交易所: {exchange_id}")
    return info["class"]({"enableRateLimit": True, "timeout": 10000})


# 交易对缓存：{cache_key: {"symbols": [...], "ts": timestamp}}
_symbols_cache: Dict[str, Any] = {}
_CACHE_TTL = 3600  # 缓存1小时


def _load_exchange_usdt_symbols(exchange_id: str) -> List[str]:
    """加载指定交易所的USDT现货交易对"""
    cache_key = f"symbols_{exchange_id}"
    cached = _symbols_cache.get(cache_key)
    if cached and (time.time() - cached["ts"]) < _CACHE_TTL:
        return cached["symbols"]

    try:
        ex = _get_exchange(exchange_id)
        ex.load_markets()
        symbols = sorted([
            s for s in ex.symbols
            if s.endswith("/USDT") and ex.markets[s].get("spot", True)
        ])
        _symbols_cache[cache_key] = {"symbols": symbols, "ts": time.time()}
        logger.info(f"已加载 {exchange_id} 交易对: {len(symbols)} 个")
        return symbols
    except Exception as e:
        logger.error(f"加载 {exchange_id} 交易对失败: {e}")
        return []


def _load_all_usdt_symbols() -> List[str]:
    """合并所有交易所的USDT交易对（去重排序）"""
    cache_key = "symbols_all"
    cached = _symbols_cache.get(cache_key)
    if cached and (time.time() - cached["ts"]) < _CACHE_TTL:
        return cached["symbols"]

    all_symbols: set = set()
    for eid, info in EXCHANGES.items():
        if info["enabled"]:
            all_symbols.update(_load_exchange_usdt_symbols(eid))

    symbols = sorted(all_symbols)
    _symbols_cache[cache_key] = {"symbols": symbols, "ts": time.time()}
    logger.info(f"合并全部交易对: {len(symbols)} 个")
    return symbols


@router.get("/klines")
async def get_klines(
    exchange: str = Query(..., description="交易所ID (binance, okx等)"),
    symbol: str = Query(..., description="交易对 (BTC/USDT)"),
    interval: str = Query(..., description="时间周期 (1m, 5m, 1h, 1d等)"),
    limit: int = Query(500, ge=1, le=1000, description="返回数量限制"),
):
    """获取K线数据"""
    try:
        ex = _get_exchange(exchange)
        ohlcv = ex.fetch_ohlcv(symbol, timeframe=interval, limit=limit)

        klines = [
            {
                "timestamp": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).isoformat(),
                "open": str(k[1]),
                "high": str(k[2]),
                "low": str(k[3]),
                "close": str(k[4]),
                "volume": str(k[5]),
                "quote_volume": None,
                "trades_count": None,
            }
            for k in ohlcv
        ]

        return {"klines": klines, "total": len(klines)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker")
async def get_ticker(
    exchange: str = Query(..., description="交易所ID"),
    symbol: str = Query(..., description="交易对"),
):
    """获取最新价格信息"""
    try:
        ex = _get_exchange(exchange)
        t = ex.fetch_ticker(symbol)

        return {
            "ticker": {
                "exchange": exchange,
                "symbol": t.get("symbol", symbol),
                "last_price": str(t.get("last", 0)),
                "bid_price": str(t["bid"]) if t.get("bid") else None,
                "ask_price": str(t["ask"]) if t.get("ask") else None,
                "volume_24h": str(t["baseVolume"]) if t.get("baseVolume") else None,
                "price_change_24h": str(t["percentage"]) if t.get("percentage") else None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbols")
async def get_symbols(
    exchange: Optional[str] = Query(None, description="交易所ID（可选，不传则合并全部交易所）"),
):
    """获取支持的交易对列表（USDT现货，带缓存）"""
    try:
        if exchange:
            symbols = _load_exchange_usdt_symbols(exchange)
        else:
            symbols = _load_all_usdt_symbols()

        return {"symbols": symbols, "count": len(symbols)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取交易对列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchanges")
async def get_exchanges():
    """获取支持的交易所列表"""
    exchanges = [
        {"id": eid, "name": info["name"], "enabled": info["enabled"]}
        for eid, info in EXCHANGES.items()
    ]
    return {"exchanges": exchanges, "count": len(exchanges)}
