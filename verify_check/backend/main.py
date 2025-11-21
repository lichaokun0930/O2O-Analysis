"""
FastAPI 后端主程序
提供RESTful API接口
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, timedelta
import os

from database.connection import get_db
from database.models import Order, Product, SceneTag, AnalysisCache
from backend.api import products, orders, analysis, scenes

# 创建FastAPI应用
app = FastAPI(
    title="智能门店经营看板 API",
    description="O2O门店数据分析后端API",
    version="1.0.0",
    docs_url="/api/docs",  # Swagger文档
    redoc_url="/api/redoc",  # ReDoc文档
)

# 配置CORS（跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(products.router, prefix="/api/products", tags=["商品管理"])
app.include_router(orders.router, prefix="/api/orders", tags=["订单管理"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["数据分析"])
app.include_router(scenes.router, prefix="/api/scenes", tags=["场景分析"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "智能门店经营看板 API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "running"
    }


@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    """健康检查"""
    try:
        # 检查数据库连接
        db.execute(text("SELECT 1"))
        
        # 统计数据量
        product_count = db.query(Product).count()
        order_count = db.query(Order).count()
        
        return {
            "status": "healthy",
            "database": "connected",
            "stats": {
                "products": product_count,
                "orders": order_count,
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """获取数据库统计信息"""
    try:
        stats = {
            "products": {
                "total": db.query(Product).count(),
                "active": db.query(Product).filter(Product.is_active == True).count(),
            },
            "orders": {
                "total": db.query(Order).count(),
                "today": db.query(Order).filter(
                    Order.date >= datetime.now().date()
                ).count(),
                "this_month": db.query(Order).filter(
                    Order.date >= datetime.now().replace(day=1)
                ).count(),
            },
            "scenes": {
                "total": db.query(SceneTag).count(),
            },
            "cache": {
                "total": db.query(AnalysisCache).count(),
                "valid": db.query(AnalysisCache).filter(
                    AnalysisCache.expire_at > datetime.now()
                ).count(),
            }
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量读取配置
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║       🚀 智能门店经营看板 - FastAPI 后端服务器            ║
╠══════════════════════════════════════════════════════════╣
║  📍 API地址: http://{host}:{port}                      ║
║  📖 API文档: http://{host}:{port}/api/docs            ║
║  🔍 ReDoc: http://{host}:{port}/api/redoc              ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True,  # 开发模式自动重载
        log_level="info"
    )
