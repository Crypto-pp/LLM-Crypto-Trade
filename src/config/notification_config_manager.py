"""
通知渠道配置管理器

管理飞书和Telegram通知渠道的配置，支持JSON文件持久化。
参照 SignalConfigManager 模式实现。
"""

import json
import os
from typing import Dict, Any, List, Optional
from loguru import logger


# 支持的通知渠道类型
CHANNEL_TYPES = ["telegram", "feishu"]


class NotificationConfigManager:
    """
    通知渠道配置管理器

    管理通知渠道的CRUD操作，持久化到JSON文件。
    配置结构：
    {
        "channels": [
            {
                "id": "telegram_1",
                "type": "telegram",
                "name": "我的TG机器人",
                "enabled": true,
                "config": {
                    "bot_token": "xxx",
                    "chat_id": "xxx"
                }
            },
            {
                "id": "feishu_1",
                "type": "feishu",
                "name": "飞书交易群",
                "enabled": true,
                "config": {
                    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
                    "secret": ""
                }
            }
        ],
        "settings": {
            "notify_on_buy": true,
            "notify_on_sell": true,
            "notify_on_hold": false
        }
    }
    """

    def __init__(self, config_path: str = "data/notification_config.json"):
        self._config_path = config_path

    def _read_json(self) -> Dict[str, Any]:
        """读取JSON配置文件，不存在则返回默认结构"""
        if not os.path.exists(self._config_path):
            return self._default_config()
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "channels" not in data:
                    data["channels"] = []
                if "settings" not in data:
                    data["settings"] = self._default_settings()
                return data
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"读取通知配置文件失败: {e}")
            return self._default_config()

    def _write_json(self, data: Dict[str, Any]) -> None:
        """写入JSON配置文件"""
        os.makedirs(os.path.dirname(self._config_path) or ".", exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _default_settings() -> Dict[str, bool]:
        return {
            "notify_on_buy": True,
            "notify_on_sell": True,
            "notify_on_hold": False,
        }

    def _default_config(self) -> Dict[str, Any]:
        return {
            "channels": [],
            "settings": self._default_settings(),
        }

    # ========== 渠道 CRUD ==========

    def get_channels(self) -> List[Dict[str, Any]]:
        """获取所有通知渠道"""
        return self._read_json().get("channels", [])

    def get_channel(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取单个渠道"""
        for ch in self.get_channels():
            if ch.get("id") == channel_id:
                return ch
        return None

    def get_enabled_channels(self) -> List[Dict[str, Any]]:
        """获取所有已启用的渠道"""
        return [ch for ch in self.get_channels() if ch.get("enabled")]

    def add_channel(self, channel: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加通知渠道

        自动生成ID，验证类型和必填字段。
        """
        ch_type = channel.get("type", "")
        if ch_type not in CHANNEL_TYPES:
            raise ValueError(f"不支持的渠道类型: {ch_type}，可选: {CHANNEL_TYPES}")

        config = channel.get("config", {})
        self._validate_channel_config(ch_type, config)

        data = self._read_json()
        # 生成自增ID
        existing_ids = [
            ch["id"] for ch in data["channels"]
            if ch.get("id", "").startswith(f"{ch_type}_")
        ]
        idx = len(existing_ids) + 1
        channel_id = f"{ch_type}_{idx}"

        new_channel = {
            "id": channel_id,
            "type": ch_type,
            "name": channel.get("name", f"{ch_type}_{idx}"),
            "enabled": channel.get("enabled", True),
            "config": config,
        }

        data["channels"].append(new_channel)
        self._write_json(data)
        logger.info(f"添加通知渠道: {channel_id} ({ch_type})")
        return new_channel

    def update_channel(
        self, channel_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """更新通知渠道"""
        data = self._read_json()
        channels = data.get("channels", [])

        for i, ch in enumerate(channels):
            if ch.get("id") != channel_id:
                continue

            if "type" in updates and updates["type"] not in CHANNEL_TYPES:
                raise ValueError(f"不支持的渠道类型: {updates['type']}")

            if "config" in updates:
                ch_type = updates.get("type", ch["type"])
                self._validate_channel_config(ch_type, updates["config"])

            allowed = {"name", "enabled", "config", "type"}
            for key, value in updates.items():
                if key in allowed:
                    channels[i][key] = value

            self._write_json(data)
            logger.info(f"更新通知渠道 {channel_id}: {list(updates.keys())}")
            return channels[i]

        return None

    def delete_channel(self, channel_id: str) -> bool:
        """删除通知渠道"""
        data = self._read_json()
        original_len = len(data["channels"])
        data["channels"] = [
            ch for ch in data["channels"] if ch.get("id") != channel_id
        ]
        if len(data["channels"]) < original_len:
            self._write_json(data)
            logger.info(f"删除通知渠道: {channel_id}")
            return True
        return False

    # ========== 全局设置 ==========

    def get_settings(self) -> Dict[str, bool]:
        """获取通知全局设置"""
        return self._read_json().get("settings", self._default_settings())

    def update_settings(self, updates: Dict[str, bool]) -> Dict[str, bool]:
        """更新通知全局设置"""
        data = self._read_json()
        allowed = {"notify_on_buy", "notify_on_sell", "notify_on_hold"}
        for key, value in updates.items():
            if key in allowed and isinstance(value, bool):
                data["settings"][key] = value
        self._write_json(data)
        logger.info(f"更新通知设置: {updates}")
        return data["settings"]

    # ========== 获取完整配置（API响应用） ==========

    def get_config_response(self) -> Dict[str, Any]:
        """获取完整配置（敏感字段脱敏）"""
        data = self._read_json()
        channels = []
        for ch in data.get("channels", []):
            safe_ch = {**ch}
            safe_config = {**ch.get("config", {})}
            # 脱敏 bot_token 和 secret
            if "bot_token" in safe_config and safe_config["bot_token"]:
                safe_config["bot_token"] = self._mask(safe_config["bot_token"])
            if "secret" in safe_config and safe_config["secret"]:
                safe_config["secret"] = self._mask(safe_config["secret"])
            safe_ch["config"] = safe_config
            channels.append(safe_ch)
        return {
            "channels": channels,
            "settings": data.get("settings", self._default_settings()),
        }

    @staticmethod
    def _mask(value: str) -> str:
        """脱敏处理，保留前4位和后4位"""
        if len(value) <= 8:
            return "****"
        return value[:4] + "****" + value[-4:]

    @staticmethod
    def _validate_channel_config(ch_type: str, config: Dict[str, Any]) -> None:
        """验证渠道配置必填字段"""
        if ch_type == "telegram":
            if not config.get("bot_token"):
                raise ValueError("Telegram渠道必须提供 bot_token")
            if not config.get("chat_id"):
                raise ValueError("Telegram渠道必须提供 chat_id")
        elif ch_type == "feishu":
            if not config.get("webhook_url"):
                raise ValueError("飞书渠道必须提供 webhook_url")
