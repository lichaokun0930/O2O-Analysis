# -*- coding: utf-8 -*-
"""
API v2 路由聚合

v2 版本使用 DuckDB + Parquet 架构，支持千万级数据查询
"""

from fastapi import APIRouter

from .orders import router as orders_router

router = APIRouter()

# 注册v2路由
router.include_router(orders_router, prefix="/orders", tags=["订单分析 v2 (DuckDB)"])
