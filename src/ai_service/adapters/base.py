"""
AI模型适配器抽象基类

定义所有AI模型适配器必须实现的接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, AsyncGenerator, Optional


class BaseModelAdapter(ABC):
    """AI模型适配器基类"""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """
        发送对话请求

        Args:
            messages: 消息列表，格式 [{"role": "system/user", "content": "..."}]
            stream: 是否使用流式响应

        Returns:
            普通模式返回完整文本，流式模式返回异步生成器
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """检查模型服务是否可用"""
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        """获取当前使用的模型名称"""
        ...

    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        ...
