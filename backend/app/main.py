# -*- coding: utf-8 -*-
"""
订单数据看板 - FastAPI 主应用

提供完整的REST API接口
版本: v2.0
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from datetime import datetime
import traceback

from .config import settings
from .api.v1 import router as v1_router
from .api.v2 import router as v2_router
from .middleware import ObservabilityMiddleware, RateLimitMiddleware

# 创建FastAPI应用（使用orjson提升JSON性能2-3倍）
app = FastAPI(
    title=settings.APP_NAME,
    description="""
订单数据看板 REST API

## 功能模块

- **认证** - JWT登录、Token刷新
- **订单分析** - KPI、趋势、渠道分析
- **商品分析** - 排行榜、分类、库存
- **诊断分析** - 今日必做核心功能
- **营销分析** - 活动损失、折扣分析
- **配送分析** - 异常检测、热力图
- **客户分析** - 流失预警、召回建议
- **场景分析** - 时段分布、趋势
- **报表导出** - Excel/CSV生成
- **数据管理** - 上传、验证、缓存
- **可观测性** - 日志聚合、健康监控、错误追踪

## 认证方式

使用 JWT Bearer Token 认证

默认账号：
- admin / admin123 (管理员)
- user / user123 (普通用户)
""",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse  # ✅ 使用orjson提升JSON性能
)

# ✅ 可观测性中间件（请求追踪、日志、性能监控）
app.add_middleware(ObservabilityMiddleware)

# ✅ 请求限流中间件（防止API被刷爆）
app.add_middleware(RateLimitMiddleware)

# ✅ 性能优化：GZip压缩中间件（减少传输大小60%）
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 配置CORS - 允许所有来源（生产模式需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=False,  # 使用 * 时必须设为 False
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    from .services.error_tracking_service import error_tracking_service
    from .services.logging_service import logging_service
    
    # 捕获错误
    error_id = error_tracking_service.capture_exception(
        error=exc,
        context={
            "method": request.method,
            "path": str(request.url.path),
            "query_params": str(request.query_params)
        },
        trace_id=logging_service.get_trace_id()
    )
    
    error_detail = str(exc)
    if settings.DEBUG:
        error_detail = traceback.format_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "error_id": error_id,
            "trace_id": logging_service.get_trace_id(),
            "detail": error_detail if settings.DEBUG else None,
            "timestamp": datetime.now().isoformat()
        }
    )


# 注册API路由
app.include_router(v1_router, prefix=settings.API_PREFIX)
app.include_router(v2_router, prefix="/api/v2")


# ==================== 生命周期事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    from .services.logging_service import logging_service
    
    logging_service.info("🚀 应用启动中...")
    
    # 初始化定时任务调度器
    try:
        from .tasks import init_scheduler
        init_scheduler()
        logging_service.info("✅ 定时任务调度器已启动")
    except Exception as e:
        logging_service.warning(f"⚠️ 定时任务初始化失败: {e}")
    
    # 检查DuckDB服务状态
    try:
        from .services import duckdb_service
        status = duckdb_service.get_status()
        if status['has_data']:
            logging_service.info(f"✅ DuckDB服务就绪: {status['raw_parquet_count']} 个Parquet文件")
        else:
            logging_service.warning("⚠️ DuckDB服务就绪，但无Parquet数据（请运行迁移脚本）")
    except Exception as e:
        logging_service.warning(f"⚠️ DuckDB服务检查失败: {e}")
    
    # 初始化智能查询路由
    try:
        from .services.query_router_service import query_router_service
        router_report = query_router_service.initialize()
        engine = router_report["current_engine"].upper()
        count = router_report["record_count"]
        level = router_report["data_level_desc"]
        logging_service.info(f"✅ 智能路由已启用: {engine} ({count:,}条, {level}数据)")
    except Exception as e:
        logging_service.warning(f"⚠️ 智能路由初始化失败: {e}")
    
    # 缓存预热
    try:
        from .services.cache_warmup_service import cache_warmup_service
        # 注册预热任务
        _register_warmup_tasks(cache_warmup_service)
        # 执行预热
        result = await cache_warmup_service.warmup_all()
        if result.get("successful", 0) > 0:
            logging_service.info(
                f"✅ 缓存预热完成: {result['successful']}/{result['total_tasks']} 成功"
            )
    except Exception as e:
        logging_service.warning(f"⚠️ 缓存预热失败: {e}")
    
    logging_service.info("✅ 应用启动完成")


def _register_warmup_tasks(warmup_service):
    """注册缓存预热任务"""
    from database.connection import get_db_context
    from sqlalchemy import text
    
    # 门店列表预热
    def load_stores():
        with get_db_context() as db:
            result = db.execute(text(
                "SELECT DISTINCT store_name FROM orders WHERE store_name IS NOT NULL ORDER BY store_name"
            ))
            return [row[0] for row in result.fetchall()]
    
    warmup_service.register_task(
        name="stores_list",
        loader=load_stores,
        cache_key="warmup:stores:list",
        ttl=3600,
        priority=1
    )
    
    # 渠道列表预热
    def load_channels():
        with get_db_context() as db:
            result = db.execute(text(
                "SELECT DISTINCT channel FROM orders WHERE channel IS NOT NULL ORDER BY channel"
            ))
            return [row[0] for row in result.fetchall()]
    
    warmup_service.register_task(
        name="channels_list",
        loader=load_channels,
        cache_key="warmup:channels:list",
        ttl=3600,
        priority=1
    )
    
    # 日期范围预热
    def load_date_range():
        with get_db_context() as db:
            result = db.execute(text(
                "SELECT MIN(date), MAX(date) FROM orders"
            ))
            row = result.fetchone()
            return {
                "min_date": str(row[0]) if row[0] else None,
                "max_date": str(row[1]) if row[1] else None
            }
    
    warmup_service.register_task(
        name="date_range",
        loader=load_date_range,
        cache_key="warmup:date:range",
        ttl=3600,
        priority=1
    )


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    from .services.logging_service import logging_service
    
    logging_service.info("🛑 应用关闭中...")
    
    # 关闭定时任务调度器
    try:
        from .tasks import shutdown_scheduler
        shutdown_scheduler()
        logging_service.info("✅ 定时任务调度器已关闭")
    except Exception as e:
        logging_service.warning(f"⚠️ 定时任务关闭失败: {e}")
    
    logging_service.info("✅ 应用已关闭")


# 根路径
@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


# 健康检查（兼容旧路径）
@app.get("/api/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║           🚀 {settings.APP_NAME} - FastAPI 后端服务器
╠══════════════════════════════════════════════════════════════════╣
║  📍 API地址: http://{settings.API_HOST}:{settings.API_PORT}
║  📖 Swagger: http://{settings.API_HOST}:{settings.API_PORT}/api/docs
║  📚 ReDoc:   http://{settings.API_HOST}:{settings.API_PORT}/api/redoc
║  🔑 认证:    JWT Bearer Token
╠══════════════════════════════════════════════════════════════════╣
║  默认账号: admin/admin123 | user/user123
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

