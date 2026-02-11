"""
AI配置管理器

管理AI提供商的运行时配置，支持JSON文件持久化。
配置合并逻辑：环境变量(AISettings)作为默认值，JSON文件作为用户覆盖层。
"""

import json
import os
from typing import Dict, Optional, Any
from loguru import logger


# AI配置字段定义
AI_CONFIG_FIELDS = [
    "default_provider",
    "deepseek_api_key", "deepseek_base_url", "deepseek_model",
    "gemini_api_key", "gemini_model",
    "openai_api_key", "openai_base_url", "openai_model",
    "max_tokens", "temperature", "timeout",
]

# API Key字段列表
API_KEY_FIELDS = ["deepseek_api_key", "gemini_api_key", "openai_api_key"]

# 提供商元数据
PROVIDER_META = {
    "deepseek": {
        "name": "DeepSeek",
        "key_field": "deepseek_api_key",
        "fields": ["deepseek_api_key", "deepseek_base_url", "deepseek_model"],
    },
    "gemini": {
        "name": "Google Gemini",
        "key_field": "gemini_api_key",
        "fields": ["gemini_api_key", "gemini_model"],
    },
    "openai": {
        "name": "OpenAI",
        "key_field": "openai_api_key",
        "fields": ["openai_api_key", "openai_base_url", "openai_model"],
    },
}


def mask_key(key: str) -> str:
    """API Key脱敏：前4位+****+后4位"""
    if not key or len(key) < 8:
        return ""
    return f"{key[:4]}****{key[-4:]}"


def _is_masked(value: str) -> bool:
    """判断值是否为脱敏后的API Key"""
    return "****" in str(value)


class AIConfigManager:
    """
    AI配置管理器

    合并环境变量默认值与JSON文件用户配置，JSON优先级更高。
    """

    def __init__(self, config_path: str = "data/ai_config.json"):
        self._config_path = config_path

    def _read_json(self) -> Dict[str, Any]:
        """读取JSON配置文件，不存在则返回空字典"""
        if not os.path.exists(self._config_path):
            return {}
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"读取AI配置文件失败: {e}")
            return {}

    def _write_json(self, data: Dict[str, Any]) -> None:
        """写入JSON配置文件"""
        os.makedirs(os.path.dirname(self._config_path) or ".", exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, env_settings) -> Dict[str, Any]:
        """
        加载合并后的配置

        Args:
            env_settings: AISettings 环境变量配置对象

        Returns:
            合并后的完整配置字典（JSON覆盖环境变量）
        """
        # 从环境变量提取默认值
        defaults = {}
        for field in AI_CONFIG_FIELDS:
            defaults[field] = getattr(env_settings, field, "")

        # 读取JSON覆盖层
        overrides = self._read_json()

        # 合并：JSON优先
        merged = {**defaults}
        for key, value in overrides.items():
            if key in AI_CONFIG_FIELDS and value is not None:
                merged[key] = value

        return merged

    def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        保存配置到JSON文件

        含 **** 的API Key值自动跳过（视为未修改）。
        只保存已知字段，忽略未知字段。

        Returns:
            保存后的JSON文件内容
        """
        current = self._read_json()

        for key, value in data.items():
            if key not in AI_CONFIG_FIELDS:
                continue
            # API Key脱敏值跳过
            if key in API_KEY_FIELDS and _is_masked(value):
                continue
            current[key] = value

        self._write_json(current)
        return current

    def get_config_response(self, env_settings) -> Dict[str, Any]:
        """
        获取前端展示用的配置响应（API Key已脱敏）

        Returns:
            结构化配置字典，包含 default_provider / providers / general
        """
        merged = self.load(env_settings)

        providers = {}
        for pid, meta in PROVIDER_META.items():
            key_field = meta["key_field"]
            raw_key = merged.get(key_field, "")
            provider_info: Dict[str, Any] = {
                "api_key": mask_key(raw_key),
                "model": merged.get(f"{pid}_model", ""),
                "has_key": bool(raw_key),
            }
            # 有 base_url 字段的提供商才返回
            base_url_field = f"{pid}_base_url"
            if base_url_field in AI_CONFIG_FIELDS:
                provider_info["base_url"] = merged.get(base_url_field, "")
            providers[pid] = provider_info

        return {
            "default_provider": merged.get("default_provider", "deepseek"),
            "providers": providers,
            "general": {
                "max_tokens": merged.get("max_tokens", 4096),
                "temperature": merged.get("temperature", 0.3),
                "timeout": merged.get("timeout", 60),
            },
        }

    def get_effective_settings(self, env_settings):
        """
        获取合并后可直接传给 get_adapter() 的配置对象

        返回一个简单命名空间对象，属性与 AISettings 一致。
        """
        from types import SimpleNamespace
        merged = self.load(env_settings)
        return SimpleNamespace(**merged)

    async def test_provider(self, provider: str, env_settings) -> Dict[str, Any]:
        """
        测试指定提供商的连接

        Args:
            provider: 提供商ID (deepseek/gemini/openai)
            env_settings: AISettings 环境变量配置对象

        Returns:
            {"provider": str, "success": bool, "message": str}
        """
        from .adapters import get_adapter

        try:
            effective = self.get_effective_settings(env_settings)
            adapter = get_adapter(provider, effective)
            ok = await adapter.health_check()
            if ok:
                return {"provider": provider, "success": True, "message": "连接成功"}
            return {"provider": provider, "success": False, "message": "健康检查未通过"}
        except ValueError as e:
            return {"provider": provider, "success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"测试提供商 {provider} 连接失败: {e}")
            return {"provider": provider, "success": False, "message": f"连接失败: {e}"}
