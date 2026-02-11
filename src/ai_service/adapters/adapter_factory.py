"""
AI模型适配器工厂

根据提供商名称创建对应的适配器实例。
"""

from typing import List, Dict
from loguru import logger

from .base import BaseModelAdapter
from .deepseek import DeepSeekAdapter
from .gemini import GeminiAdapter
from .openai_compatible import OpenAICompatibleAdapter


def get_adapter(provider: str, settings) -> BaseModelAdapter:
    """
    根据提供商创建适配器

    Args:
        provider: 提供商名称 (deepseek/gemini/openai)
        settings: AISettings配置对象
    """
    if provider == "deepseek":
        if not settings.deepseek_api_key:
            raise ValueError("未配置 AI_DEEPSEEK_API_KEY")
        return DeepSeekAdapter(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            timeout=settings.timeout,
        )

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("未配置 AI_GEMINI_API_KEY")
        return GeminiAdapter(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            timeout=settings.timeout,
        )

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("未配置 AI_OPENAI_API_KEY")
        return OpenAICompatibleAdapter(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            timeout=settings.timeout,
            provider_name="openai",
        )

    raise ValueError(f"不支持的AI提供商: {provider}")


def get_available_providers(settings) -> List[Dict]:
    """获取已配置API Key的可用提供商列表"""
    providers = []

    if settings.deepseek_api_key:
        providers.append({
            "id": "deepseek",
            "name": "DeepSeek",
            "model": settings.deepseek_model,
            "enabled": True,
        })

    if settings.gemini_api_key:
        providers.append({
            "id": "gemini",
            "name": "Google Gemini",
            "model": settings.gemini_model,
            "enabled": True,
        })

    if settings.openai_api_key:
        providers.append({
            "id": "openai",
            "name": "OpenAI",
            "model": settings.openai_model,
            "enabled": True,
        })

    return providers
