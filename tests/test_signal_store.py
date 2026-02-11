"""
信号存储测试

测试 SignalStore 的信号增删查和过期清理。
"""

import os
import json
import pytest
from datetime import datetime, timezone, timedelta

from src.services.signal_store import SignalStore


@pytest.fixture
def tmp_store(tmp_path):
    """创建临时存储文件路径"""
    return str(tmp_path / "signals.json")


@pytest.fixture
def store(tmp_store):
    """创建使用临时文件的存储实例"""
    return SignalStore(store_path=tmp_store)


def _make_signal(symbol="BTC/USDT", signal_type="BUY", strategy="trend_following",
                 hours_valid=24, task_id="task-1"):
    """构造测试信号"""
    now = datetime.now(timezone.utc)
    return {
        "symbol": symbol,
        "signal_type": signal_type,
        "entry_price": 50000.0,
        "stop_loss": 48000.0,
        "take_profit": 55000.0,
        "strategy": strategy,
        "interval": "1h",
        "confidence": 0.85,
        "timestamp": now.isoformat(),
        "valid_until": (now + timedelta(hours=hours_valid)).isoformat(),
        "task_id": task_id,
    }


class TestSignalStoreBasic:
    """基本读写测试"""

    def test_get_signals_empty(self, store):
        """空存储返回空列表"""
        signals = store.get_signals()
        assert signals == []

    def test_add_and_get_signals(self, store):
        """添加后能查询到信号"""
        sig = _make_signal()
        count = store.add_signals([sig])
        assert count == 1

        signals = store.get_signals()
        assert len(signals) == 1
        assert signals[0]["symbol"] == "BTC/USDT"
        assert signals[0]["signal_type"] == "BUY"
        assert "signal_id" in signals[0]

    def test_add_empty_list(self, store):
        """添加空列表返回0"""
        count = store.add_signals([])
        assert count == 0

    def test_auto_generate_fields(self, store):
        """自动生成 signal_id/timestamp/valid_until"""
        sig = {"symbol": "BTC/USDT", "signal_type": "BUY"}
        store.add_signals([sig])

        signals = store.get_signals()
        assert len(signals) == 1
        assert "signal_id" in signals[0]
        assert "timestamp" in signals[0]
        assert "valid_until" in signals[0]


class TestSignalStoreFilter:
    """过滤查询测试"""

    def test_filter_by_symbol(self, store):
        """按交易对过滤"""
        store.add_signals([
            _make_signal(symbol="BTC/USDT"),
            _make_signal(symbol="ETH/USDT"),
        ])

        btc = store.get_signals(symbol="BTC/USDT")
        assert len(btc) == 1
        assert btc[0]["symbol"] == "BTC/USDT"

    def test_filter_by_strategy(self, store):
        """按策略过滤"""
        store.add_signals([
            _make_signal(strategy="trend_following"),
            _make_signal(strategy="momentum"),
        ])

        tf = store.get_signals(strategy="trend_following")
        assert len(tf) == 1
        assert tf[0]["strategy"] == "trend_following"

    def test_limit(self, store):
        """限制返回数量"""
        store.add_signals([_make_signal() for _ in range(5)])

        signals = store.get_signals(limit=3)
        assert len(signals) == 3


class TestSignalStoreCleanup:
    """过期清理测试"""

    def test_cleanup_expired(self, store):
        """清理过期信号"""
        # 添加一个已过期的信号（valid_until 在过去）
        now = datetime.now(timezone.utc)
        expired_sig = _make_signal()
        expired_sig["valid_until"] = (now - timedelta(hours=1)).isoformat()

        valid_sig = _make_signal(symbol="ETH/USDT")

        store.add_signals([expired_sig, valid_sig])
        removed = store.cleanup_expired()

        assert removed == 1
        signals = store.get_signals()
        assert len(signals) == 1
        assert signals[0]["symbol"] == "ETH/USDT"

    def test_cleanup_on_get(self, store):
        """查询时自动清理过期信号"""
        now = datetime.now(timezone.utc)
        expired_sig = _make_signal()
        expired_sig["valid_until"] = (now - timedelta(hours=1)).isoformat()

        store.add_signals([expired_sig])

        # get_signals 内部会调用 cleanup_expired
        signals = store.get_signals()
        assert len(signals) == 0


class TestSignalStoreTaskQuery:
    """按任务查询测试"""

    def test_get_latest_by_task(self, store):
        """获取指定任务的最新信号"""
        store.add_signals([
            _make_signal(task_id="task-1", signal_type="BUY"),
            _make_signal(task_id="task-2", signal_type="SELL"),
        ])

        latest = store.get_latest_by_task("task-1")
        assert latest is not None
        assert latest["task_id"] == "task-1"

    def test_get_latest_by_task_not_found(self, store):
        """查询不存在的任务返回 None"""
        result = store.get_latest_by_task("nonexistent")
        assert result is None


class TestSignalStoreLimit:
    """信号上限测试"""

    def test_enforce_max_signals(self, tmp_store):
        """超过上限时删除最旧的信号"""
        store = SignalStore(store_path=tmp_store)

        # 添加超过上限的信号
        from src.services.signal_store import MAX_SIGNALS
        signals = [_make_signal() for _ in range(MAX_SIGNALS + 10)]
        store.add_signals(signals)

        all_signals = store.get_signals(limit=MAX_SIGNALS + 100)
        assert len(all_signals) <= MAX_SIGNALS
