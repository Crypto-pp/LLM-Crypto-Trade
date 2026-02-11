"""
信号存储模块

管理交易信号的持久化存储，使用 data/signals.json 文件。
支持信号的增删查和过期清理。
"""

import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger

# 信号默认有效期（小时）
DEFAULT_VALID_HOURS = 24

# 最大信号保留数量
MAX_SIGNALS = 500


class SignalStore:
    """
    信号存储管理器

    管理信号的读写和过期清理，持久化到JSON文件。
    """

    def __init__(self, store_path: str = "data/signals.json"):
        self._store_path = store_path

    def _read_json(self) -> Dict[str, Any]:
        """读取信号文件"""
        if not os.path.exists(self._store_path):
            return {"signals": []}
        try:
            with open(self._store_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "signals" not in data:
                    data["signals"] = []
                return data
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"读取信号文件失败: {e}")
            return {"signals": []}

    def _write_json(self, data: Dict[str, Any]) -> None:
        """写入信号文件"""
        os.makedirs(os.path.dirname(self._store_path) or ".", exist_ok=True)
        with open(self._store_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def cleanup_expired(self) -> int:
        """
        清理过期信号

        Returns:
            清理的信号数量
        """
        data = self._read_json()
        now = datetime.now(timezone.utc).isoformat()
        original_len = len(data["signals"])

        data["signals"] = [
            s for s in data["signals"]
            if s.get("valid_until", "") > now
        ]

        removed = original_len - len(data["signals"])
        if removed > 0:
            self._write_json(data)
            logger.info(f"清理了 {removed} 条过期信号")
        return removed

    def _enforce_limit(self, data: Dict[str, Any]) -> None:
        """确保信号数量不超过上限，超出时删除最旧的"""
        signals = data["signals"]
        if len(signals) > MAX_SIGNALS:
            # 按时间戳排序，保留最新的
            signals.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
            data["signals"] = signals[:MAX_SIGNALS]

    def get_signals(
        self,
        symbol: Optional[str] = None,
        strategy: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        查询信号，支持按交易对和策略过滤

        每次查询时自动清理过期信号。
        """
        self.cleanup_expired()
        data = self._read_json()
        signals = data.get("signals", [])

        if symbol:
            signals = [s for s in signals if s.get("symbol") == symbol]
        if strategy:
            signals = [s for s in signals if s.get("strategy") == strategy]

        # 按时间倒序
        signals.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
        return signals[:limit]

    def add_signals(self, signals: List[Dict[str, Any]]) -> int:
        """
        批量添加信号

        自动生成 signal_id 和 valid_until（如未提供）。

        Returns:
            添加的信号数量
        """
        if not signals:
            return 0

        data = self._read_json()
        now = datetime.now(timezone.utc)

        for signal in signals:
            if "signal_id" not in signal:
                signal["signal_id"] = str(uuid.uuid4())
            if "timestamp" not in signal:
                signal["timestamp"] = now.isoformat()
            if "valid_until" not in signal:
                valid_until = now + timedelta(hours=DEFAULT_VALID_HOURS)
                signal["valid_until"] = valid_until.isoformat()
            data["signals"].append(signal)

        self._enforce_limit(data)
        self._write_json(data)

        logger.info(f"添加了 {len(signals)} 条信号")
        return len(signals)

    def get_latest_by_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取指定任务的最新信号"""
        data = self._read_json()
        task_signals = [
            s for s in data.get("signals", [])
            if s.get("task_id") == task_id
        ]
        if not task_signals:
            return None

        task_signals.sort(
            key=lambda s: s.get("timestamp", ""), reverse=True
        )
        return task_signals[0]
