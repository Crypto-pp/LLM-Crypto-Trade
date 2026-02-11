"""
告警规则定义
包括系统、应用和业务告警规则
"""

from typing import Dict, Any, Callable
from dataclasses import dataclass
from .alert_manager import Alert, AlertSeverity


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    title: str
    description_template: str
    labels: Dict[str, str] = None

    def evaluate(self, metrics: Dict[str, Any]) -> bool:
        """评估规则"""
        return self.condition(metrics)

    def create_alert(self, metrics: Dict[str, Any]) -> Alert:
        """创建告警"""
        description = self.description_template.format(**metrics)
        return Alert(
            name=self.name,
            severity=self.severity,
            title=self.title,
            description=description,
            labels=self.labels or {}
        )


class SystemAlertRules:
    """系统告警规则"""

    @staticmethod
    def high_cpu_usage() -> AlertRule:
        """CPU使用率过高"""
        return AlertRule(
            name="HighCPUUsage",
            condition=lambda m: m.get('cpu_usage', 0) > 80,
            severity=AlertSeverity.WARNING,
            title="High CPU Usage",
            description_template="CPU usage is {cpu_usage:.1f}% (threshold: 80%)",
            labels={'category': 'system'}
        )

    @staticmethod
    def critical_cpu_usage() -> AlertRule:
        """CPU使用率严重过高"""
        return AlertRule(
            name="CriticalCPUUsage",
            condition=lambda m: m.get('cpu_usage', 0) > 95,
            severity=AlertSeverity.CRITICAL,
            title="Critical CPU Usage",
            description_template="CPU usage is {cpu_usage:.1f}% (threshold: 95%)",
            labels={'category': 'system'}
        )

    @staticmethod
    def high_memory_usage() -> AlertRule:
        """内存使用率过高"""
        return AlertRule(
            name="HighMemoryUsage",
            condition=lambda m: m.get('memory_usage_percent', 0) > 80,
            severity=AlertSeverity.WARNING,
            title="High Memory Usage",
            description_template="Memory usage is {memory_usage_percent:.1f}% (threshold: 80%)",
            labels={'category': 'system'}
        )

    @staticmethod
    def disk_space_low() -> AlertRule:
        """磁盘空间不足"""
        return AlertRule(
            name="DiskSpaceLow",
            condition=lambda m: m.get('disk_usage_percent', 0) > 80,
            severity=AlertSeverity.WARNING,
            title="Disk Space Low",
            description_template="Disk usage is {disk_usage_percent:.1f}% (threshold: 80%)",
            labels={'category': 'system'}
        )


class ApplicationAlertRules:
    """应用告警规则"""

    @staticmethod
    def high_error_rate() -> AlertRule:
        """错误率过高"""
        return AlertRule(
            name="HighErrorRate",
            condition=lambda m: m.get('error_rate', 0) > 0.05,
            severity=AlertSeverity.WARNING,
            title="High Error Rate",
            description_template="Error rate is {error_rate:.2%} (threshold: 5%)",
            labels={'category': 'application'}
        )

    @staticmethod
    def slow_api_response() -> AlertRule:
        """API响应慢"""
        return AlertRule(
            name="SlowAPIResponse",
            condition=lambda m: m.get('p95_latency', 0) > 2.0,
            severity=AlertSeverity.WARNING,
            title="Slow API Response",
            description_template="P95 latency is {p95_latency:.2f}s (threshold: 2s)",
            labels={'category': 'application'}
        )

    @staticmethod
    def service_down() -> AlertRule:
        """服务不可用"""
        return AlertRule(
            name="ServiceDown",
            condition=lambda m: m.get('service_up', 1) == 0,
            severity=AlertSeverity.CRITICAL,
            title="Service Down",
            description_template="Service {service_name} is down",
            labels={'category': 'application'}
        )


class BusinessAlertRules:
    """业务告警规则"""

    @staticmethod
    def data_collection_delay() -> AlertRule:
        """数据采集延迟"""
        return AlertRule(
            name="DataCollectionDelay",
            condition=lambda m: m.get('data_age_seconds', 0) > 300,
            severity=AlertSeverity.WARNING,
            title="Data Collection Delay",
            description_template="Data for {symbol} is {data_age_seconds:.0f}s old (threshold: 300s)",
            labels={'category': 'business'}
        )

    @staticmethod
    def data_collection_failure() -> AlertRule:
        """数据采集失败"""
        return AlertRule(
            name="DataCollectionFailure",
            condition=lambda m: m.get('failure_rate', 0) > 0.1,
            severity=AlertSeverity.WARNING,
            title="High Data Collection Failure Rate",
            description_template="Failure rate is {failure_rate:.2%} (threshold: 10%)",
            labels={'category': 'business'}
        )

    @staticmethod
    def strategy_loss() -> AlertRule:
        """策略亏损"""
        return AlertRule(
            name="StrategyLoss",
            condition=lambda m: m.get('profit_loss', 0) < -1000,
            severity=AlertSeverity.CRITICAL,
            title="Strategy Experiencing Losses",
            description_template="Strategy {strategy_name} loss: ${profit_loss:.2f}",
            labels={'category': 'business'}
        )

    @staticmethod
    def api_rate_limit_approaching() -> AlertRule:
        """API限流接近"""
        return AlertRule(
            name="APIRateLimitApproaching",
            condition=lambda m: m.get('rate_limit_remaining', 1000) < 100,
            severity=AlertSeverity.WARNING,
            title="API Rate Limit Approaching",
            description_template="Only {rate_limit_remaining} requests remaining for {exchange}",
            labels={'category': 'business'}
        )
