"""
提示词管理器

管理预设提示词模板，构建发送给AI的消息列表。
"""

from typing import List, Dict, Optional
from loguru import logger

from .templates import SYSTEM_PROMPT, PROMPT_TEMPLATES


class PromptManager:
    """提示词管理器"""

    def get_prompt(self, prompt_id: str) -> Optional[Dict]:
        """获取指定提示词模板"""
        return PROMPT_TEMPLATES.get(prompt_id)

    def list_prompts(self) -> List[Dict]:
        """获取所有可用提示词列表"""
        return [
            {
                "id": t["id"],
                "name": t["name"],
                "description": t["description"],
                "category": t["category"],
            }
            for t in PROMPT_TEMPLATES.values()
        ]

    def build_messages(
        self,
        prompt_id: str,
        symbol: str,
        interval: str,
        market_context: str,
    ) -> List[Dict[str, str]]:
        """
        构建发送给AI的消息列表

        Args:
            prompt_id: 提示词模板ID
            symbol: 交易对
            interval: 时间周期
            market_context: 市场上下文文本

        Returns:
            消息列表 [{"role": "system/user", "content": "..."}]
        """
        template = PROMPT_TEMPLATES.get(prompt_id)
        if not template:
            raise ValueError(f"未知的提示词ID: {prompt_id}")

        user_content = template["template"].format(
            symbol=symbol,
            interval=interval,
            market_context=market_context,
        )

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
