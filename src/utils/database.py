"""
数据库连接管理模块

提供 TimescaleDB/PostgreSQL 数据库连接管理、会话管理、健康检查等功能。
"""

import time
from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from ..config import get_settings
from .logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        """初始化数据库管理器"""
        self.settings = get_settings()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    def _create_engine(self) -> Engine:
        """
        创建数据库引擎

        Returns:
            SQLAlchemy Engine 实例
        """
        db_config = self.settings.database

        engine = create_engine(
            db_config.url,
            poolclass=QueuePool,
            pool_size=db_config.pool_size,
            max_overflow=db_config.max_overflow,
            pool_timeout=db_config.pool_timeout,
            pool_recycle=db_config.pool_recycle,
            pool_pre_ping=True,
            echo=self.settings.system.debug,
            connect_args={
                "connect_timeout": 10,
                "application_name": self.settings.system.app_name,
                "options": "-c statement_timeout=30000",  # 30秒查询超时
            },
        )

        # 添加连接池事件监听
        self._setup_engine_events(engine)

        logger.info(
            f"数据库引擎创建成功 - "
            f"主机: {db_config.host}:{db_config.port}, "
            f"数据库: {db_config.database}, "
            f"连接池: {db_config.pool_size}+{db_config.max_overflow}"
        )

        return engine

    def _setup_engine_events(self, engine: Engine):
        """
        设置引擎事件监听

        Args:
            engine: SQLAlchemy Engine 实例
        """
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """连接建立时的回调"""
            logger.debug("数据库连接已建立")

        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """从连接池获取连接时的回调"""
            logger.debug("从连接池获取连接")

        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """连接归还到连接池时的回调"""
            logger.debug("连接归还到连接池")

    @property
    def engine(self) -> Engine:
        """
        获取数据库引擎

        Returns:
            SQLAlchemy Engine 实例
        """
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """
        获取会话工厂

        Returns:
            SQLAlchemy sessionmaker 实例
        """
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
        return self._session_factory

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        获取数据库会话（上下文管理器）

        Yields:
            SQLAlchemy Session 实例

        Example:
            with db_manager.get_session() as session:
                result = session.execute(text("SELECT 1"))
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话错误: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """
        数据库健康检查

        Returns:
            True 表示健康，False 表示不健康
        """
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.debug("数据库健康检查通过")
            return True
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False

    def execute_with_retry(
        self,
        query: str,
        params: Optional[dict] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> any:
        """
        执行SQL查询，支持重试机制

        Args:
            query: SQL查询语句
            params: 查询参数
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）

        Returns:
            查询结果

        Raises:
            SQLAlchemyError: 数据库错误
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                with self.get_session() as session:
                    result = session.execute(text(query), params or {})
                    return result.fetchall()
            except OperationalError as e:
                last_error = e
                logger.warning(
                    f"数据库查询失败 (尝试 {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # 指数退避
            except SQLAlchemyError as e:
                logger.error(f"数据库查询错误: {e}", exc_info=True)
                raise

        logger.error(f"数据库查询失败，已达最大重试次数: {last_error}")
        raise last_error

    def close(self):
        """关闭数据库连接"""
        if self._engine:
            self._engine.dispose()
            logger.info("数据库连接已关闭")


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
    获取全局数据库管理器实例

    Returns:
        DatabaseManager 实例
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话（依赖注入用）

    Yields:
        SQLAlchemy Session 实例

    Example:
        # FastAPI 依赖注入
        @app.get("/items")
        def get_items(db: Session = Depends(get_db_session)):
            return db.query(Item).all()
    """
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        yield session
