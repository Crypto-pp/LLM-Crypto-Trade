"""
认证配置管理器

管理用户凭据，支持JSON文件持久化。
参照 SignalConfigManager 模式实现。
"""

import hashlib
import json
import os
import secrets
from typing import Dict, Any, Tuple

from loguru import logger


class AuthConfigManager:
    """
    认证配置管理器

    单用户系统，密码使用 pbkdf2_hmac 哈希存储，持久化到JSON文件。
    """

    DEFAULT_USERNAME = "admin"
    DEFAULT_PASSWORD = "crypto2024"

    def __init__(self, config_path: str = "data/auth_config.json"):
        self._config_path = config_path
        self._ensure_default()

    def _read_json(self) -> Dict[str, Any]:
        """读取JSON配置文件，不存在则返回空字典"""
        if not os.path.exists(self._config_path):
            return {}
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"读取认证配置文件失败: {e}")
            return {}

    def _write_json(self, data: Dict[str, Any]) -> None:
        """写入JSON配置文件"""
        os.makedirs(os.path.dirname(self._config_path) or ".", exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """使用 pbkdf2_hmac 哈希密码"""
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        )
        return dk.hex()

    def _ensure_default(self) -> None:
        """初始化时写入默认凭据（仅在配置文件不存在时）"""
        data = self._read_json()
        if data.get("username"):
            return

        salt = secrets.token_hex(16)
        password_hash = self._hash_password(self.DEFAULT_PASSWORD, salt)

        data = {
            "username": self.DEFAULT_USERNAME,
            "password_hash": password_hash,
            "salt": salt,
            "must_change_password": True,
        }
        self._write_json(data)
        logger.info("已初始化默认认证凭据")

    def verify_password(self, username: str, password: str) -> Tuple[bool, bool]:
        """
        验证用户名和密码

        返回 (验证通过, 是否需要修改密码)
        """
        data = self._read_json()
        if not data.get("username") or data["username"] != username:
            return False, False

        password_hash = self._hash_password(password, data["salt"])
        if password_hash != data["password_hash"]:
            return False, False

        return True, data.get("must_change_password", False)

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        修改密码

        验证旧密码后更新为新密码，重置 must_change_password 标志。
        """
        ok, _ = self.verify_password(username, old_password)
        if not ok:
            return False

        salt = secrets.token_hex(16)
        password_hash = self._hash_password(new_password, salt)

        data = self._read_json()
        data["password_hash"] = password_hash
        data["salt"] = salt
        data["must_change_password"] = False
        self._write_json(data)

        logger.info(f"用户 {username} 已修改密码")
        return True
