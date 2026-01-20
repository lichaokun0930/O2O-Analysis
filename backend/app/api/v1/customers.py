# -*- coding: utf-8 -*-
"""
客户分析 API

提供:
- 客户流失识别
- 流失原因分析
- 召回建议
- 客单价异常分析
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dependencies import (
    get_customer_service,
    get_order_data,
    common_store_param,
)
from services import CustomerService

router = APIRouter()


@router.get("/churn")
async def get_churn_customers(
    lookback_days: int = Query(30, ge=7, le=90, description="回溯天数"),
    min_orders: int = Query(2, ge=1, description="最小订单数"),
    no_order_days: int = Query(7, ge=1, description="未下单天数阈值"),
    store_name: Optional[str] = Depends(common_store_param),
    service: CustomerService = Depends(get_customer_service)
):
    """
    识别流失客户
    
    定义: 过去N天内下单>=min_orders次，但no_order_days天未下单
    """
    df = get_order_data(store_name)  # ✅ 传入门店参数以利用缓存
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.identify_churn_customers(
        df,
        lookback_days=lookback_days,
        min_orders=min_orders,
        no_order_days=no_order_days
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"],
        "summary": result["summary"]
    }


@router.get("/churn/reasons")
async def get_churn_reasons(
    store_name: Optional[str] = Depends(common_store_param),
    service: CustomerService = Depends(get_customer_service)
):
    """
    分析流失原因
    
    可能原因：缺货、涨价、下架
    """
    import pandas as pd
    
    df = get_order_data(store_name)  # ✅ 传入门店参数以利用缓存
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    # 先获取流失客户
    churn_result = service.identify_churn_customers(df)
    if churn_result.get("error"):
        raise HTTPException(status_code=400, detail=churn_result["error"])
    
    churn_df = pd.DataFrame(churn_result["data"])
    
    if churn_df.empty:
        return {"success": True, "data": {}, "summary": {}}
    
    result = service.analyze_churn_reasons(df, churn_df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"],
        "summary": result["summary"]
    }


@router.get("/recall-suggestions")
async def get_recall_suggestions(
    top_n: int = Query(10, ge=1, le=50, description="优先召回数量"),
    store_name: Optional[str] = Depends(common_store_param),
    service: CustomerService = Depends(get_customer_service)
):
    """
    获取召回建议
    
    基于LTV和流失天数优先级排序
    """
    import pandas as pd
    
    df = get_order_data(store_name)  # ✅ 传入门店参数以利用缓存
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    # 先获取流失客户
    churn_result = service.identify_churn_customers(df)
    if churn_result.get("error"):
        raise HTTPException(status_code=400, detail=churn_result["error"])
    
    churn_df = pd.DataFrame(churn_result["data"])
    
    if churn_df.empty:
        return {"success": True, "data": [], "summary": {}}
    
    result = service.generate_recall_suggestions(churn_df, top_n=top_n)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"],
        "summary": result["summary"]
    }


@router.get("/aov-anomaly")
async def get_aov_anomaly(
    store_name: Optional[str] = Depends(common_store_param),
    service: CustomerService = Depends(get_customer_service)
):
    """
    获取客单价异常分析
    
    检测异常高/低的订单
    """
    df = get_order_data(store_name)  # ✅ 传入门店参数以利用缓存
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.analyze_aov_anomaly(df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"],
        "summary": result["summary"]
    }

