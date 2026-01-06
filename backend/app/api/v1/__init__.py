# -*- coding: utf-8 -*-
"""
API v1 路由聚合
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .orders import router as orders_router
from .products import router as products_router
from .diagnosis import router as diagnosis_router
from .marketing import router as marketing_router
from .delivery import router as delivery_router
from .customers import router as customers_router
from .scenes import router as scenes_router
from .reports import router as reports_router
from .data_management import router as data_router
from .monitoring import router as monitoring_router

router = APIRouter()

# 注册所有路由
router.include_router(auth_router, prefix="/auth", tags=["认证"])
router.include_router(orders_router, prefix="/orders", tags=["订单分析"])
router.include_router(products_router, prefix="/products", tags=["商品分析"])
router.include_router(diagnosis_router, prefix="/diagnosis", tags=["诊断分析-今日必做"])
router.include_router(marketing_router, prefix="/marketing", tags=["营销分析"])
router.include_router(delivery_router, prefix="/delivery", tags=["配送分析"])
router.include_router(customers_router, prefix="/customers", tags=["客户分析"])
router.include_router(scenes_router, prefix="/scenes", tags=["场景分析"])
router.include_router(reports_router, prefix="/reports", tags=["报表导出"])
router.include_router(data_router, prefix="/data", tags=["数据管理"])
router.include_router(monitoring_router, prefix="/monitor", tags=["系统监控"])

