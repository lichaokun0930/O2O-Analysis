# -*- coding: utf-8 -*-
"""
订单数据看板 - FastAPI 主应用

提供完整的REST API接口
版本: v2.0
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import traceback

from .config import settings
from .api.v1 import router as v1_router

# 创建FastAPI应用
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

## 认证方式

使用 JWT Bearer Token 认证

默认账号：
- admin / admin123 (管理员)
- user / user123 (普通用户)
""",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    error_detail = str(exc)
    if settings.DEBUG:
        error_detail = traceback.format_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "detail": error_detail if settings.DEBUG else None,
            "timestamp": datetime.now().isoformat()
        }
    )


# 注册API路由
app.include_router(v1_router, prefix=settings.API_PREFIX)


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

