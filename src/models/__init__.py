"""
数据模型模块

提供数据库表的ORM模型定义。
"""

from .base import Base, TimestampMixin

__all__ = [
    "Base",
    "TimestampMixin",
]
