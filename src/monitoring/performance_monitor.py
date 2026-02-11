"""
性能监控模块
追踪应用性能、慢查询、内存泄漏等
"""

import time
import logging
import tracemalloc
from typing import Dict, List, Any, Optional
from collections import deque
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, slow_query_threshold: float = 1.0):
        self.slow_query_threshold = slow_query_threshold
        self.slow_queries: deque = deque(maxlen=100)
        self.request_times: deque = deque(maxlen=1000)
        self.memory_snapshots: List[Any] = []
        self.tracemalloc_enabled = False

    def start_memory_tracking(self):
        """开始内存追踪"""
        if not self.tracemalloc_enabled:
            tracemalloc.start()
            self.tracemalloc_enabled = True
            logger.info("Memory tracking started")

    def stop_memory_tracking(self):
        """停止内存追踪"""
        if self.tracemalloc_enabled:
            tracemalloc.stop()
            self.tracemalloc_enabled = False
            logger.info("Memory tracking stopped")

    def take_memory_snapshot(self) -> Optional[Any]:
        """获取内存快照"""
        if not self.tracemalloc_enabled:
            return None

        snapshot = tracemalloc.take_snapshot()
        self.memory_snapshots.append({
            'timestamp': datetime.utcnow(),
            'snapshot': snapshot
        })

        # 只保留最近10个快照
        if len(self.memory_snapshots) > 10:
            self.memory_snapshots.pop(0)

        return snapshot

    def get_memory_top_stats(self, limit: int = 10) -> List[str]:
        """获取内存使用Top统计"""
        if not self.memory_snapshots:
            return []

        snapshot = self.memory_snapshots[-1]['snapshot']
        top_stats = snapshot.statistics('lineno')

        return [str(stat) for stat in top_stats[:limit]]

    def detect_memory_leak(self) -> Optional[Dict[str, Any]]:
        """检测内存泄漏"""
        if len(self.memory_snapshots) < 2:
            return None

        old_snapshot = self.memory_snapshots[0]['snapshot']
        new_snapshot = self.memory_snapshots[-1]['snapshot']

        top_stats = new_snapshot.compare_to(old_snapshot, 'lineno')

        # 查找增长最多的内存
        leaks = []
        for stat in top_stats[:10]:
            if stat.size_diff > 1024 * 1024:  # 超过1MB增长
                leaks.append({
                    'file': stat.traceback.format()[0] if stat.traceback else 'unknown',
                    'size_diff': stat.size_diff,
                    'count_diff': stat.count_diff
                })

        if leaks:
            return {
                'detected': True,
                'leaks': leaks,
                'timestamp': datetime.utcnow().isoformat()
            }

        return {'detected': False}

    def record_slow_query(self, query: str, duration: float, params: Optional[Dict] = None):
        """记录慢查询"""
        if duration > self.slow_query_threshold:
            self.slow_queries.append({
                'query': query,
                'duration': duration,
                'params': params,
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.warning(f"Slow query detected: {duration:.2f}s - {query[:100]}")

    def record_request_time(self, endpoint: str, duration: float):
        """记录请求时间"""
        self.request_times.append({
            'endpoint': endpoint,
            'duration': duration,
            'timestamp': datetime.utcnow()
        })

    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """获取慢查询列表"""
        return list(self.slow_queries)[-limit:]

    def get_request_stats(self, minutes: int = 5) -> Dict[str, Any]:
        """获取请求统计"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        recent_requests = [
            req for req in self.request_times
            if req['timestamp'] > cutoff_time
        ]

        if not recent_requests:
            return {
                'count': 0,
                'avg_duration': 0,
                'max_duration': 0,
                'min_duration': 0
            }

        durations = [req['duration'] for req in recent_requests]

        return {
            'count': len(recent_requests),
            'avg_duration': sum(durations) / len(durations),
            'max_duration': max(durations),
            'min_duration': min(durations),
            'p95_duration': self._calculate_percentile(durations, 0.95),
            'p99_duration': self._calculate_percentile(durations, 0.99)
        }

    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()
