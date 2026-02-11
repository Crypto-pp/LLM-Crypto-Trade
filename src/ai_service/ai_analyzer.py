"""
AI分析器

核心编排模块，协调适配器、上下文构建器和提示词管理器完成AI分析。
"""

import pandas as pd
from typing import Dict, AsyncGenerator, Optional
from datetime import datetime, timezone
from loguru import logger

from .adapters import get_adapter, get_available_providers
from .context_builder import ContextBuilder
from .prompts.prompt_manager import PromptManager


class AIAnalyzer:
    """AI分析器"""

    def __init__(self, settings):
        """
        Args:
            settings: AISettings配置对象
        """
        self.settings = settings
        self.context_builder = ContextBuilder()
        self.prompt_manager = PromptManager()

    async def analyze(
        self,
        symbol: str,
        interval: str,
        prompt_id: str,
        df: pd.DataFrame,
        provider: Optional[str] = None,
    ) -> Dict:
        """
        执行AI分析（普通响应）

        Args:
            symbol: 交易对
            interval: 时间周期
            prompt_id: 提示词模板ID
            df: K线数据
            provider: AI提供商（默认使用配置中的默认值）
        """
        provider = provider or self.settings.default_provider
        adapter = get_adapter(provider, self.settings)

        # 构建市场上下文
        market_context = self.context_builder.build_market_context(
            symbol, interval, df
        )

        # 构建消息
        messages = self.prompt_manager.build_messages(
            prompt_id, symbol, interval, market_context
        )

        # 调用AI
        logger.info(f"AI分析请求: {provider}/{adapter.get_model_name()} "
                     f"symbol={symbol} prompt={prompt_id}")
        analysis_text = await adapter.chat(messages, stream=False)

        return {
            "symbol": symbol,
            "interval": interval,
            "provider": provider,
            "model": adapter.get_model_name(),
            "prompt_id": prompt_id,
            "analysis": analysis_text,
            "market_context_summary": market_context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def analyze_stream(
        self,
        symbol: str,
        interval: str,
        prompt_id: str,
        df: pd.DataFrame,
        provider: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        执行AI分析（流式响应）

        返回异步生成器，逐步产出分析文本片段。
        """
        provider = provider or self.settings.default_provider
        adapter = get_adapter(provider, self.settings)

        market_context = self.context_builder.build_market_context(
            symbol, interval, df
        )
        messages = self.prompt_manager.build_messages(
            prompt_id, symbol, interval, market_context
        )

        logger.info(f"AI流式分析请求: {provider}/{adapter.get_model_name()} "
                     f"symbol={symbol} prompt={prompt_id}")

        stream = await adapter.chat(messages, stream=True)
        async for chunk in stream:
            yield chunk

    def get_providers(self) -> list:
        """获取可用AI提供商列表"""
        return get_available_providers(self.settings)

    def get_prompts(self) -> list:
        """获取可用提示词列表"""
        return self.prompt_manager.list_prompts()
