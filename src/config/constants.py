"""
系统常量定义

定义系统中使用的各种常量，包括时间周期、交易所名称、表名等。
"""

from enum import Enum


class TimeInterval(str, Enum):
    """时间周期常量"""
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"


class ExchangeName(str, Enum):
    """交易所名称常量"""
    BINANCE = "binance"
    OKX = "okx"
    COINBASE = "coinbase"
    HUOBI = "huobi"
    KRAKEN = "kraken"


class TableName(str, Enum):
    """数据库表名常量"""
    # TimescaleDB 时序表
    KLINES = "klines"
    TICKS = "ticks"
    ORDERBOOK_SNAPSHOTS = "orderbook_snapshots"
    INDICATORS = "indicators"
    SIGNALS = "signals"

    # PostgreSQL 关系表
    EXCHANGES = "exchanges"
    SYMBOLS = "symbols"
    STRATEGIES = "strategies"
    COLLECTION_TASKS = "collection_tasks"
    DATA_QUALITY_METRICS = "data_quality_metrics"
    ALERT_RULES = "alert_rules"
    ALERT_HISTORY = "alert_history"


class RedisKeyPrefix(str, Enum):
    """Redis键前缀常量"""
    # 实时价格
    PRICE_LATEST = "price:latest"

    # K线数据缓存
    KLINES = "klines"

    # 技术指标缓存
    INDICATOR = "indicator"

    # 热门交易对
    POPULAR_SYMBOLS = "popular:symbols"

    # 查询结果缓存
    QUERY = "query"

    # 会话数据
    SESSION = "session"

    # 分布式锁
    LOCK = "lock"

    # 消息队列（Redis Streams）
    STREAM_MARKET_KLINE = "stream:market:kline"
    STREAM_MARKET_TICK = "stream:market:tick"
    STREAM_ANALYSIS_RESULT = "stream:analysis:result"


class SignalAction(str, Enum):
    """交易信号动作"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalStatus(str, Enum):
    """信号状态"""
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class SignalPriority(str, Enum):
    """信号优先级"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(str, Enum):
    """任务类型"""
    REALTIME = "realtime"
    HISTORICAL = "historical"
    BACKFILL = "backfill"


# 缓存过期时间（秒）
CACHE_TTL = {
    # 实时数据 - 短期缓存
    "price:latest": 60,              # 1分钟
    "ticker": 30,                     # 30秒
    "orderbook": 10,                  # 10秒

    # K线数据 - 中期缓存
    "klines:1m": 60,                  # 1分钟
    "klines:5m": 300,                 # 5分钟
    "klines:1h": 3600,                # 1小时
    "klines:1d": 86400,               # 1天

    # 技术指标 - 中期缓存
    "indicator": 300,                 # 5分钟

    # 查询结果 - 中期缓存
    "query": 600,                     # 10分钟

    # 配置数据 - 长期缓存
    "config": 3600,                   # 1小时
    "symbols": 86400,                 # 1天

    # 会话数据
    "session": 86400,                 # 1天

    # 分布式锁
    "lock": 30,                       # 30秒
}


# 数据库连接池配置
DB_POOL_CONFIG = {
    "pool_size": 20,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}


# API限流配置
RATE_LIMIT_CONFIG = {
    "anonymous": "100/hour",
    "authenticated": "1000/hour",
    "admin": "unlimited",
}
