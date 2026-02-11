"""
信号通知服务

桥接信号生成与通知渠道，读取通知配置后将交易信号分发到已启用的飞书/Telegram渠道。
"""

import asyncio
from typing import Dict, Any, List
from loguru import logger

from src.config.notification_config_manager import NotificationConfigManager
from src.alerting.notifiers.telegram_notifier import TelegramNotifier
from src.alerting.notifiers.feishu_notifier import FeishuNotifier


class SignalNotificationService:
    """
    信号通知服务

    根据通知配置，将交易信号发送到所有已启用的通知渠道。
    支持 Telegram 和飞书两种渠道。
    """

    def __init__(self, config_manager: NotificationConfigManager = None):
        self._config = config_manager or NotificationConfigManager()

    async def notify_signals(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量发送信号通知

        根据全局设置过滤信号类型，然后分发到所有已启用渠道。

        Returns:
            发送结果统计 {"sent": int, "failed": int, "skipped": int}
        """
        settings = self._config.get_settings()
        channels = self._config.get_enabled_channels()

        if not channels:
            return {"sent": 0, "failed": 0, "skipped": len(signals)}

        stats = {"sent": 0, "failed": 0, "skipped": 0}

        for signal in signals:
            if not self._should_notify(signal, settings):
                stats["skipped"] += 1
                continue

            results = await self._dispatch_signal(signal, channels)
            stats["sent"] += results["sent"]
            stats["failed"] += results["failed"]

        return stats

    async def notify_single(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """发送单条信号通知"""
        return await self.notify_signals([signal])

    async def send_test(self, channel_id: str) -> bool:
        """
        发送测试消息到指定渠道

        用于前端配置时验证渠道连通性。
        """
        channel = self._config.get_channel(channel_id)
        if not channel:
            raise ValueError(f"渠道不存在: {channel_id}")

        test_signal = {
            "symbol": "BTC/USDT",
            "signal_type": "BUY",
            "entry_price": 100000.0,
            "stop_loss": 96000.0,
            "take_profit": 110000.0,
            "strategy": "测试信号",
            "interval": "1h",
            "confidence": 0.85,
            "timestamp": "2026-01-01T00:00:00",
        }

        notifier = self._create_notifier(channel)
        if not notifier:
            return False

        try:
            return await notifier.send_signal(test_signal)
        except Exception as e:
            logger.error(f"测试消息发送失败 [{channel_id}]: {e}")
            return False

    # ========== 内部方法 ==========

    @staticmethod
    def _should_notify(signal: Dict[str, Any], settings: Dict[str, bool]) -> bool:
        """根据全局设置判断是否需要发送通知"""
        signal_type = signal.get("signal_type", "HOLD").upper()
        if signal_type == "BUY":
            return settings.get("notify_on_buy", True)
        if signal_type == "SELL":
            return settings.get("notify_on_sell", True)
        if signal_type == "HOLD":
            return settings.get("notify_on_hold", False)
        return False

    async def _dispatch_signal(
        self, signal: Dict[str, Any], channels: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """将单条信号分发到所有渠道"""
        tasks = []
        for ch in channels:
            notifier = self._create_notifier(ch)
            if notifier:
                tasks.append(self._safe_send(notifier, signal, ch["id"]))

        if not tasks:
            return {"sent": 0, "failed": 0}

        results = await asyncio.gather(*tasks)
        sent = sum(1 for r in results if r)
        failed = sum(1 for r in results if not r)
        return {"sent": sent, "failed": failed}

    @staticmethod
    def _create_notifier(channel: Dict[str, Any]):
        """根据渠道配置创建对应的通知器实例"""
        ch_type = channel.get("type")
        config = channel.get("config", {})

        if ch_type == "telegram":
            bot_token = config.get("bot_token", "")
            chat_id = config.get("chat_id", "")
            if bot_token and chat_id:
                return TelegramNotifier(bot_token=bot_token, chat_id=chat_id)

        elif ch_type == "feishu":
            webhook_url = config.get("webhook_url", "")
            secret = config.get("secret", "")
            if webhook_url:
                return FeishuNotifier(webhook_url=webhook_url, secret=secret)

        return None

    @staticmethod
    async def _safe_send(notifier, signal: Dict[str, Any], channel_id: str) -> bool:
        """安全发送，捕获异常"""
        try:
            return await notifier.send_signal(signal)
        except Exception as e:
            logger.error(f"信号通知发送失败 [{channel_id}]: {e}")
            return False
