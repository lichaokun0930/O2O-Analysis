# -*- coding: utf-8 -*-
"""
诊断分析 API - 今日必做核心接口

提供:
- 诊断汇总
- 🔴 紧急处理：穿底订单、高配送费、缺货预警
- 🟡 关注观察：流量下滑、滞销预警、价格异常
- 🟢 亮点分析：热销商品、高利润商品
- 客户流失、客单价异常
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dependencies import (
    get_diagnosis_service,
    get_product_service,
    get_customer_service,
    get_order_data,
    common_store_param,
)
from services import DiagnosisService, ProductService, CustomerService
from schemas.diagnosis import (
    DiagnosisSummaryResponse,
    OverflowOrdersResponse,
    HighDeliveryResponse,
    SlowMovingResponse,
    TrafficDropResponse,
    CustomerChurnResponse,
    AOVAnomalyResponse,
)

router = APIRouter()


# ==================== 诊断汇总 ====================

@router.get("/summary", response_model=DiagnosisSummaryResponse)
async def get_diagnosis_summary(
    store_name: Optional[str] = Depends(common_store_param),
    service: DiagnosisService = Depends(get_diagnosis_service)
):
    """
    获取完整诊断汇总
    
    返回:
    - 🔴 紧急处理问题列表
    - 🟡 关注观察问题列表
    - 数据日期
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_diagnosis_summary(df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return DiagnosisSummaryResponse(
        data=result["data"],
        date=result.get("date")
    )


# ==================== 🔴 紧急处理 API ====================

@router.get("/urgent/overflow-orders", response_model=OverflowOrdersResponse)
async def get_overflow_orders(
    store_name: Optional[str] = Depends(common_store_param),
    yesterday_only: bool = Query(True, description="是否只分析昨日数据"),
    service: DiagnosisService = Depends(get_diagnosis_service)
):
    """
    获取穿底订单列表
    
    穿底订单：订单实际利润 < 0
    公式：订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_overflow_orders(
        df, 
        store_name=store_name,
        yesterday_only=yesterday_only
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return OverflowOrdersResponse(
        data=result["data"],
        summary=result["summary"]
    )


@router.get("/urgent/high-delivery", response_model=HighDeliveryResponse)
async def get_high_delivery_orders(
    threshold: float = Query(6.0, ge=0, description="配送费阈值（元）"),
    store_name: Optional[str] = Depends(common_store_param),
    yesterday_only: bool = Query(True, description="是否只分析昨日数据"),
    service: DiagnosisService = Depends(get_diagnosis_service)
):
    """
    获取高配送费订单
    
    定义：配送费 > 阈值 且 订单毛利 < 配送费
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_high_delivery_orders(
        df,
        threshold=threshold,
        store_name=store_name,
        yesterday_only=yesterday_only
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return HighDeliveryResponse(
        data=result["data"],
        summary=result["summary"]
    )


@router.get("/urgent/stockout")
async def get_stockout_products(
    stock_threshold: int = Query(5, ge=0, description="库存阈值"),
    store_name: Optional[str] = Depends(common_store_param),
    service: ProductService = Depends(get_product_service)
):
    """
    获取热销缺货商品
    
    热销品：昨日有销量
    缺货：库存 <= 阈值
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_inventory_analysis(df, store_name=store_name)
    
    if result.get("error"):
        return {"success": False, "message": result["error"], "data": []}
    
    return {
        "success": True,
        "data": result.get("data", []),
        "summary": result.get("summary", {})
    }


# ==================== 🟡 关注观察 API ====================

@router.get("/watch/traffic-drop", response_model=TrafficDropResponse)
async def get_traffic_drop_products(
    drop_threshold: float = Query(0.5, ge=0, le=1, description="下滑阈值（50%）"),
    min_sales: int = Query(3, ge=1, description="最小前日销量"),
    top_n: int = Query(20, ge=1, le=100, description="Top N"),
    store_name: Optional[str] = Depends(common_store_param),
    service: ProductService = Depends(get_product_service)
):
    """
    获取流量下滑商品
    
    定义：以前卖得好，昨天突然卖不动了
    筛选：前日销量 >= min_sales 且 昨日销量环比下跌 > drop_threshold
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_traffic_drop_products(
        df,
        top_n=top_n,
        drop_threshold=drop_threshold,
        min_sales=min_sales,
        store_name=store_name
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return TrafficDropResponse(
        data=result["data"],
        summary=result["summary"]
    )


@router.get("/watch/slow-moving", response_model=SlowMovingResponse)
async def get_slow_moving_products(
    days: int = Query(7, ge=1, le=90, description="滞销天数阈值"),
    store_name: Optional[str] = Depends(common_store_param),
    service: DiagnosisService = Depends(get_diagnosis_service)
):
    """
    获取滞销商品
    
    定义：有库存但连续N天无销量
    级别：新增滞销(3天)、持续滞销(7天)、严重滞销(15天)
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_slow_moving_products(
        df,
        days=days,
        store_name=store_name
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return SlowMovingResponse(
        data=result["data"],
        summary=result["summary"]
    )


@router.get("/watch/price-abnormal")
async def get_price_abnormal_products(
    store_name: Optional[str] = Depends(common_store_param),
    service: ProductService = Depends(get_product_service)
):
    """
    获取价格异常商品
    
    异常：售价低于成本
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    # TODO: 实现价格异常分析
    return {
        "success": True,
        "data": [],
        "summary": {"count": 0}
    }


# ==================== 🟢 亮点分析 API ====================

@router.get("/highlights/hot-products")
async def get_hot_products(
    top_n: int = Query(10, ge=1, le=50, description="Top N"),
    store_name: Optional[str] = Depends(common_store_param),
    service: ProductService = Depends(get_product_service)
):
    """
    获取热销商品TOP N
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_hot_products(df, top_n=top_n, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result.get("data", []),
        "summary": result.get("summary", {})
    }


@router.get("/highlights/high-profit")
async def get_high_profit_products(
    top_n: int = Query(20, ge=1, le=100, description="Top N"),
    store_name: Optional[str] = Depends(common_store_param),
    service: ProductService = Depends(get_product_service)
):
    """
    获取高利润商品TOP N
    
    定义：昨日给门店赚钱最多的商品（现金牛）
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_high_profit_products(df, top_n=top_n, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result.get("data", []),
        "summary": result.get("summary", {})
    }


# ==================== 客户流失 API ====================

@router.get("/customer-churn", response_model=CustomerChurnResponse)
async def get_customer_churn_warning(
    lookback_days: int = Query(30, ge=7, le=90, description="回溯天数"),
    min_orders: int = Query(2, ge=1, description="最小订单数"),
    no_order_days: int = Query(7, ge=1, description="未下单天数阈值"),
    store_name: Optional[str] = Depends(common_store_param),
    service: CustomerService = Depends(get_customer_service)
):
    """
    获取客户流失预警
    
    定义：过去N天内下单>=2次，但7天未下单的客户
    """
    df = get_order_data()
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
    
    return CustomerChurnResponse(
        data=result["data"],
        summary=result["summary"]
    )


@router.get("/customer-churn/recall-suggestions")
async def get_recall_suggestions(
    top_n: int = Query(10, ge=1, le=50, description="优先召回数量"),
    service: CustomerService = Depends(get_customer_service)
):
    """
    获取召回建议
    
    基于LTV和流失天数优先级排序
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    # 先获取流失客户
    churn_result = service.identify_churn_customers(df)
    if churn_result.get("error"):
        raise HTTPException(status_code=400, detail=churn_result["error"])
    
    # 生成召回建议
    import pandas as pd
    churn_df = pd.DataFrame(churn_result["data"])
    
    if churn_df.empty:
        return {"success": True, "data": [], "summary": {}}
    
    result = service.generate_recall_suggestions(churn_df, top_n=top_n)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result.get("data", []),
        "summary": result.get("summary", {})
    }


# ==================== 客单价异常 API ====================

@router.get("/aov-anomaly", response_model=AOVAnomalyResponse)
async def get_aov_anomaly(
    store_name: Optional[str] = Depends(common_store_param),
    service: CustomerService = Depends(get_customer_service)
):
    """
    获取客单价异常分析
    
    检测异常高/低的订单
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.analyze_aov_anomaly(df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return AOVAnomalyResponse(
        data=result["data"],
        summary=result["summary"]
    )


# ==================== 趋势分析 API ====================

@router.get("/trend/overflow-daily")
async def get_overflow_daily_trend(
    days: int = Query(7, ge=1, le=30, description="天数"),
    store_name: Optional[str] = Depends(common_store_param),
    service: DiagnosisService = Depends(get_diagnosis_service)
):
    """
    获取穿底订单每日趋势
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.calculate_daily_overflow_batch(df, days=days)
    
    return {
        "success": True,
        "data": result,
        "period_days": days
    }

