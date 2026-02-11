"""
Webhook通知器
通过HTTP POST发送告警到Webhook
"""

import aiohttp
from typing import Dict, Any, Optional
from .base_notifier import BaseNotifier


class WebhookNotifier(BaseNotifier):
    """Webhook通知器"""

    def __init__(
        self,
        webhook_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10
    ):
        super().__init__("webhook")
        self.webhook_url = webhook_url
        self.headers = headers or {'Content-Type': 'application/json'}
        self.timeout = timeout

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """发送告警到Webhook"""
        payload = self._format_payload(alert)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status in [200, 201, 202, 204]:
                        self.logger.info("Webhook notification sent successfully")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Webhook returned status {response.status}: {error_text}")
                        return False

        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")
            return False

    async def send_resolution(self, alert: Dict[str, Any]) -> bool:
        """发送告警解决通知到Webhook"""
        payload = self._format_payload(alert, resolved=True)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    return response.status in [200, 201, 202, 204]

        except Exception as e:
            self.logger.error(f"Failed to send resolution webhook: {e}")
            return False

    def _format_payload(self, alert: Dict[str, Any], resolved: bool = False) -> Dict[str, Any]:
        """格式化Webhook payload"""
        payload = {
            'alert_name': alert['name'],
            'title': alert['title'],
            'description': alert['description'],
            'severity': alert['severity'],
            'status': 'resolved' if resolved else alert['status'],
            'fired_at': alert['fired_at'],
            'labels': alert.get('labels', {}),
            'annotations': alert.get('annotations', {})
        }

        if resolved and alert.get('resolved_at'):
            payload['resolved_at'] = alert['resolved_at']

        return payload
