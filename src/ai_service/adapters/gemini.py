"""
Gemini模型适配器

使用google-generativeai SDK调用Gemini API。
"""

from typing import List, Dict, AsyncGenerator
from loguru import logger

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .base import BaseModelAdapter


class GeminiAdapter(BaseModelAdapter):
    """Gemini模型适配器"""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        max_tokens: int = 4096,
        temperature: float = 0.3,
        timeout: int = 60,
    ):
        if not genai:
            raise ImportError("需要安装 google-generativeai: pip install google-generativeai")
        genai.configure(api_key=api_key)
        self.model_name = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._model = genai.GenerativeModel(
            model_name=model,
            generation_config=genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )

    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple:
        """将OpenAI格式消息转为Gemini格式"""
        system_instruction = None
        contents = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_instruction = content
            elif role == "user":
                contents.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [content]})

        return system_instruction, contents

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
        system_instruction, contents = self._convert_messages(messages)

        model = self._model
        if system_instruction:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=self.max_tokens,
                    temperature=self.temperature,
                ),
                system_instruction=system_instruction,
            )

        response = await model.generate_content_async(contents)
        return response.text

    async def _stream_chat(
        self, messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """流式对话请求"""
        system_instruction, contents = self._convert_messages(messages)

        model = self._model
        if system_instruction:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=self.max_tokens,
                    temperature=self.temperature,
                ),
                system_instruction=system_instruction,
            )

        response = await model.generate_content_async(contents, stream=True)
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def health_check(self) -> bool:
        """检查Gemini服务可用性"""
        try:
            response = await self._model.generate_content_async("ping")
            return bool(response.text)
        except Exception as e:
            logger.warning(f"Gemini健康检查失败: {e}")
            return False

    def get_model_name(self) -> str:
        return self.model_name

    def get_provider_name(self) -> str:
        return "gemini"
