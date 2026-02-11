"""
日志工具模块测试
"""

import pytest
from pathlib import Path
from src.utils.logger import get_logger, setup_logging, set_request_context, clear_request_context


def test_setup_logging():
    """测试日志系统设置"""
    setup_logging(log_level="DEBUG", log_format="text")
    logger = get_logger(__name__)
    assert logger is not None


def test_get_logger():
    """测试获取日志记录器"""
    logger = get_logger("test_module")
    assert logger is not None


def test_logger_info():
    """测试INFO级别日志"""
    logger = get_logger(__name__)
    logger.info("测试INFO日志")


def test_logger_error():
    """测试ERROR级别日志"""
    logger = get_logger(__name__)
    logger.error("测试ERROR日志")


def test_request_context():
    """测试请求上下文"""
    set_request_context(request_id="test-123", user_id="user-456")
    logger = get_logger(__name__)
    logger.info("带上下文的日志")
    clear_request_context()


def test_logger_with_exception():
    """测试异常日志"""
    logger = get_logger(__name__)
    try:
        raise ValueError("测试异常")
    except ValueError:
        logger.exception("捕获到异常")
