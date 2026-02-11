"""
限流中间件
防止API滥用
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from typing import Callable, Dict
from collections import defaultdict
import asyncio


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_task = None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端标识（IP地址）
        client_id = self._get_client_id(request)

        # 检查限流
        if not self._check_rate_limit(client_id):
            return JSONResponse(
                status_code=429,
                content={
                    'error': 'Too Many Requests',
                    'message': f'Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute.'
                },
                headers={
                    'Retry-After': '60'
                }
            )

        # 记录请求
        self._record_request(client_id)

        # 处理请求
        response = await call_next(request)

        # 添加限流信息到响应头
        remaining = self._get_remaining_requests(client_id)
        response.headers['X-RateLimit-Limit'] = str(self.requests_per_minute)
        response.headers['X-RateLimit-Remaining'] = str(remaining)

        return response

    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用X-Forwarded-For头
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        # 使用客户端IP
        if request.client:
            return request.client.host

        return 'unknown'

    def _check_rate_limit(self, client_id: str) -> bool:
        """检查是否超过限流"""
        now = time.time()
        minute_ago = now - 60

        # 清理过期请求
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]

        # 检查请求数
        return len(self.requests[client_id]) < self.requests_per_minute

    def _record_request(self, client_id: str):
        """记录请求"""
        self.requests[client_id].append(time.time())

    def _get_remaining_requests(self, client_id: str) -> int:
        """获取剩余请求数"""
        return max(0, self.requests_per_minute - len(self.requests[client_id]))

    async def cleanup_old_records(self):
        """定期清理旧记录"""
        while True:
            await asyncio.sleep(300)  # 每5分钟清理一次
            now = time.time()
            minute_ago = now - 60

            for client_id in list(self.requests.keys()):
                self.requests[client_id] = [
                    req_time for req_time in self.requests[client_id]
                    if req_time > minute_ago
                ]

                # 删除空记录
                if not self.requests[client_id]:
                    del self.requests[client_id]
