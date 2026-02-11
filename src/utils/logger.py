"""
日志工具模块

使用 loguru 实现结构化日志系统，支持 JSON 格式输出、日志轮转等功能。
"""

import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
from contextvars import ContextVar

from ..config import get_settings


# 上下文变量，用于存储请求级别的信息
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def serialize_record(record: Dict[str, Any]) -> str:
    """
    序列化日志记录为 JSON 格式

    Args:
        record: 日志记录字典

    Returns:
        JSON 格式的日志字符串
    """
    # 提取基本信息
    log_data = {
        "timestamp": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "level": record["level"].name,
        "logger": record["name"],
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }

    # 添加上下文信息
    request_id = request_id_var.get()
    user_id = user_id_var.get()

    if request_id:
        log_data["request_id"] = request_id
    if user_id:
        log_data["user_id"] = user_id

    # 添加额外字段
    if record["extra"]:
        log_data["extra"] = record["extra"]

    # 添加异常信息
    if record["exception"]:
        log_data["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback,
        }

    return json.dumps(log_data, ensure_ascii=False)


def text_format(record: Dict[str, Any]) -> str:
    """
    文本格式化日志

    Args:
        record: 日志记录字典

    Returns:
        格式化的文本日志
    """
    # 基本格式
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    )

    # 添加上下文信息
    request_id = request_id_var.get()
    if request_id:
        fmt += f"<yellow>req_id={request_id}</yellow> | "

    # 添加消息
    fmt += "<level>{message}</level>\n"

    # 添加异常信息
    if record["exception"]:
        fmt += "{exception}\n"

    return fmt


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_dir: Optional[str] = None,
) -> None:
    """
    设置日志系统

    Args:
        log_level: 日志级别，默认从配置读取
        log_format: 日志格式 (json/text)，默认从配置读取
        log_dir: 日志目录，默认从配置读取
    """
    settings = get_settings()

    # 使用参数或配置
    level = log_level or settings.logging.level
    format_type = log_format or settings.logging.format
    log_directory = log_dir or settings.logging.log_dir

    # 移除默认的 handler
    logger.remove()

    # 控制台输出
    if settings.logging.console_output:
        if format_type == "json":
            logger.add(
                sys.stdout,
                level=level,
                format=lambda record: serialize_record(record) + "\n",
                colorize=False,
            )
        else:
            logger.add(
                sys.stdout,
                level=level,
                format=text_format,
                colorize=True,
            )

    # 创建日志目录
    log_path = Path(log_directory)
    log_path.mkdir(parents=True, exist_ok=True)

    # 文件输出 - 所有日志
    logger.add(
        log_path / "app_{time:YYYY-MM-DD}.log",
        level=level,
        format=lambda record: serialize_record(record) + "\n" if format_type == "json" else text_format(record),
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        compression=settings.logging.compression,
        encoding="utf-8",
    )

    # 文件输出 - 错误日志
    logger.add(
        log_path / "error_{time:YYYY-MM-DD}.log",
        level="ERROR",
        format=lambda record: serialize_record(record) + "\n" if format_type == "json" else text_format(record),
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        compression=settings.logging.compression,
        encoding="utf-8",
    )

    logger.info(f"日志系统初始化完成 - 级别: {level}, 格式: {format_type}, 目录: {log_directory}")


def get_logger(name: Optional[str] = None):
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        配置好的日志记录器
    """
    if name:
        return logger.bind(name=name)
    return logger


def set_request_context(request_id: Optional[str] = None, user_id: Optional[str] = None):
    """
    设置请求上下文信息

    Args:
        request_id: 请求ID
        user_id: 用户ID
    """
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context():
    """清除请求上下文信息"""
    request_id_var.set(None)
    user_id_var.set(None)
