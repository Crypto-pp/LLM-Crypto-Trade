"""
Prometheus指标定义和采集
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
from typing import Callable, Any
import psutil
import logging

logger = logging.getLogger(__name__)

# ==========================================
# HTTP请求指标
# ==========================================

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

REQUEST_SIZE = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

RESPONSE_SIZE = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

# ==========================================
# 业务指标
# ==========================================

SIGNAL_GENERATED = Counter(
    'trading_signals_generated_total',
    'Total trading signals generated',
    ['symbol', 'action', 'strategy', 'confidence_level']
)

SIGNAL_EXECUTED = Counter(
    'trading_signals_executed_total',
    'Total trading signals executed',
    ['symbol', 'action', 'result']
)

DATA_COLLECTION_SUCCESS = Counter(
    'data_collection_success_total',
    'Successful data collections',
    ['exchange', 'symbol', 'data_type']
)

DATA_COLLECTION_FAILURE = Counter(
    'data_collection_failure_total',
    'Failed data collections',
    ['exchange', 'symbol', 'error_type']
)

DATA_FRESHNESS = Gauge(
    'data_freshness_seconds',
    'Age of the most recent data in seconds',
    ['exchange', 'symbol']
)

STRATEGY_EXECUTION_TIME = Histogram(
    'strategy_execution_seconds',
    'Strategy execution time in seconds',
    ['strategy_name'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

STRATEGY_WIN_RATE = Gauge(
    'strategy_win_rate',
    'Strategy win rate (0-1)',
    ['strategy_name']
)

STRATEGY_PROFIT_LOSS = Gauge(
    'strategy_profit_loss_usd',
    'Strategy profit/loss in USD',
    ['strategy_name']
)

ACCOUNT_BALANCE = Gauge(
    'account_balance_usd',
    'Account balance in USD',
    ['exchange', 'currency']
)

API_RATE_LIMIT_REMAINING = Gauge(
    'api_rate_limit_remaining',
    'API rate limit remaining requests',
    ['exchange', 'endpoint']
)

# ==========================================
# 系统指标
# ==========================================

SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes'
)

SYSTEM_MEMORY_AVAILABLE = Gauge(
    'system_memory_available_bytes',
    'System available memory in bytes'
)

SYSTEM_DISK_USAGE = Gauge(
    'system_disk_usage_bytes',
    'System disk usage in bytes',
    ['path']
)

# ==========================================
# 应用指标
# ==========================================

APPLICATION_ERRORS = Counter(
    'application_errors_total',
    'Total application errors',
    ['error_type', 'module', 'severity']
)

DATABASE_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Number of active database connections',
    ['database']
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

QUEUE_SIZE = Gauge(
    'queue_size',
    'Number of messages in queue',
    ['queue_name']
)

QUEUE_PROCESSING_TIME = Histogram(
    'queue_processing_seconds',
    'Queue message processing time in seconds',
    ['queue_name'],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0)
)

# ==========================================
# 装饰器
# ==========================================

def track_request(func: Callable) -> Callable:
    """
    装饰器：自动追踪HTTP请求指标
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        ACTIVE_REQUESTS.inc()
        start_time = time.time()

        try:
            response = await func(*args, **kwargs)
            status = getattr(response, 'status_code', 200)

            # 从kwargs或args中获取request对象
            request = kwargs.get('request') or (args[0] if args else None)
            if request and hasattr(request, 'method'):
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=status
                ).inc()

            return response

        except Exception as e:
            request = kwargs.get('request') or (args[0] if args else None)
            if request and hasattr(request, 'method'):
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=500
                ).inc()
            raise

        finally:
            duration = time.time() - start_time
            request = kwargs.get('request') or (args[0] if args else None)
            if request and hasattr(request, 'method'):
                REQUEST_DURATION.labels(
                    method=request.method,
                    endpoint=request.url.path
                ).observe(duration)
            ACTIVE_REQUESTS.dec()

    return wrapper


def track_execution_time(metric: Histogram, **labels):
    """
    装饰器：追踪函数执行时间

    Args:
        metric: Prometheus Histogram指标
        **labels: 标签键值对
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                metric.labels(**labels).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                metric.labels(**labels).observe(duration)

        # 判断是否为异步函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ==========================================
# 系统指标采集器
# ==========================================

class SystemMetricsCollector:
    """系统指标采集器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def collect_cpu_metrics(self):
        """采集CPU指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_USAGE.set(cpu_percent)
        except Exception as e:
            self.logger.error(f"Failed to collect CPU metrics: {e}")

    def collect_memory_metrics(self):
        """采集内存指标"""
        try:
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.set(memory.used)
            SYSTEM_MEMORY_AVAILABLE.set(memory.available)
        except Exception as e:
            self.logger.error(f"Failed to collect memory metrics: {e}")

    def collect_disk_metrics(self):
        """采集磁盘指标"""
        try:
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    SYSTEM_DISK_USAGE.labels(path=partition.mountpoint).set(usage.used)
                except PermissionError:
                    continue
        except Exception as e:
            self.logger.error(f"Failed to collect disk metrics: {e}")

    def collect_all(self):
        """采集所有系统指标"""
        self.collect_cpu_metrics()
        self.collect_memory_metrics()
        self.collect_disk_metrics()


# 全局系统指标采集器实例
system_metrics_collector = SystemMetricsCollector()
