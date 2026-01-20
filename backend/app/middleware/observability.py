# -*- coding: utf-8 -*-
"""
可观测性中间件

功能:
- 请求追踪 (trace_id)
- 请求日志
- 性能监控
- 错误捕获
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """可观测性中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        from ..services.logging_service import logging_service
        from ..services.health_service import health_service
        from ..services.error_tracking_service import error_tracking_service
        
        # 生成并设置 trace_id
        trace_id = logging_service.generate_trace_id()
        logging_service.set_trace_id(trace_id)
        
        # 记录开始时间
        start_time = time.time()
        
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        
        # 请求路径
        path = request.url.path
        method = request.method
        
        # 跳过健康检查和静态资源的日志
        skip_logging = path in ["/api/health", "/health", "/favicon.ico"] or path.startswith("/api/docs")
        
        is_error = False
        status_code = 500
        
        try:
            # 执行请求
            response = await call_next(request)
            status_code = response.status_code
            is_error = status_code >= 400
            
            # 添加 trace_id 到响应头
            response.headers["X-Trace-ID"] = trace_id
            
            return response
            
        except Exception as e:
            # 捕获异常
            is_error = True
            error_id = error_tracking_service.capture_exception(
                error=e,
                context={
                    "method": method,
                    "path": path,
                    "client_ip": client_ip,
                    "query_params": str(request.query_params)
                },
                trace_id=trace_id
            )
            
            logging_service.log_error(e, context={
                "error_id": error_id,
                "method": method,
                "path": path
            })
            
            raise
            
        finally:
            # 计算耗时
            duration_ms = (time.time() - start_time) * 1000
            
            # 记录请求指标
            health_service.record_request(duration_ms, is_error)
            
            # 记录访问日志
            if not skip_logging:
                logging_service.log_request(
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    client_ip=client_ip
                )
