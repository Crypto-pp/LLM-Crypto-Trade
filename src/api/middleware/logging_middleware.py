"""
请求日志中间件
记录所有HTTP请求和响应
"""

import time
import logging
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
import uuid

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录请求开始
        start_time = time.time()

        # 记录请求信息
        log_data = {
            'request_id': request_id,
            'method': request.method,
            'url': str(request.url),
            'client_host': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent'),
        }

        logger.info(f"Request started: {json.dumps(log_data)}")

        # 处理请求
        try:
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录响应信息
            log_data.update({
                'status_code': response.status_code,
                'process_time': f"{process_time:.3f}s"
            })

            logger.info(f"Request completed: {json.dumps(log_data)}")

            # 添加响应头
            response.headers['X-Request-ID'] = request_id
            response.headers['X-Process-Time'] = f"{process_time:.3f}"

            return response

        except Exception as e:
            process_time = time.time() - start_time

            log_data.update({
                'status_code': 500,
                'process_time': f"{process_time:.3f}s",
                'error': str(e)
            })

            logger.error(f"Request failed: {json.dumps(log_data)}")
            raise
