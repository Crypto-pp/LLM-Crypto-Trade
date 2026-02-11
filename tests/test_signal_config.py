"""
信号配置管理器测试

测试 SignalConfigManager 的 CRUD 操作。
"""

import os
import json
import tempfile
import pytest

from src.config.signal_config_manager import SignalConfigManager


@pytest.fixture
def tmp_config(tmp_path):
    """创建临时配置文件路径"""
    return str(tmp_path / "signal_config.json")


@pytest.fixture
def manager(tmp_config):
    """创建使用临时文件的管理器实例"""
    return SignalConfigManager(config_path=tmp_config)


class TestSignalConfigManager:
    """SignalConfigManager 测试套件"""

    def test_get_tasks_empty(self, manager):
        """空配置返回空列表"""
        tasks = manager.get_tasks()
        assert tasks == []

    def test_add_task_basic(self, manager):
        """添加基本任务"""
        task = manager.add_task({
            "symbol": "BTC/USDT",
            "strategy": "trend_following",
            "interval": "1h",
        })

        assert task["symbol"] == "BTC/USDT"
        assert task["strategy"] == "trend_following"
        assert task["interval"] == "1h"
        assert task["enabled"] is True
        assert "id" in task
        assert "created_at" in task

    def test_add_task_disabled(self, manager):
        """添加禁用状态的任务"""
        task = manager.add_task({
            "symbol": "ETH/USDT",
            "strategy": "momentum",
            "interval": "4h",
            "enabled": False,
        })

        assert task["enabled"] is False

    def test_add_task_invalid_strategy(self, manager):
        """无效策略抛出 ValueError"""
        with pytest.raises(ValueError, match="不支持的策略"):
            manager.add_task({
                "symbol": "BTC/USDT",
                "strategy": "invalid_strategy",
                "interval": "1h",
            })

    def test_add_task_invalid_interval(self, manager):
        """无效周期抛出 ValueError"""
        with pytest.raises(ValueError, match="不支持的周期"):
            manager.add_task({
                "symbol": "BTC/USDT",
                "strategy": "trend_following",
                "interval": "2h",
            })

    def test_add_task_empty_symbol(self, manager):
        """空交易对抛出 ValueError"""
        with pytest.raises(ValueError, match="交易对不能为空"):
            manager.add_task({
                "symbol": "",
                "strategy": "trend_following",
                "interval": "1h",
            })

    def test_get_tasks_after_add(self, manager):
        """添加后能查询到任务"""
        manager.add_task({
            "symbol": "BTC/USDT",
            "strategy": "trend_following",
            "interval": "1h",
        })
        manager.add_task({
            "symbol": "ETH/USDT",
            "strategy": "momentum",
            "interval": "4h",
        })

        tasks = manager.get_tasks()
        assert len(tasks) == 2
        symbols = [t["symbol"] for t in tasks]
        assert "BTC/USDT" in symbols
        assert "ETH/USDT" in symbols

    def test_get_task_by_id(self, manager):
        """根据ID获取单个任务"""
        task = manager.add_task({
            "symbol": "BTC/USDT",
            "strategy": "trend_following",
            "interval": "1h",
        })

        found = manager.get_task(task["id"])
        assert found is not None
        assert found["id"] == task["id"]
        assert found["symbol"] == "BTC/USDT"

    def test_get_task_not_found(self, manager):
        """查询不存在的任务返回 None"""
        result = manager.get_task("nonexistent-id")
        assert result is None

    def test_update_task(self, manager):
        """更新任务字段"""
        task = manager.add_task({
            "symbol": "BTC/USDT",
            "strategy": "trend_following",
            "interval": "1h",
        })

        updated = manager.update_task(task["id"], {
            "enabled": False,
            "interval": "4h",
        })

        assert updated is not None
        assert updated["enabled"] is False
        assert updated["interval"] == "4h"
        assert updated["symbol"] == "BTC/USDT"

    def test_update_task_invalid_strategy(self, manager):
        """更新为无效策略抛出 ValueError"""
        task = manager.add_task({
            "symbol": "BTC/USDT",
            "strategy": "trend_following",
            "interval": "1h",
        })

        with pytest.raises(ValueError, match="不支持的策略"):
            manager.update_task(task["id"], {"strategy": "bad"})

    def test_update_task_not_found(self, manager):
        """更新不存在的任务返回 None"""
        result = manager.update_task("nonexistent", {"enabled": False})
        assert result is None

    def test_delete_task(self, manager):
        """删除任务"""
        task = manager.add_task({
            "symbol": "BTC/USDT",
            "strategy": "trend_following",
            "interval": "1h",
        })

        deleted = manager.delete_task(task["id"])
        assert deleted is True
        assert manager.get_tasks() == []

    def test_delete_task_not_found(self, manager):
        """删除不存在的任务返回 False"""
        result = manager.delete_task("nonexistent")
        assert result is False

    def test_persistence(self, tmp_config):
        """数据持久化到文件"""
        mgr1 = SignalConfigManager(config_path=tmp_config)
        mgr1.add_task({
            "symbol": "BTC/USDT",
            "strategy": "trend_following",
            "interval": "1h",
        })

        # 新实例应能读取到数据
        mgr2 = SignalConfigManager(config_path=tmp_config)
        tasks = mgr2.get_tasks()
        assert len(tasks) == 1
        assert tasks[0]["symbol"] == "BTC/USDT"

    def test_corrupted_file(self, tmp_config):
        """损坏的JSON文件返回空列表"""
        os.makedirs(os.path.dirname(tmp_config) or ".", exist_ok=True)
        with open(tmp_config, "w") as f:
            f.write("not valid json{{{")

        mgr = SignalConfigManager(config_path=tmp_config)
        tasks = mgr.get_tasks()
        assert tasks == []

    def test_update_last_run(self, manager):
        """更新 last_run 和 last_signal"""
        task = manager.add_task({
            "symbol": "BTC/USDT",
            "strategy": "trend_following",
            "interval": "1h",
        })

        updated = manager.update_task(task["id"], {
            "last_run": "2026-02-10T06:00:00+00:00",
            "last_signal": "BUY",
        })

        assert updated["last_run"] == "2026-02-10T06:00:00+00:00"
        assert updated["last_signal"] == "BUY"
