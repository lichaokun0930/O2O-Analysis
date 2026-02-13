# -*- coding: utf-8 -*-
"""
请求限流中间件
集成到FastAPI，自动对所有请求进行限流
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from typing import Callable

from ..services.rate_limiter_service import rate_limiter_service


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    请求限流中间件
    
    功能：
    - 自动对所有API请求进行限流
    - 支持IP级别限流
    - 返回标准限流响应头
    - 白名单路径跳过限流
    """
    
    # 白名单路径（不限流）
    WHITELIST_PATHS = {
        "/",
        "/api/health",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/favicon.ico"
    }
    
    # 白名单前缀
    WHITELIST_PREFIXES = [
        "/static/",
        "/assets/"
    ]
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        path = request.url.path
        
        # 检查白名单
        if self._is_whitelisted(path):
            return await call_next(request)
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # ✅ localhost / 内网请求直接放行，不限流
        if client_ip in ("127.0.0.1", "localhost", "::1", "0.0.0.0") or client_ip.startswith("192.168.") or client_ip.startswith("10."):
            return await call_next(request)
        
        # 获取用户ID（如果已认证）
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("id")
        
        # 检查限流
        allowed, info = rate_limiter_service.check_rate_limit(
            client_ip=client_ip,
            path=path,
            user_id=user_id
        )
        
        if not allowed:
            # 返回429 Too Many Requests
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": info.get("error", "rate_limit_exceeded"),
                    "message": info.get("message", "请求过于频繁"),
                    "retry_after": info.get("retry_after", 60),
                    "timestamp": datetime.now().isoformat()
                },
                headers={
                    "Retry-After": str(info.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(info.get("limit", 60)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info.get("retry_after", 60))
                }
            )
        
        # 正常处理请求
        response = await call_next(request)
        
        # 添加限流响应头
        if info:
            response.headers["X-RateLimit-Limit"] = str(info.get("limit", 60))
            response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
            response.headers["X-RateLimit-Reset"] = str(info.get("reset", 60))
        
        return response
    
    def _is_whitelisted(self, path: str) -> bool:
        """检查路径是否在白名单"""
        if path in self.WHITELIST_PATHS:
            return True
        
        for prefix in self.WHITELIST_PREFIXES:
            if path.startswith(prefix):
                return True
        
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        # 优先从代理头获取
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # 取第一个IP（最原始的客户端IP）
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 直接连接的IP
        if request.client:
            return request.client.host
        
        return "unknown"
