"""
健康检查模块
检查各个组件的健康状态
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
import asyncpg
import aio_pika
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)


class HealthChecker:
    """健康检查器"""

    def __init__(
        self,
        database_url: Optional[str] = None,
        redis_url: Optional[str] = None,
        rabbitmq_url: Optional[str] = None
    ):
        self.database_url = database_url
        self.redis_url = redis_url
        self.rabbitmq_url = rabbitmq_url

    async def check_database(self) -> Dict[str, Any]:
        """检查数据库连接"""
        if not self.database_url:
            return {"status": "unknown", "message": "Database URL not configured"}

        try:
            conn = await asyncpg.connect(self.database_url, timeout=5)
            await conn.execute("SELECT 1")
            await conn.close()
            return {
                "status": "healthy",
                "message": "Database connection successful",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def check_redis(self) -> Dict[str, Any]:
        """检查Redis连接"""
        if not self.redis_url:
            return {"status": "unknown", "message": "Redis URL not configured"}

        try:
            redis = await aioredis.from_url(self.redis_url, decode_responses=True)
            await redis.ping()
            await redis.close()
            return {
                "status": "healthy",
                "message": "Redis connection successful",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def check_rabbitmq(self) -> Dict[str, Any]:
        """检查RabbitMQ连接"""
        if not self.rabbitmq_url:
            return {"status": "unknown", "message": "RabbitMQ URL not configured"}

        try:
            connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                timeout=5
            )
            await connection.close()
            return {
                "status": "healthy",
                "message": "RabbitMQ connection successful",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"RabbitMQ health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"RabbitMQ connection failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def check_external_api(self, url: str, name: str) -> Dict[str, Any]:
        """检查外部API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "message": f"{name} API is accessible",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    else:
                        return {
                            "status": "degraded",
                            "message": f"{name} API returned status {response.status}",
                            "timestamp": datetime.utcnow().isoformat()
                        }
        except Exception as e:
            logger.error(f"{name} API health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"{name} API check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def check_all(self) -> Dict[str, Any]:
        """执行所有健康检查"""
        checks = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_rabbitmq(),
            return_exceptions=True
        )

        database_health, redis_health, rabbitmq_health = checks

        # 处理异常
        if isinstance(database_health, Exception):
            database_health = {"status": "error", "message": str(database_health)}
        if isinstance(redis_health, Exception):
            redis_health = {"status": "error", "message": str(redis_health)}
        if isinstance(rabbitmq_health, Exception):
            rabbitmq_health = {"status": "error", "message": str(rabbitmq_health)}

        # 确定整体状态
        all_healthy = all(
            check.get("status") == "healthy"
            for check in [database_health, redis_health, rabbitmq_health]
        )

        overall_status = "healthy" if all_healthy else "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": database_health,
                "redis": redis_health,
                "rabbitmq": rabbitmq_health
            }
        }
