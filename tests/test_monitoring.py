"""
监控模块测试
"""

import pytest
from src.monitoring.metrics import (
    REQUEST_COUNT,
    DATA_COLLECTION_SUCCESS,
    SystemMetricsCollector
)
from src.monitoring.health_check import HealthChecker


def test_request_count_metric():
    """测试请求计数指标"""
    initial = REQUEST_COUNT.labels(method="GET", endpoint="/test", status=200)._value.get()
    REQUEST_COUNT.labels(method="GET", endpoint="/test", status=200).inc()
    final = REQUEST_COUNT.labels(method="GET", endpoint="/test", status=200)._value.get()
    assert final > initial


def test_system_metrics_collector():
    """测试系统指标采集器"""
    collector = SystemMetricsCollector()
    collector.collect_all()
    # 验证指标已采集（不抛出异常即可）


@pytest.mark.asyncio
async def test_health_checker():
    """测试健康检查器"""
    checker = HealthChecker()
    result = await checker.check_all()
    assert "status" in result
    assert "checks" in result
