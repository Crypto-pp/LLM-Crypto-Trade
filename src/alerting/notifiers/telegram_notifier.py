"""
Telegram通知器
通过Telegram Bot发送告警通知
"""

import aiohttp
from typing import Dict, Any, Optional
from .base_notifier import BaseNotifier


class TelegramNotifier(BaseNotifier):
    """Telegram通知器"""

    def __init__(self, bot_token: str, chat_id: str):
        super().__init__("telegram")
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    async def send_message(
        self,
        message: str,
        parse_mode: str = 'HTML',
        disable_notification: bool = False
    ) -> bool:
        """
        发送Telegram消息

        Args:
            message: 消息内容
            parse_mode: 解析模式 (HTML/Markdown)
            disable_notification: 是否静默发送

        Returns:
            bool: 发送是否成功
        """
        url = f"{self.api_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_notification': disable_notification
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        self.logger.info("Telegram message sent successfully")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Failed to send Telegram message: {error_text}")
                        return False
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """发送告警通知"""
        message = self._format_html_alert(alert)

        # 严重告警不静默
        disable_notification = alert.get('severity') != 'critical'

        return await self.send_message(
            message,
            parse_mode='HTML',
            disable_notification=disable_notification
        )

    async def send_resolution(self, alert: Dict[str, Any]) -> bool:
        """发送告警解决通知"""
        message = f"✅ <b>Alert Resolved</b>\n\n"
        message += f"<b>{alert['title']}</b>\n"
        message += f"Resolved at: {alert['resolved_at']}\n"

        return await self.send_message(message, parse_mode='HTML', disable_notification=True)

    async def send_signal(self, signal: Dict[str, Any]) -> bool:
        """发送交易信号通知"""
        message = self._format_signal_html(signal)
        disable_notification = signal.get("signal_type") == "HOLD"
        return await self.send_message(
            message, parse_mode='HTML', disable_notification=disable_notification
        )

    def _format_signal_html(self, signal: Dict[str, Any]) -> str:
        """格式化交易信号为HTML消息"""
        signal_type = signal.get("signal_type", "HOLD")
        type_map = {
            "BUY": ("📈", "买入"),
            "SELL": ("📉", "卖出"),
            "HOLD": ("⏸️", "持有"),
        }
        emoji, label = type_map.get(signal_type, ("📢", signal_type))

        symbol = signal.get("symbol", "")
        strategy = signal.get("strategy", "")
        entry = signal.get("entry_price", "--")
        stop_loss = signal.get("stop_loss")
        take_profit = signal.get("take_profit")
        confidence = signal.get("confidence", 0)
        interval = signal.get("interval", "--")
        timestamp = signal.get("timestamp", "--")

        conf_pct = f"{confidence * 100:.0f}%" if isinstance(confidence, (int, float)) else str(confidence)

        msg = f"{emoji} <b>{symbol} {label}信号</b>\n\n"
        msg += f"<b>策略:</b> {strategy}\n"
        msg += f"<b>入场价:</b> {entry}\n"
        msg += f"<b>置信度:</b> {conf_pct}\n"
        if stop_loss:
            msg += f"<b>止损:</b> {stop_loss}\n"
        if take_profit:
            msg += f"<b>止盈:</b> {take_profit}\n"
        msg += f"<b>周期:</b> {interval}\n"
        ts = str(timestamp)[:19] if len(str(timestamp)) > 19 else str(timestamp)
        msg += f"<b>时间:</b> {ts}"
        return msg

    def _format_html_alert(self, alert: Dict[str, Any]) -> str:
        """格式化HTML告警消息"""
        severity_emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'critical': '🚨'
        }

        emoji = severity_emoji.get(alert.get('severity', 'info'), '📢')

        message = f"{emoji} <b>{alert['title']}</b>\n\n"
        message += f"<b>Severity:</b> {alert['severity'].upper()}\n"
        message += f"<b>Time:</b> {alert['fired_at']}\n\n"
        message += f"<b>Description:</b>\n{alert['description']}\n"

        if alert.get('labels'):
            message += f"\n<b>Labels:</b>\n"
            for key, value in alert['labels'].items():
                message += f"  • {key}: {value}\n"

        return message
