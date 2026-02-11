"""
配置管理模块测试
"""

import pytest
from src.config import Settings, get_settings
from src.config.constants import TimeInterval, ExchangeName, TableName


def test_settings_creation():
    """测试配置创建"""
    settings = Settings()
    assert settings is not None
    assert settings.system.app_name == "Crypto-Trade"


def test_database_settings():
    """测试数据库配置"""
    settings = Settings()
    assert settings.database.host is not None
    assert settings.database.port == 5432
    assert settings.database.url.startswith("postgresql://")


def test_redis_settings():
    """测试Redis配置"""
    settings = Settings()
    assert settings.redis.host is not None
    assert settings.redis.port == 6379
    assert settings.redis.url.startswith("redis://")


def test_logging_settings():
    """测试日志配置"""
    settings = Settings()
    assert settings.logging.level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    assert settings.logging.format in ["json", "text"]


def test_get_settings_singleton():
    """测试配置单例"""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_time_interval_constants():
    """测试时间周期常量"""
    assert TimeInterval.ONE_MINUTE == "1m"
    assert TimeInterval.ONE_HOUR == "1h"
    assert TimeInterval.ONE_DAY == "1d"


def test_exchange_name_constants():
    """测试交易所名称常量"""
    assert ExchangeName.BINANCE == "binance"
    assert ExchangeName.OKX == "okx"


def test_table_name_constants():
    """测试表名常量"""
    assert TableName.KLINES == "klines"
    assert TableName.SIGNALS == "signals"
