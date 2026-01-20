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
from .category_health import router as category_health_router
from .inventory_risk import router as inventory_risk_router
from .category_matrix import router as category_matrix_router
from .store_comparison import router as store_comparison_router
from .data_monitor import router as data_monitor_router
from .observability import router as observability_router

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
router.include_router(category_health_router, prefix="/category", tags=["品类健康度"])
router.include_router(inventory_risk_router, prefix="/inventory-risk", tags=["库存风险分析"])
router.include_router(category_matrix_router, prefix="/category-matrix", tags=["品类效益矩阵"])
router.include_router(store_comparison_router, prefix="/stores", tags=["全量门店对比"])
router.include_router(data_monitor_router, prefix="/data-monitor", tags=["数据量监控"])
router.include_router(observability_router, prefix="/observability", tags=["可观测性"])

