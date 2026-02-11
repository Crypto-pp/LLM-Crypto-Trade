"""
Pytest配置文件

提供测试fixtures和配置。
"""

import pytest
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import Settings
from src.utils.database import DatabaseManager
from src.utils.redis_client import RedisClient


@pytest.fixture(scope="session")
def test_settings():
    """测试配置fixture"""
    return Settings(
        database={
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "test",
            "database": "crypto_test_db",
        },
        redis={
            "host": "localhost",
            "port": 6379,
            "db": 1,  # 使用测试数据库
        },
        system={
            "environment": "testing",
            "debug": True,
        }
    )


@pytest.fixture(scope="session")
def db_manager(test_settings):
    """数据库管理器fixture"""
    manager = DatabaseManager()
    yield manager
    manager.close()


@pytest.fixture(scope="function")
def db_session(db_manager):
    """数据库会话fixture"""
    with db_manager.get_session() as session:
        yield session
        session.rollback()


@pytest.fixture(scope="session")
def redis_client(test_settings):
    """Redis客户端fixture"""
    client = RedisClient()
    yield client
    # 清理测试数据
    client.client.flushdb()
    client.close()


@pytest.fixture(scope="function")
def clean_redis(redis_client):
    """清理Redis数据fixture"""
    redis_client.client.flushdb()
    yield redis_client
    redis_client.client.flushdb()
