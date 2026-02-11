"""
AI辅助分析API路由

提供AI模型列表、提示词列表、分析（普通/流式）等接口。
"""

import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from loguru import logger
import pandas as pd
import ccxt

from src.config import get_settings
from src.ai_service.ai_analyzer import AIAnalyzer
from src.ai_service.config_manager import AIConfigManager

router = APIRouter(tags=["ai_analysis"])

_config_manager = AIConfigManager()

# 复用 exchange 实例，避免每次请求重新加载 exchangeInfo
_exchange = ccxt.binance({"enableRateLimit": True, "timeout": 30000})


class AnalyzeRequest(BaseModel):
    """AI分析请求体"""
    symbol: str
    interval: str = "1h"
    prompt_id: str = "comprehensive"
    provider: Optional[str] = None


class TestProviderRequest(BaseModel):
    """测试提供商连接请求体"""
    provider: str


def _get_analyzer() -> AIAnalyzer:
    """获取AI分析器实例（使用合并后的配置）"""
    settings = get_settings()
    effective = _config_manager.get_effective_settings(settings.ai)
    return AIAnalyzer(effective)


def _fetch_ohlcv_df(symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
    """从Binance获取K线数据"""
    try:
        ohlcv = _exchange.fetch_ohlcv(symbol, timeframe=interval, limit=limit)
        if not ohlcv:
            raise ValueError(f"未获取到 {symbol} 的K线数据")
        df = pd.DataFrame(
            ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        return df
    except Exception as e:
        logger.error(f"获取K线数据失败: {symbol} {interval} - {e}")
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {e}")


@router.get("/providers")
async def list_providers():
    """获取可用AI模型提供商列表"""
    try:
        analyzer = _get_analyzer()
        providers = analyzer.get_providers()
        return {"providers": providers, "total": len(providers)}
    except Exception as e:
        logger.error(f"获取AI提供商列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts")
async def list_prompts():
    """获取预设提示词列表"""
    try:
        analyzer = _get_analyzer()
        prompts = analyzer.get_prompts()
        return {"prompts": prompts, "total": len(prompts)}
    except Exception as e:
        logger.error(f"获取提示词列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """执行AI分析（普通响应）"""
    try:
        analyzer = _get_analyzer()
        df = _fetch_ohlcv_df(req.symbol, req.interval)

        result = await analyzer.analyze(
            symbol=req.symbol,
            interval=req.interval,
            prompt_id=req.prompt_id,
            df=df,
            provider=req.provider,
        )
        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"AI分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/stream")
async def analyze_stream(req: AnalyzeRequest):
    """执行AI分析（SSE流式响应）"""
    try:
        analyzer = _get_analyzer()
        df = _fetch_ohlcv_df(req.symbol, req.interval)

        async def event_generator():
            try:
                async for chunk in analyzer.analyze_stream(
                    symbol=req.symbol,
                    interval=req.interval,
                    prompt_id=req.prompt_id,
                    df=df,
                    provider=req.provider,
                ):
                    yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"AI流式分析失败: {e}")
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"AI流式分析初始化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config():
    """获取当前AI配置（API Key已脱敏）"""
    try:
        settings = get_settings()
        return _config_manager.get_config_response(settings.ai)
    except Exception as e:
        logger.error(f"获取AI配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_config(data: dict):
    """更新AI配置（持久化到JSON文件）"""
    try:
        settings = get_settings()
        _config_manager.save(data)
        return _config_manager.get_config_response(settings.ai)
    except Exception as e:
        logger.error(f"更新AI配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/test")
async def test_provider(req: TestProviderRequest):
    """测试指定提供商的连接"""
    try:
        settings = get_settings()
        result = await _config_manager.test_provider(req.provider, settings.ai)
        return result
    except Exception as e:
        logger.error(f"测试提供商连接失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
