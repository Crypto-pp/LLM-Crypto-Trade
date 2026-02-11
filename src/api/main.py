"""
API服务入口

FastAPI应用主文件。
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from ..config import get_settings
from ..utils.logger import setup_logging, get_logger
from .middleware import LoggingMiddleware, RateLimitMiddleware, AuthMiddleware
from .dependencies import close_redis
from ..monitoring import HealthChecker
from ..monitoring.metrics import system_metrics_collector
from ..services.signal_scheduler import SignalScheduler

# 设置日志
setup_logging()
logger = get_logger(__name__)

# 获取配置
settings = get_settings()

# 创建FastAPI应用
app = FastAPI(
    title=settings.system.app_name,
    version=settings.system.app_version,
    description="加密货币自动化分析系统API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.system.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加认证中间件（CORS之后、其他中间件之前）
app.add_middleware(AuthMiddleware)

# 添加日志中间件
app.add_middleware(LoggingMiddleware)

# 添加限流中间件
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# 挂载Prometheus指标端点
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# 健康检查器（从 Settings 获取组装后的连接 URL）
health_checker = HealthChecker(
    database_url=settings.database.async_url.replace("postgresql+asyncpg", "postgresql"),
    redis_url=settings.redis.url,
    rabbitmq_url=settings.rabbitmq.url
)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"{settings.system.app_name} v{settings.system.app_version} 启动中...")
    logger.info(f"环境: {settings.system.environment}")
    logger.info(f"调试模式: {settings.system.debug}")

    # 采集系统指标
    system_metrics_collector.collect_all()

    # 启动信号调度器
    scheduler = SignalScheduler()
    app.state.signal_scheduler = scheduler
    await scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info(f"{settings.system.app_name} 正在关闭...")

    # 停止信号调度器
    scheduler = getattr(app.state, "signal_scheduler", None)
    if scheduler:
        await scheduler.stop()

    await close_redis()


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.system.app_name,
        "version": settings.system.app_version,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return await health_checker.check_all()


# 导入路由
from .routes import market_data, technical_analysis, strategies, backtesting, ai_analysis
from .routes import settings as settings_routes
from .routes import auth as auth_routes

# 注册路由
app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(market_data.router, prefix="/api/v1/market", tags=["Market Data"])
app.include_router(technical_analysis.router, prefix="/api/v1/analysis", tags=["Technical Analysis"])
app.include_router(strategies.router, prefix="/api/v1/strategies", tags=["Strategies"])
app.include_router(backtesting.router, prefix="/api/v1/backtest", tags=["Backtesting"])
app.include_router(ai_analysis.router, prefix="/api/v1/ai", tags=["AI Analysis"])
app.include_router(settings_routes.router, prefix="/api/v1/settings", tags=["Settings"])
