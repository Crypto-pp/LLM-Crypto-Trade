"""
交易所配置管理器

管理交易所API Key的运行时配置，支持JSON文件持久化。
配置合并逻辑：环境变量作为默认值，JSON文件作为用户覆盖层。
"""

import json
import os
from typing import Dict, Any
from loguru import logger


# 交易所配置字段定义
EXCHANGE_CONFIG_FIELDS = [
    "binance_api_key", "binance_api_secret",
    "okx_api_key", "okx_api_secret", "okx_passphrase",
    "coinbase_api_key", "coinbase_api_secret",
]

# 敏感字段（需脱敏）
SECRET_FIELDS = [
    "binance_api_key", "binance_api_secret",
    "okx_api_key", "okx_api_secret", "okx_passphrase",
    "coinbase_api_key", "coinbase_api_secret",
]

# 交易所元数据
EXCHANGE_META = {
    "binance": {
        "name": "Binance",
        "fields": ["binance_api_key", "binance_api_secret"],
    },
    "okx": {
        "name": "OKX",
        "fields": ["okx_api_key", "okx_api_secret", "okx_passphrase"],
    },
    "coinbase": {
        "name": "Coinbase",
        "fields": ["coinbase_api_key", "coinbase_api_secret"],
    },
}


def _mask_key(key: str) -> str:
    """API Key脱敏：前4位+****+后4位"""
    if not key or len(key) < 8:
        return ""
    return f"{key[:4]}****{key[-4:]}"


def _is_masked(value: str) -> bool:
    """判断值是否为脱敏后的值"""
    return "****" in str(value)


class ExchangeConfigManager:
    """
    交易所配置管理器

    合并环境变量默认值与JSON文件用户配置，JSON优先级更高。
    """

    def __init__(self, config_path: str = "data/exchange_config.json"):
        self._config_path = config_path

    def _read_json(self) -> Dict[str, Any]:
        """读取JSON配置文件，不存在则返回空字典"""
        if not os.path.exists(self._config_path):
            return {}
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"读取交易所配置文件失败: {e}")
            return {}

    def _write_json(self, data: Dict[str, Any]) -> None:
        """写入JSON配置文件"""
        os.makedirs(os.path.dirname(self._config_path) or ".", exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, env_settings=None) -> Dict[str, Any]:
        """
        加载合并后的配置

        Args:
            env_settings: 环境变量配置对象（可选）

        Returns:
            合并后的完整配置字典（JSON覆盖环境变量）
        """
        # 从环境变量提取默认值
        defaults = {}
        for field in EXCHANGE_CONFIG_FIELDS:
            if env_settings is not None:
                defaults[field] = getattr(env_settings, field, "")
            else:
                defaults[field] = ""

        # 读取JSON覆盖层
        overrides = self._read_json()

        # 合并：JSON优先
        merged = {**defaults}
        for key, value in overrides.items():
            if key in EXCHANGE_CONFIG_FIELDS and value is not None:
                merged[key] = value

        return merged

    def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        保存配置到JSON文件

        含 **** 的脱敏值自动跳过（视为未修改）。
        只保存已知字段，忽略未知字段。

        Returns:
            保存后的JSON文件内容
        """
        current = self._read_json()

        for key, value in data.items():
            if key not in EXCHANGE_CONFIG_FIELDS:
                continue
            # 脱敏值跳过
            if key in SECRET_FIELDS and _is_masked(value):
                continue
            current[key] = value

        self._write_json(current)
        return current

    def get_config_response(self, env_settings=None) -> Dict[str, Any]:
        """
        获取前端展示用的配置响应（敏感字段已脱敏）

        Returns:
            结构化配置字典，按交易所分组
        """
        merged = self.load(env_settings)

        exchanges = {}
        for eid, meta in EXCHANGE_META.items():
            exchange_info: Dict[str, Any] = {"name": meta["name"]}
            has_key = False

            for field in meta["fields"]:
                raw_value = merged.get(field, "")
                # 提取字段短名（去掉交易所前缀）
                short_name = field.replace(f"{eid}_", "")

                if field in SECRET_FIELDS and raw_value:
                    exchange_info[short_name] = _mask_key(raw_value)
                    has_key = True
                else:
                    exchange_info[short_name] = raw_value or ""

            exchange_info["has_key"] = has_key
            exchanges[eid] = exchange_info

        return {"exchanges": exchanges}

    def get_effective_settings(self, env_settings=None):
        """
        获取合并后的配置对象

        返回一个简单命名空间对象，属性与配置字段一致。
        """
        from types import SimpleNamespace
        merged = self.load(env_settings)
        return SimpleNamespace(**merged)
