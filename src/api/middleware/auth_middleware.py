"""
认证中间件

验证Bearer Token，保护需要认证的API端点。
参照 LoggingMiddleware / RateLimitMiddleware 模式实现。
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from typing import Callable


# 无需认证的路径白名单
AUTH_WHITELIST = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
}

# 无需认证的路径前缀
AUTH_WHITELIST_PREFIXES = (
    "/metrics",
)


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # 白名单路径直接放行
        if path in AUTH_WHITELIST or path.startswith(AUTH_WHITELIST_PREFIXES):
            return await call_next(request)

        # 提取 Bearer Token
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "缺少认证Token"},
            )

        token = auth_header[7:]

        # 延迟导入避免循环依赖
        from src.api.routes.auth import verify_token

        user_info = verify_token(token)
        if not user_info:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token无效或已过期"},
            )

        # 将用户信息注入 request.state
        request.state.user = user_info
        return await call_next(request)
