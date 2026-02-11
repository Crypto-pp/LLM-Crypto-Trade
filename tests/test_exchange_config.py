"""
交易所配置管理器测试
"""

import json
import os
import tempfile
import pytest

from src.config.exchange_config_manager import (
    ExchangeConfigManager,
    _mask_key,
    _is_masked,
    EXCHANGE_CONFIG_FIELDS,
    SECRET_FIELDS,
    EXCHANGE_META,
)


@pytest.fixture
def tmp_config_path():
    """创建临时配置文件路径"""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.unlink(path)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def manager(tmp_config_path):
    """创建使用临时路径的管理器实例"""
    return ExchangeConfigManager(config_path=tmp_config_path)


class TestMaskKey:
    """脱敏函数测试"""

    def test_normal_key(self):
        assert _mask_key("abcdefghijklmnop") == "abcd****mnop"

    def test_short_key(self):
        assert _mask_key("short") == ""

    def test_empty_key(self):
        assert _mask_key("") == ""

    def test_exactly_8_chars(self):
        assert _mask_key("12345678") == "1234****5678"


class TestIsMasked:
    """脱敏判断函数测试"""

    def test_masked_value(self):
        assert _is_masked("abcd****efgh") is True

    def test_normal_value(self):
        assert _is_masked("normal-key-value") is False

    def test_empty_value(self):
        assert _is_masked("") is False


class TestLoad:
    """load方法测试"""

    def test_load_empty_no_env(self, manager):
        """无JSON文件、无环境变量时返回空字符串默认值"""
        result = manager.load()
        assert len(result) == len(EXCHANGE_CONFIG_FIELDS)
        for field in EXCHANGE_CONFIG_FIELDS:
            assert result[field] == ""

    def test_load_with_json(self, manager, tmp_config_path):
        """JSON文件存在时正确加载"""
        data = {"binance_api_key": "test-key-123456789"}
        os.makedirs(os.path.dirname(tmp_config_path) or ".", exist_ok=True)
        with open(tmp_config_path, "w") as f:
            json.dump(data, f)

        result = manager.load()
        assert result["binance_api_key"] == "test-key-123456789"
        assert result["binance_api_secret"] == ""


class TestSave:
    """save方法测试"""

    def test_save_new_config(self, manager):
        """保存新配置到JSON文件"""
        data = {
            "binance_api_key": "my-binance-key-12345",
            "binance_api_secret": "my-binance-secret-67890",
        }
        result = manager.save(data)
        assert result["binance_api_key"] == "my-binance-key-12345"
        assert result["binance_api_secret"] == "my-binance-secret-67890"

    def test_save_skips_masked_values(self, manager):
        """保存时跳过脱敏值"""
        manager.save({"binance_api_key": "original-key-123456"})
        manager.save({"binance_api_key": "orig****3456"})
        result = manager.load()
        assert result["binance_api_key"] == "original-key-123456"

    def test_save_ignores_unknown_fields(self, manager):
        """保存时忽略未知字段"""
        manager.save({"unknown_field": "value", "binance_api_key": "test-key-abcdefgh"})
        result = manager.load()
        assert result["binance_api_key"] == "test-key-abcdefgh"
        assert "unknown_field" not in result


class TestGetConfigResponse:
    """get_config_response方法测试"""

    def test_empty_config_response(self, manager):
        """空配置时返回正确结构"""
        resp = manager.get_config_response()
        assert "exchanges" in resp
        assert "binance" in resp["exchanges"]
        assert "okx" in resp["exchanges"]
        assert "coinbase" in resp["exchanges"]
        for eid, info in resp["exchanges"].items():
            assert info["has_key"] is False
            assert "name" in info

    def test_config_response_with_data(self, manager):
        """有配置数据时返回脱敏后的值"""
        manager.save({
            "binance_api_key": "abcdefghijklmnop",
            "binance_api_secret": "secretvalue12345678",
        })
        resp = manager.get_config_response()
        binance = resp["exchanges"]["binance"]
        assert binance["has_key"] is True
        assert binance["api_key"] == "abcd****mnop"
        assert binance["api_secret"] == "secr****5678"


class TestGetEffectiveSettings:
    """get_effective_settings方法测试"""

    def test_returns_namespace(self, manager):
        """返回SimpleNamespace对象"""
        manager.save({"binance_api_key": "test-key-12345678"})
        ns = manager.get_effective_settings()
        assert hasattr(ns, "binance_api_key")
        assert ns.binance_api_key == "test-key-12345678"
        assert ns.binance_api_secret == ""
