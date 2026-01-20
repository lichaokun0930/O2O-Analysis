# -*- coding: utf-8 -*-
"""
场景分析 API

提供:
- 场景分布
- 小时分析
- 场景×渠道交叉
- 场景趋势
- 场景商品
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dependencies import (
    get_scene_service,
    get_order_data,
    common_store_param,
)
from services import SceneService

router = APIRouter()


@router.get("/distribution")
async def get_scene_distribution(
    store_name: Optional[str] = Depends(common_store_param),
    service: SceneService = Depends(get_scene_service)
):
    """
    获取场景分布
    
    按场景（早餐/午餐/下午茶/晚餐/夜宵）统计
    """
    df = get_order_data(store_name)  # ✅ 传入门店参数以利用缓存
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_scene_distribution(df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"],
        "config": result["config"]
    }


@router.get("/hourly")
async def get_hourly_analysis(
    store_name: Optional[str] = Depends(common_store_param),
    service: SceneService = Depends(get_scene_service)
):
    """
    按小时分析
    
    返回每小时的订单数和销售额
    """
    df = get_order_data(store_name)  # ✅ 传入门店参数以利用缓存
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_hourly_analysis(df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.get("/channel-cross")
async def get_scene_channel_cross(
    store_name: Optional[str] = Depends(common_store_param),
    service: SceneService = Depends(get_scene_service)
):
    """
    场景×渠道交叉分析
    
    热力图数据
    """
    df = get_order_data(store_name)  # ✅ 传入门店参数以利用缓存
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_scene_channel_cross(df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"],
        "config": result["config"]
    }


@router.get("/trend")
async def get_scene_trend(
    days: int = Query(7, ge=1, le=30, description="天数"),
    store_name: Optional[str] = Depends(common_store_param),
    service: SceneService = Depends(get_scene_service)
):
    """
    场景趋势分析
    
    返回每个场景的日趋势
    """
    df = get_order_data(store_name)  # ✅ 传入门店参数以利用缓存
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_scene_trend(df, days=days, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"],
        "config": result["config"]
    }


@router.get("/products/{scene}")
async def get_scene_products(
    scene: str,
    top_n: int = Query(10, ge=1, le=50, description="Top N"),
    store_name: Optional[str] = Depends(common_store_param),
    service: SceneService = Depends(get_scene_service)
):
    """
    获取指定场景的热销商品
    
    场景：早餐/午餐/下午茶/晚餐/夜宵
    """
    df = get_order_data(store_name)  # ✅ 传入门店参数以利用缓存
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_scene_products(
        df, 
        scene=scene, 
        top_n=top_n, 
        store_name=store_name
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"],
        "scene": result["scene"]
    }

