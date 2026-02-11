"""
Redis客户端模块测试
"""

import pytest
from src.utils.redis_client import RedisClient, get_redis_client


def test_redis_client_creation():
    """测试Redis客户端创建"""
    client = RedisClient()
    assert client is not None


def test_get_redis_client_singleton():
    """测试Redis客户端单例"""
    client1 = get_redis_client()
    client2 = get_redis_client()
    assert client1 is client2


def test_redis_health_check(redis_client):
    """测试Redis健康检查"""
    is_healthy = redis_client.health_check()
    assert isinstance(is_healthy, bool)


def test_redis_set_get(clean_redis):
    """测试Redis SET/GET操作"""
    clean_redis.set("test_key", "test_value")
    value = clean_redis.get("test_key")
    assert value == "test_value"


def test_redis_delete(clean_redis):
    """测试Redis DELETE操作"""
    clean_redis.set("test_key", "test_value")
    deleted = clean_redis.delete("test_key")
    assert deleted == 1
    value = clean_redis.get("test_key")
    assert value is None


def test_redis_exists(clean_redis):
    """测试Redis EXISTS操作"""
    clean_redis.set("test_key", "test_value")
    exists = clean_redis.exists("test_key")
    assert exists == 1


def test_redis_expire(clean_redis):
    """测试Redis EXPIRE操作"""
    clean_redis.set("test_key", "test_value")
    result = clean_redis.expire("test_key", 60)
    assert result is True
    ttl = clean_redis.ttl("test_key")
    assert ttl > 0


def test_redis_hash_operations(clean_redis):
    """测试Redis Hash操作"""
    clean_redis.hset("test_hash", "field1", "value1")
    value = clean_redis.hget("test_hash", "field1")
    assert value == "value1"

    all_fields = clean_redis.hgetall("test_hash")
    assert "field1" in all_fields


def test_redis_list_operations(clean_redis):
    """测试Redis List操作"""
    clean_redis.lpush("test_list", "value1", "value2")
    values = clean_redis.lrange("test_list", 0, -1)
    assert len(values) == 2


def test_redis_set_operations(clean_redis):
    """测试Redis Set操作"""
    clean_redis.sadd("test_set", "member1", "member2")
    members = clean_redis.smembers("test_set")
    assert len(members) == 2
    assert clean_redis.sismember("test_set", "member1")


def test_redis_json_operations(clean_redis):
    """测试Redis JSON操作"""
    data = {"key": "value", "number": 123}
    clean_redis.set_json("test_json", data)
    retrieved = clean_redis.get_json("test_json")
    assert retrieved == data


def test_redis_cache_operations(clean_redis):
    """测试Redis缓存操作"""
    data = {"test": "data"}
    clean_redis.cache_set("cache_key", data, ttl=60)
    cached = clean_redis.cache_get("cache_key")
    assert cached == data


def test_redis_lock(clean_redis):
    """测试Redis分布式锁"""
    with clean_redis.lock("test_lock", timeout=10):
        # 在锁内执行操作
        clean_redis.set("locked_key", "locked_value")

    value = clean_redis.get("locked_key")
    assert value == "locked_value"
