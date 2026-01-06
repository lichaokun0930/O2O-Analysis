# -*- coding: utf-8 -*-
"""
营销分析 API

提供:
- 营销损失分析
- 活动叠加分析
- 配送×活动交叉分析
- 折扣分析
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dependencies import (
    get_marketing_service,
    get_order_data,
    common_store_param,
)
from services import MarketingService

router = APIRouter()


@router.get("/loss-analysis")
async def get_marketing_loss_analysis(
    store_name: Optional[str] = Depends(common_store_param),
    yesterday_only: bool = Query(True, description="是否只分析昨日数据"),
    service: MarketingService = Depends(get_marketing_service)
):
    """
    营销导致亏损订单分析
    
    定义:
    - 基础条件: 订单实际利润 < 0
    - 营销关联: 参与了活动
    - 分类: 按活动类型统计
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.analyze_marketing_loss(
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


@router.get("/activity-overlap")
async def get_activity_overlap_analysis(
    store_name: Optional[str] = Depends(common_store_param),
    yesterday_only: bool = Query(True, description="是否只分析昨日数据"),
    service: MarketingService = Depends(get_marketing_service)
):
    """
    活动叠加分析
    
    分析同时参与多个活动的订单
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.analyze_activity_overlap(
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


@router.get("/delivery-cross")
async def get_delivery_activity_cross_analysis(
    delivery_threshold: float = Query(6.0, ge=0, description="配送费阈值"),
    store_name: Optional[str] = Depends(common_store_param),
    yesterday_only: bool = Query(True, description="是否只分析昨日数据"),
    service: MarketingService = Depends(get_marketing_service)
):
    """
    配送费×活动叠加交叉分析
    
    分析高配送费且参与活动的订单（风险最高）
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.analyze_delivery_activity_cross(
        df,
        delivery_threshold=delivery_threshold,
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


@router.get("/discount-analysis")
async def get_discount_analysis(
    store_name: Optional[str] = Depends(common_store_param),
    service: MarketingService = Depends(get_marketing_service)
):
    """
    折扣分析
    
    分析各类折扣的使用情况
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.analyze_discounts(df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"],
        "summary": result["summary"]
    }

