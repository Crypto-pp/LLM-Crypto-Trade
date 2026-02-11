"""
飞书自定义机器人通知器

通过飞书 Webhook 发送交易信号和告警通知，支持富文本卡片消息格式。
飞书自定义机器人文档：https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot
"""

import time
import hashlib
import hmac
import base64
import aiohttp
from typing import Dict, Any, Optional
from .base_notifier import BaseNotifier


class FeishuNotifier(BaseNotifier):
    """飞书自定义机器人通知器"""

    def __init__(self, webhook_url: str, secret: str = ""):
        super().__init__("feishu")
        self.webhook_url = webhook_url
        self.secret = secret

    def _gen_sign(self, timestamp: int) -> str:
        """
        生成签名（飞书安全设置-签名校验）

        算法：HMAC-SHA256(timestamp + "\\n" + secret)，再 base64 编码
        """
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(hmac_code).decode("utf-8")

    async def _post(self, payload: Dict[str, Any]) -> bool:
        """发送 POST 请求到飞书 Webhook"""
        if self.secret:
            timestamp = int(time.time())
            payload["timestamp"] = str(timestamp)
            payload["sign"] = self._gen_sign(timestamp)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    result = await resp.json()
                    if result.get("code") == 0:
                        self.logger.info("飞书消息发送成功")
                        return True
                    self.logger.error(f"飞书消息发送失败: {result}")
                    return False
        except Exception as e:
            self.logger.error(f"飞书消息发送异常: {e}")
            return False

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """发送告警通知（交互式卡片）"""
        card = self._build_alert_card(alert)
        return await self._post({"msg_type": "interactive", "card": card})

    async def send_resolution(self, alert: Dict[str, Any]) -> bool:
        """发送告警解决通知"""
        card = self._build_resolution_card(alert)
        return await self._post({"msg_type": "interactive", "card": card})

    async def send_signal(self, signal: Dict[str, Any]) -> bool:
        """发送交易信号通知（交互式卡片）"""
        card = self._build_signal_card(signal)
        return await self._post({"msg_type": "interactive", "card": card})

    # ========== 卡片构建 ==========

    def _build_signal_card(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """构建交易信号卡片"""
        signal_type = signal.get("signal_type", "HOLD")
        symbol = signal.get("symbol", "")
        strategy = signal.get("strategy", "")
        confidence = signal.get("confidence", 0)

        # 信号类型对应的颜色和 emoji
        type_map = {
            "BUY": {"color": "green", "emoji": "📈", "label": "买入"},
            "SELL": {"color": "red", "emoji": "📉", "label": "卖出"},
            "HOLD": {"color": "blue", "emoji": "⏸️", "label": "持有"},
        }
        info = type_map.get(signal_type, type_map["HOLD"])

        # 价格信息
        entry = signal.get("entry_price", "--")
        stop_loss = signal.get("stop_loss", "--")
        take_profit = signal.get("take_profit", "--")
        interval = signal.get("interval", "--")
        timestamp = signal.get("timestamp", "--")

        # 置信度百分比
        conf_pct = f"{confidence * 100:.0f}%" if isinstance(confidence, (int, float)) else str(confidence)

        elements = [
            {
                "tag": "div",
                "fields": [
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**交易对**\n{symbol}"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**策略**\n{strategy}"}},
                ],
            },
            {
                "tag": "div",
                "fields": [
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**入场价**\n{entry}"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**置信度**\n{conf_pct}"}},
                ],
            },
            {
                "tag": "div",
                "fields": [
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**止损**\n{stop_loss or '--'}"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**止盈**\n{take_profit or '--'}"}},
                ],
            },
            {
                "tag": "div",
                "fields": [
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**周期**\n{interval}"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**时间**\n{timestamp[:19] if len(str(timestamp)) > 19 else timestamp}"}},
                ],
            },
        ]

        return {
            "header": {
                "title": {"tag": "plain_text", "content": f"{info['emoji']} {symbol} {info['label']}信号"},
                "template": info["color"],
            },
            "elements": elements,
        }

    def _build_alert_card(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """构建告警卡片"""
        severity = alert.get("severity", "info")
        color_map = {"info": "blue", "warning": "orange", "critical": "red"}
        emoji_map = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}

        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**级别**: {severity.upper()}\n**时间**: {alert.get('fired_at', '--')}\n\n{alert.get('description', '')}",
                },
            },
        ]

        if alert.get("labels"):
            label_text = "\n".join(f"• {k}: {v}" for k, v in alert["labels"].items())
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"**标签**\n{label_text}"},
            })

        return {
            "header": {
                "title": {"tag": "plain_text", "content": f"{emoji_map.get(severity, '📢')} {alert.get('title', '告警')}"},
                "template": color_map.get(severity, "blue"),
            },
            "elements": elements,
        }

    def _build_resolution_card(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """构建告警解决卡片"""
        return {
            "header": {
                "title": {"tag": "plain_text", "content": f"✅ 告警已解决: {alert.get('title', '')}"},
                "template": "green",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**解决时间**: {alert.get('resolved_at', '--')}",
                    },
                },
            ],
        }
