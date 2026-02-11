"""
告警系统测试
"""

import pytest
from src.alerting.alert_manager import AlertManager, Alert, AlertSeverity
from src.alerting.alert_rules import SystemAlertRules


def test_alert_creation():
    """测试告警创建"""
    alert = Alert(
        name="TestAlert",
        severity=AlertSeverity.WARNING,
        title="Test Alert",
        description="This is a test alert"
    )
    assert alert.name == "TestAlert"
    assert alert.severity == AlertSeverity.WARNING


@pytest.mark.asyncio
async def test_alert_manager():
    """测试告警管理器"""
    manager = AlertManager()

    alert = Alert(
        name="TestAlert",
        severity=AlertSeverity.WARNING,
        title="Test Alert",
        description="Test"
    )

    await manager.fire_alert(alert)
    active_alerts = manager.get_active_alerts()
    assert len(active_alerts) > 0


def test_alert_rules():
    """测试告警规则"""
    rule = SystemAlertRules.high_cpu_usage()

    # 测试条件
    assert rule.evaluate({"cpu_usage": 85}) == True
    assert rule.evaluate({"cpu_usage": 70}) == False
