"""
告警管理器
负责告警的触发、聚合、抑制和发送
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """告警严重级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态"""
    FIRING = "firing"
    RESOLVED = "resolved"


class Alert:
    """告警对象"""

    def __init__(
        self,
        name: str,
        severity: AlertSeverity,
        title: str,
        description: str,
        labels: Optional[Dict[str, str]] = None,
        annotations: Optional[Dict[str, str]] = None
    ):
        self.name = name
        self.severity = severity
        self.title = title
        self.description = description
        self.labels = labels or {}
        self.annotations = annotations or {}
        self.status = AlertStatus.FIRING
        self.fired_at = datetime.utcnow()
        self.resolved_at: Optional[datetime] = None

    def resolve(self):
        """解决告警"""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'labels': self.labels,
            'annotations': self.annotations,
            'status': self.status.value,
            'fired_at': self.fired_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class AlertManager:
    """告警管理器"""

    def __init__(self, aggregation_window: int = 300):
        self.aggregation_window = aggregation_window  # 秒
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notifiers: List[Any] = []
        self.alert_counts: Dict[str, int] = defaultdict(int)
        self.last_sent: Dict[str, datetime] = {}
        self.inhibit_rules: List[Dict] = []

    def add_notifier(self, notifier):
        """添加通知器"""
        self.notifiers.append(notifier)
        logger.info(f"Added notifier: {notifier.__class__.__name__}")

    def add_inhibit_rule(self, source_severity: AlertSeverity, target_severity: AlertSeverity):
        """
        添加抑制规则
        如果有source_severity的告警，则抑制target_severity的告警
        """
        self.inhibit_rules.append({
            'source': source_severity,
            'target': target_severity
        })

    async def fire_alert(self, alert: Alert):
        """触发告警"""
        alert_key = f"{alert.name}:{alert.labels.get('instance', 'default')}"

        # 检查是否应该抑制
        if self._should_inhibit(alert):
            logger.info(f"Alert {alert_key} inhibited")
            return

        # 检查是否在聚合窗口内
        if not self._should_send(alert_key):
            logger.info(f"Alert {alert_key} aggregated")
            self.alert_counts[alert_key] += 1
            return

        # 添加到活跃告警
        self.active_alerts[alert_key] = alert
        self.alert_counts[alert_key] += 1

        # 发送通知
        await self._send_notifications(alert)

        # 更新最后发送时间
        self.last_sent[alert_key] = datetime.utcnow()

        logger.info(f"Alert fired: {alert_key} - {alert.title}")

    async def resolve_alert(self, alert_name: str, instance: str = 'default'):
        """解决告警"""
        alert_key = f"{alert_name}:{instance}"

        if alert_key in self.active_alerts:
            alert = self.active_alerts[alert_key]
            alert.resolve()

            # 移到历史记录
            self.alert_history.append(alert)
            del self.active_alerts[alert_key]

            # 发送解决通知
            await self._send_resolution_notifications(alert)

            logger.info(f"Alert resolved: {alert_key}")

    def _should_inhibit(self, alert: Alert) -> bool:
        """检查是否应该抑制告警"""
        for rule in self.inhibit_rules:
            if alert.severity == rule['target']:
                # 检查是否有更高级别的告警
                for active_alert in self.active_alerts.values():
                    if active_alert.severity == rule['source']:
                        # 检查标签是否匹配
                        if self._labels_match(alert.labels, active_alert.labels):
                            return True
        return False

    def _labels_match(self, labels1: Dict, labels2: Dict) -> bool:
        """检查标签是否匹配"""
        # 简单实现：检查instance标签
        return labels1.get('instance') == labels2.get('instance')

    def _should_send(self, alert_key: str) -> bool:
        """检查是否应该发送告警"""
        if alert_key not in self.last_sent:
            return True

        elapsed = (datetime.utcnow() - self.last_sent[alert_key]).total_seconds()
        return elapsed >= self.aggregation_window

    async def _send_notifications(self, alert: Alert):
        """发送通知"""
        tasks = []
        for notifier in self.notifiers:
            tasks.append(notifier.send_alert(alert.to_dict()))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Notifier {self.notifiers[i].__class__.__name__} failed: {result}")

    async def _send_resolution_notifications(self, alert: Alert):
        """发送解决通知"""
        tasks = []
        for notifier in self.notifiers:
            if hasattr(notifier, 'send_resolution'):
                tasks.append(notifier.send_resolution(alert.to_dict()))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_active_alerts(self) -> List[Dict]:
        """获取活跃告警"""
        return [alert.to_dict() for alert in self.active_alerts.values()]

    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        """获取告警历史"""
        return [alert.to_dict() for alert in self.alert_history[-limit:]]

    def get_alert_stats(self) -> Dict[str, Any]:
        """获取告警统计"""
        severity_counts = defaultdict(int)
        for alert in self.active_alerts.values():
            severity_counts[alert.severity.value] += 1

        return {
            'active_count': len(self.active_alerts),
            'total_fired': sum(self.alert_counts.values()),
            'severity_breakdown': dict(severity_counts),
            'history_count': len(self.alert_history)
        }
