"""
FastAPI依赖注入
提供数据库会话、Redis客户端等依赖
"""

import os
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from redis import asyncio as aioredis
import logging

logger = logging.getLogger(__name__)

# 数据库引擎
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://crypto_user:password@localhost:5432/crypto_trade')
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Redis客户端
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_client = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_redis():
    """获取Redis客户端"""
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(REDIS_URL, decode_responses=True)
    return redis_client


async def close_redis():
    """关闭Redis连接"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
