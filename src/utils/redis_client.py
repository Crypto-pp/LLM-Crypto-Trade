"""
Redis客户端模块

提供 Redis 连接管理、常用操作封装、分布式锁等功能。
"""

import json
import time
from typing import Optional, Any, Dict, List
from contextlib import contextmanager
import redis
from redis.connection import ConnectionPool
from redis.exceptions import RedisError, LockError

from ..config import get_settings
from .logger import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis客户端封装"""

    def __init__(self):
        """初始化Redis客户端"""
        self.settings = get_settings()
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None

    def _create_pool(self) -> ConnectionPool:
        """
        创建Redis连接池

        Returns:
            Redis ConnectionPool 实例
        """
        redis_config = self.settings.redis

        pool = ConnectionPool(
            host=redis_config.host,
            port=redis_config.port,
            password=redis_config.password,
            db=redis_config.db,
            max_connections=redis_config.max_connections,
            socket_timeout=redis_config.socket_timeout,
            socket_connect_timeout=redis_config.socket_connect_timeout,
            decode_responses=True,
        )

        logger.info(
            f"Redis连接池创建成功 - "
            f"主机: {redis_config.host}:{redis_config.port}, "
            f"数据库: {redis_config.db}"
        )

        return pool

    @property
    def client(self) -> redis.Redis:
        """
        获取Redis客户端

        Returns:
            Redis客户端实例
        """
        if self._client is None:
            if self._pool is None:
                self._pool = self._create_pool()
            self._client = redis.Redis(connection_pool=self._pool)
        return self._client

    def health_check(self) -> bool:
        """
        Redis健康检查

        Returns:
            True 表示健康，False 表示不健康
        """
        try:
            self.client.ping()
            logger.debug("Redis健康检查通过")
            return True
        except RedisError as e:
            logger.error(f"Redis健康检查失败: {e}")
            return False

    # ==================== 基本操作 ====================

    def get(self, key: str) -> Optional[str]:
        """
        获取键值

        Args:
            key: 键名

        Returns:
            键值，不存在返回None
        """
        try:
            return self.client.get(key)
        except RedisError as e:
            logger.error(f"Redis GET 错误 [{key}]: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        设置键值

        Args:
            key: 键名
            value: 键值
            ex: 过期时间（秒）
            px: 过期时间（毫秒）
            nx: 仅当键不存在时设置
            xx: 仅当键存在时设置

        Returns:
            True 表示成功，False 表示失败
        """
        try:
            return self.client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        except RedisError as e:
            logger.error(f"Redis SET 错误 [{key}]: {e}")
            return False

    def delete(self, *keys: str) -> int:
        """
        删除键

        Args:
            keys: 键名列表

        Returns:
            删除的键数量
        """
        try:
            return self.client.delete(*keys)
        except RedisError as e:
            logger.error(f"Redis DELETE 错误: {e}")
            return 0

    def exists(self, *keys: str) -> int:
        """
        检查键是否存在

        Args:
            keys: 键名列表

        Returns:
            存在的键数量
        """
        try:
            return self.client.exists(*keys)
        except RedisError as e:
            logger.error(f"Redis EXISTS 错误: {e}")
            return 0

    def expire(self, key: str, seconds: int) -> bool:
        """
        设置键过期时间

        Args:
            key: 键名
            seconds: 过期时间（秒）

        Returns:
            True 表示成功，False 表示失败
        """
        try:
            return self.client.expire(key, seconds)
        except RedisError as e:
            logger.error(f"Redis EXPIRE 错误 [{key}]: {e}")
            return False

    def ttl(self, key: str) -> int:
        """
        获取键剩余过期时间

        Args:
            key: 键名

        Returns:
            剩余秒数，-1表示永不过期，-2表示不存在
        """
        try:
            return self.client.ttl(key)
        except RedisError as e:
            logger.error(f"Redis TTL 错误 [{key}]: {e}")
            return -2

    # ==================== Hash操作 ====================

    def hget(self, name: str, key: str) -> Optional[str]:
        """
        获取Hash字段值

        Args:
            name: Hash名称
            key: 字段名

        Returns:
            字段值，不存在返回None
        """
        try:
            return self.client.hget(name, key)
        except RedisError as e:
            logger.error(f"Redis HGET 错误 [{name}.{key}]: {e}")
            return None

    def hset(self, name: str, key: str, value: Any) -> int:
        """
        设置Hash字段值

        Args:
            name: Hash名称
            key: 字段名
            value: 字段值

        Returns:
            1表示新增，0表示更新
        """
        try:
            return self.client.hset(name, key, value)
        except RedisError as e:
            logger.error(f"Redis HSET 错误 [{name}.{key}]: {e}")
            return 0

    def hgetall(self, name: str) -> Dict[str, str]:
        """
        获取Hash所有字段

        Args:
            name: Hash名称

        Returns:
            字段字典
        """
        try:
            return self.client.hgetall(name)
        except RedisError as e:
            logger.error(f"Redis HGETALL 错误 [{name}]: {e}")
            return {}

    def hmset(self, name: str, mapping: Dict[str, Any]) -> bool:
        """
        批量设置Hash字段

        Args:
            name: Hash名称
            mapping: 字段字典

        Returns:
            True 表示成功
        """
        try:
            return self.client.hset(name, mapping=mapping)
        except RedisError as e:
            logger.error(f"Redis HMSET 错误 [{name}]: {e}")
            return False

    def hdel(self, name: str, *keys: str) -> int:
        """
        删除Hash字段

        Args:
            name: Hash名称
            keys: 字段名列表

        Returns:
            删除的字段数量
        """
        try:
            return self.client.hdel(name, *keys)
        except RedisError as e:
            logger.error(f"Redis HDEL 错误 [{name}]: {e}")
            return 0

    # ==================== List操作 ====================

    def lpush(self, name: str, *values: Any) -> int:
        """
        从左侧推入列表

        Args:
            name: 列表名称
            values: 值列表

        Returns:
            列表长度
        """
        try:
            return self.client.lpush(name, *values)
        except RedisError as e:
            logger.error(f"Redis LPUSH 错误 [{name}]: {e}")
            return 0

    def rpush(self, name: str, *values: Any) -> int:
        """
        从右侧推入列表

        Args:
            name: 列表名称
            values: 值列表

        Returns:
            列表长度
        """
        try:
            return self.client.rpush(name, *values)
        except RedisError as e:
            logger.error(f"Redis RPUSH 错误 [{name}]: {e}")
            return 0

    def lrange(self, name: str, start: int, end: int) -> List[str]:
        """
        获取列表范围

        Args:
            name: 列表名称
            start: 起始索引
            end: 结束索引

        Returns:
            值列表
        """
        try:
            return self.client.lrange(name, start, end)
        except RedisError as e:
            logger.error(f"Redis LRANGE 错误 [{name}]: {e}")
            return []

    def ltrim(self, name: str, start: int, end: int) -> bool:
        """
        修剪列表

        Args:
            name: 列表名称
            start: 起始索引
            end: 结束索引

        Returns:
            True 表示成功
        """
        try:
            return self.client.ltrim(name, start, end)
        except RedisError as e:
            logger.error(f"Redis LTRIM 错误 [{name}]: {e}")
            return False

    # ==================== Set操作 ====================

    def sadd(self, name: str, *values: Any) -> int:
        """
        添加集合成员

        Args:
            name: 集合名称
            values: 值列表

        Returns:
            添加的成员数量
        """
        try:
            return self.client.sadd(name, *values)
        except RedisError as e:
            logger.error(f"Redis SADD 错误 [{name}]: {e}")
            return 0

    def smembers(self, name: str) -> set:
        """
        获取集合所有成员

        Args:
            name: 集合名称

        Returns:
            成员集合
        """
        try:
            return self.client.smembers(name)
        except RedisError as e:
            logger.error(f"Redis SMEMBERS 错误 [{name}]: {e}")
            return set()

    def sismember(self, name: str, value: Any) -> bool:
        """
        检查是否为集合成员

        Args:
            name: 集合名称
            value: 值

        Returns:
            True 表示是成员
        """
        try:
            return self.client.sismember(name, value)
        except RedisError as e:
            logger.error(f"Redis SISMEMBER 错误 [{name}]: {e}")
            return False

    # ==================== Sorted Set操作 ====================

    def zadd(self, name: str, mapping: Dict[Any, float]) -> int:
        """
        添加有序集合成员

        Args:
            name: 有序集合名称
            mapping: {成员: 分数} 字典

        Returns:
            添加的成员数量
        """
        try:
            return self.client.zadd(name, mapping)
        except RedisError as e:
            logger.error(f"Redis ZADD 错误 [{name}]: {e}")
            return 0

    def zrange(
        self,
        name: str,
        start: int,
        end: int,
        withscores: bool = False,
    ) -> List:
        """
        获取有序集合范围

        Args:
            name: 有序集合名称
            start: 起始索引
            end: 结束索引
            withscores: 是否返回分数

        Returns:
            成员列表
        """
        try:
            return self.client.zrange(name, start, end, withscores=withscores)
        except RedisError as e:
            logger.error(f"Redis ZRANGE 错误 [{name}]: {e}")
            return []

    # ==================== JSON操作 ====================

    def get_json(self, key: str) -> Optional[Any]:
        """
        获取JSON值

        Args:
            key: 键名

        Returns:
            解析后的JSON对象
        """
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误 [{key}]: {e}")
        return None

    def set_json(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
    ) -> bool:
        """
        设置JSON值

        Args:
            key: 键名
            value: Python对象
            ex: 过期时间（秒）

        Returns:
            True 表示成功
        """
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            return self.set(key, json_str, ex=ex)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON序列化错误 [{key}]: {e}")
            return False

    # ==================== 分布式锁 ====================

    @contextmanager
    def lock(
        self,
        name: str,
        timeout: Optional[float] = None,
        blocking: bool = True,
        blocking_timeout: Optional[float] = None,
    ):
        """
        分布式锁上下文管理器

        Args:
            name: 锁名称
            timeout: 锁超时时间（秒）
            blocking: 是否阻塞等待
            blocking_timeout: 阻塞超时时间（秒）

        Yields:
            锁对象

        Example:
            with redis_client.lock("my_lock", timeout=10):
                # 执行需要加锁的操作
                pass
        """
        lock_obj = self.client.lock(
            name,
            timeout=timeout,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
        )
        try:
            acquired = lock_obj.acquire()
            if not acquired:
                raise LockError(f"无法获取锁: {name}")
            logger.debug(f"获取锁成功: {name}")
            yield lock_obj
        finally:
            try:
                lock_obj.release()
                logger.debug(f"释放锁成功: {name}")
            except LockError:
                logger.warning(f"锁已过期或不存在: {name}")

    # ==================== 缓存操作 ====================

    def cache_get(self, key: str) -> Optional[Any]:
        """
        获取缓存（自动JSON解析）

        Args:
            key: 缓存键

        Returns:
            缓存值
        """
        return self.get_json(key)

    def cache_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        设置缓存（自动JSON序列化）

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）

        Returns:
            True 表示成功
        """
        return self.set_json(key, value, ex=ttl)

    def close(self):
        """关闭Redis连接"""
        if self._client:
            self._client.close()
            logger.info("Redis连接已关闭")


# 全局Redis客户端实例
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """
    获取全局Redis客户端实例

    Returns:
        RedisClient 实例
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client