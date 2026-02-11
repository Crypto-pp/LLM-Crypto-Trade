"""
AI辅助分析服务模块

提供多模型AI接入（DeepSeek/Gemini/OpenAI兼容），
基于价格行为和金融知识预设提示词进行智能分析。
"""

from .ai_analyzer import AIAnalyzer
from .config_manager import AIConfigManager
from .context_builder import ContextBuilder
from .prompts.prompt_manager import PromptManager

__all__ = [
    "AIAnalyzer",
    "AIConfigManager",
    "ContextBuilder",
    "PromptManager",
]
