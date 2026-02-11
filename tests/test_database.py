"""
数据库连接模块测试
"""

import pytest
from sqlalchemy import text
from src.utils.database import DatabaseManager, get_db_manager


def test_database_manager_creation():
    """测试数据库管理器创建"""
    db_manager = DatabaseManager()
    assert db_manager is not None


def test_get_db_manager_singleton():
    """测试数据库管理器单例"""
    manager1 = get_db_manager()
    manager2 = get_db_manager()
    assert manager1 is manager2


def test_database_health_check(db_manager):
    """测试数据库健康检查"""
    is_healthy = db_manager.health_check()
    assert isinstance(is_healthy, bool)


def test_database_session(db_manager):
    """测试数据库会话"""
    with db_manager.get_session() as session:
        result = session.execute(text("SELECT 1 as num"))
        row = result.fetchone()
        assert row[0] == 1


def test_execute_with_retry(db_manager):
    """测试带重试的查询执行"""
    result = db_manager.execute_with_retry("SELECT 1 as num")
    assert len(result) > 0
    assert result[0][0] == 1
