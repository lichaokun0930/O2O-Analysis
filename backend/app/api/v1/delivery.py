# -*- coding: utf-8 -*-
"""
配送分析 API

提供:
- 配送异常分析
- 距离×时段热力图
- 按距离分析
- 按时段分析
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dependencies import (
    get_delivery_service,
    get_order_data,
    common_store_param,
)
from services import DeliveryService

router = APIRouter()


@router.get("/issues")
async def get_delivery_issues(
    threshold: float = Query(6.0, ge=0, description="配送费阈值（元）"),
    store_name: Optional[str] = Depends(common_store_param),
    yesterday_only: bool = Query(True, description="是否只分析昨日数据"),
    service: DeliveryService = Depends(get_delivery_service)
):
    """
    配送成本异常分析
    
    定义: 配送费>阈值 且 订单毛利<配送费
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.analyze_delivery_issues(
        df,
        store_name=store_name,
        yesterday_only=yesterday_only
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"],
        "summary": result["summary"]
    }


@router.get("/heatmap")
async def get_delivery_heatmap(
    store_name: Optional[str] = Depends(common_store_param),
    service: DeliveryService = Depends(get_delivery_service)
):
    """
    生成距离×时段热力图数据
    
    用于分析配送异常高发区
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_delivery_heatmap(df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"],
        "config": result["config"]
    }


@router.get("/by-distance")
async def get_analysis_by_distance(
    store_name: Optional[str] = Depends(common_store_param),
    service: DeliveryService = Depends(get_delivery_service)
):
    """
    按配送距离分析
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.analyze_by_distance(df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"],
        "config": result["config"]
    }


@router.get("/by-time-period")
async def get_analysis_by_time_period(
    store_name: Optional[str] = Depends(common_store_param),
    service: DeliveryService = Depends(get_delivery_service)
):
    """
    按时段分析配送
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.analyze_by_time_period(df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"],
        "config": result["config"]
    }

