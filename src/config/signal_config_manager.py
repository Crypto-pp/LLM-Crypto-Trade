"""
信号监控配置管理器

管理信号监控任务的配置，支持JSON文件持久化。
参照 ExchangeConfigManager 模式实现。
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from loguru import logger


# 可选策略
STRATEGY_OPTIONS = ["趋势跟踪", "均值回归", "动量策略", "AI分析"]

# 可选K线周期
INTERVAL_OPTIONS = ["1m", "5m", "15m", "1h", "4h", "1d"]


class SignalConfigManager:
    """
    信号监控配置管理器

    管理监控任务的CRUD操作，持久化到JSON文件。
    """

    def __init__(self, config_path: str = "data/signal_config.json"):
        self._config_path = config_path

    def _read_json(self) -> Dict[str, Any]:
        """读取JSON配置文件，不存在则返回默认结构"""
        if not os.path.exists(self._config_path):
            return {"tasks": []}
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "tasks" not in data:
                    data["tasks"] = []
                return data
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"读取信号配置文件失败: {e}")
            return {"tasks": []}

    def _write_json(self, data: Dict[str, Any]) -> None:
        """写入JSON配置文件"""
        os.makedirs(os.path.dirname(self._config_path) or ".", exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取所有监控任务"""
        data = self._read_json()
        return data.get("tasks", [])

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取单个任务"""
        for task in self.get_tasks():
            if task.get("id") == task_id:
                return task
        return None

    def add_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加监控任务

        自动生成UUID和创建时间。
        验证 strategy 和 interval 是否合法。
        """
        symbol = task.get("symbol", "").strip()
        strategy = task.get("strategy", "")
        interval = task.get("interval", "")

        if not symbol:
            raise ValueError("交易对不能为空")
        if strategy not in STRATEGY_OPTIONS:
            raise ValueError(f"不支持的策略: {strategy}，可选: {STRATEGY_OPTIONS}")
        if interval not in INTERVAL_OPTIONS:
            raise ValueError(f"不支持的周期: {interval}，可选: {INTERVAL_OPTIONS}")

        new_task = {
            "id": str(uuid.uuid4()),
            "symbol": symbol,
            "strategy": strategy,
            "interval": interval,
            "enabled": task.get("enabled", True),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_run": None,
            "last_signal": None,
        }

        data = self._read_json()
        data["tasks"].append(new_task)
        self._write_json(data)

        logger.info(f"添加信号监控任务: {symbol} {strategy} {interval}")
        return new_task

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新监控任务

        支持更新 symbol/strategy/interval/enabled/last_run/last_signal 字段。
        """
        data = self._read_json()
        tasks = data.get("tasks", [])

        for i, task in enumerate(tasks):
            if task.get("id") != task_id:
                continue

            # 验证可更新字段
            if "strategy" in updates and updates["strategy"] not in STRATEGY_OPTIONS:
                raise ValueError(f"不支持的策略: {updates['strategy']}")
            if "interval" in updates and updates["interval"] not in INTERVAL_OPTIONS:
                raise ValueError(f"不支持的周期: {updates['interval']}")

            allowed_fields = {
                "symbol", "strategy", "interval", "enabled",
                "last_run", "last_signal",
            }
            for key, value in updates.items():
                if key in allowed_fields:
                    tasks[i][key] = value

            self._write_json(data)
            logger.info(f"更新信号监控任务 {task_id}: {updates}")
            return tasks[i]

        return None

    def delete_task(self, task_id: str) -> bool:
        """删除监控任务"""
        data = self._read_json()
        original_len = len(data["tasks"])
        data["tasks"] = [t for t in data["tasks"] if t.get("id") != task_id]

        if len(data["tasks"]) < original_len:
            self._write_json(data)
            logger.info(f"删除信号监控任务: {task_id}")
            return True
        return False
