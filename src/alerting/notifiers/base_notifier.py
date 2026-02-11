"""
通知器基类
定义通知器接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseNotifier(ABC):
    """通知器基类"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """
        发送告警通知

        Args:
            alert: 告警信息字典

        Returns:
            bool: 发送是否成功
        """
        pass

    async def send_resolution(self, alert: Dict[str, Any]) -> bool:
        """
        发送告警解决通知

        Args:
            alert: 告警信息字典

        Returns:
            bool: 发送是否成功
        """
        # 默认实现：不发送解决通知
        return True

    def format_alert_message(self, alert: Dict[str, Any]) -> str:
        """
        格式化告警消息

        Args:
            alert: 告警信息字典

        Returns:
            str: 格式化后的消息
        """
        severity_emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'critical': '🚨'
        }

        emoji = severity_emoji.get(alert.get('severity', 'info'), '📢')

        message = f"{emoji} {alert['title']}\n\n"
        message += f"Severity: {alert['severity']}\n"
        message += f"Time: {alert['fired_at']}\n\n"
        message += f"Description:\n{alert['description']}\n"

        if alert.get('labels'):
            message += f"\nLabels: {alert['labels']}"

        return message
