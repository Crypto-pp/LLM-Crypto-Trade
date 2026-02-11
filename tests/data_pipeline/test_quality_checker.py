"""
数据质量检查测试
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.data_pipeline.quality_checker import DataQualityChecker
from src.data_pipeline.adapters.base import KlineData


@pytest.fixture
def quality_checker():
    """创建质量检查器实例"""
    return DataQualityChecker()


@pytest.fixture
def sample_klines():
    """创建示例K线数据"""
    base_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    klines = []

    for i in range(10):
        klines.append(KlineData(
            timestamp=base_time + timedelta(hours=i),
            open=Decimal("50000") + Decimal(i * 100),
            high=Decimal("51000") + Decimal(i * 100),
            low=Decimal("49000") + Decimal(i * 100),
            close=Decimal("50500") + Decimal(i * 100),
            volume=Decimal("100.5")
        ))

    return klines


def test_check_validity_valid_kline(quality_checker):
    """测试有效K线数据"""
    kline = KlineData(
        timestamp=datetime.now(timezone.utc),
        open=Decimal("50000"),
        high=Decimal("51000"),
        low=Decimal("49000"),
        close=Decimal("50500"),
        volume=Decimal("100.5")
    )

    is_valid, error_msg = quality_checker.check_validity(kline)
    assert is_valid is True
    assert error_msg == ""


def test_check_validity_invalid_ohlc(quality_checker):
    """测试无效的OHLC关系"""
    kline = KlineData(
        timestamp=datetime.now(timezone.utc),
        open=Decimal("50000"),
        high=Decimal("48000"),  # 最高价低于开盘价
        low=Decimal("49000"),
        close=Decimal("50500"),
        volume=Decimal("100.5")
    )

    is_valid, error_msg = quality_checker.check_validity(kline)
    assert is_valid is False
    assert "Invalid OHLC" in error_msg


def test_check_completeness(quality_checker, sample_klines):
    """测试数据完整性检查"""
    is_complete, msg, rate = quality_checker.check_completeness(
        sample_klines, "1h", expected_count=10
    )

    assert is_complete is True
    assert rate == 100.0


def test_check_timestamp_continuity(quality_checker, sample_klines):
    """测试时间戳连续性"""
    is_continuous, missing = quality_checker.check_timestamp(sample_klines, "1h")

    assert is_continuous is True
    assert len(missing) == 0


def test_detect_anomaly(quality_checker):
    """测试异常值检测"""
    klines = []
    base_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # 创建正常数据
    for i in range(10):
        klines.append(KlineData(
            timestamp=base_time + timedelta(hours=i),
            open=Decimal("50000"),
            high=Decimal("51000"),
            low=Decimal("49000"),
            close=Decimal("50000"),
            volume=Decimal("100")
        ))

    # 添加异常值
    klines.append(KlineData(
        timestamp=base_time + timedelta(hours=10),
        open=Decimal("50000"),
        high=Decimal("100000"),  # 异常高价
        low=Decimal("49000"),
        close=Decimal("50000"),
        volume=Decimal("100")
    ))

    anomalies = quality_checker.detect_anomaly(klines, method='zscore')
    assert len(anomalies) > 0


def test_generate_quality_report(quality_checker, sample_klines):
    """测试质量报告生成"""
    report = quality_checker.generate_quality_report(
        sample_klines, "1h", "BTC/USDT"
    )

    assert report['symbol'] == "BTC/USDT"
    assert report['interval'] == "1h"
    assert report['total_records'] == 10
    assert 'completeness' in report
    assert 'validity' in report
    assert 'continuity' in report
