"""
通用OpenAI兼容模型适配器

支持所有兼容OpenAI API协议的模型服务。
"""

import json
from typing import List, Dict, AsyncGenerator
from loguru import logger

try:
    import httpx
except ImportError:
    httpx = None

from .base import BaseModelAdapter


class OpenAICompatibleAdapter(BaseModelAdapter):
    """通用OpenAI兼容模型适配器"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        temperature: float = 0.3,
        timeout: int = 60,
        provider_name: str = "openai",
    ):
        if not httpx:
            raise ImportError("需要安装 httpx: pip install httpx")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._provider_name = provider_name

    async def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        if stream:
            return self._stream_chat(messages)
        return await self._normal_chat(messages)

    async def _normal_chat(self, messages: List[Dict[str, str]]) -> str:
        """普通对话请求"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _stream_chat(
        self, messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """流式对话请求"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 5,
                    },
                )
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"OpenAI兼容服务健康检查失败: {e}")
            return False

    def get_model_name(self) -> str:
        return self.model

    def get_provider_name(self) -> str:
        return self._provider_name
