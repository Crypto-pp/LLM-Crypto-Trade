"""
认证API路由

提供登录、登出、修改密码和用户信息接口。
"""

import secrets
import time
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from src.config.auth_config_manager import AuthConfigManager

router = APIRouter(tags=["auth"])

_auth_config_manager = AuthConfigManager()

# 内存Token存储：{token: {"username": str, "expires_at": float}}
_active_tokens: Dict[str, Dict[str, Any]] = {}

TOKEN_EXPIRY_SECONDS = 24 * 60 * 60  # 24小时


def _create_token(username: str) -> str:
    """生成Bearer Token并存储"""
    token = secrets.token_hex(32)
    _active_tokens[token] = {
        "username": username,
        "expires_at": time.time() + TOKEN_EXPIRY_SECONDS,
    }
    return token


def verify_token(token: str) -> Dict[str, Any] | None:
    """验证Token有效性，返回用户信息或None"""
    info = _active_tokens.get(token)
    if not info:
        return None
    if time.time() > info["expires_at"]:
        _active_tokens.pop(token, None)
        return None
    return info


def _get_current_user(request: Request) -> Dict[str, Any]:
    """从请求中提取已认证用户信息"""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="未认证")
    return user


@router.post("/login")
async def login(data: dict):
    """用户登录，返回Bearer Token"""
    username = data.get("username", "")
    password = data.get("password", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")

    ok, must_change = _auth_config_manager.verify_password(username, password)
    if not ok:
        logger.warning(f"登录失败: {username}")
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = _create_token(username)
    logger.info(f"用户 {username} 登录成功")

    return {
        "token": token,
        "username": username,
        "must_change_password": must_change,
    }


@router.post("/change-password")
async def change_password(data: dict, request: Request):
    """修改密码（需认证）"""
    user = _get_current_user(request)

    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")

    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="旧密码和新密码不能为空")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于6位")

    ok = _auth_config_manager.change_password(user["username"], old_password, new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="旧密码错误")

    # 修改密码后注销当前Token，要求重新登录
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        _active_tokens.pop(auth_header[7:], None)

    return {"success": True, "message": "密码修改成功，请重新登录"}


@router.post("/logout")
async def logout(request: Request):
    """注销Token"""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        _active_tokens.pop(token, None)
    return {"success": True}


@router.get("/me")
async def get_current_user(request: Request):
    """获取当前用户信息"""
    user = _get_current_user(request)
    return {
        "username": user["username"],
    }
