"""
API集成测试
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "status" in data


def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data


def test_metrics_endpoint():
    """测试指标端点"""
    response = client.get("/metrics")
    assert response.status_code == 200


def test_rate_limit():
    """测试限流"""
    # 发送大量请求
    responses = []
    for _ in range(70):
        response = client.get("/")
        responses.append(response.status_code)

    # 应该有一些请求被限流
    assert 429 in responses


def test_cors_headers():
    """测试CORS头"""
    response = client.options("/")
    assert "access-control-allow-origin" in response.headers
