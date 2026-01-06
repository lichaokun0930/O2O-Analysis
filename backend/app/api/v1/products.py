# -*- coding: utf-8 -*-
"""
商品分析 API

提供:
- 商品排行榜
- 分类分析
- 库存分析
- 热销商品
- 高利润商品
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dependencies import (
    get_product_service,
    get_order_data,
    common_store_param,
)
from services import ProductService
from schemas.product import (
    ProductRankingResponse,
    ProductCategoryResponse,
    HotProductsResponse,
    HighProfitProductsResponse,
    InventoryResponse,
)

router = APIRouter()


@router.get("/ranking", response_model=ProductRankingResponse)
async def get_product_ranking(
    sort_by: str = Query("sales", description="排序依据(sales/profit/quantity)"),
    top_n: int = Query(20, ge=1, le=100, description="Top N"),
    store_name: Optional[str] = Depends(common_store_param),
    service: ProductService = Depends(get_product_service)
):
    """
    获取商品排行榜
    
    可按销售额、利润、销量排序
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_ranking(
        df,
        sort_by=sort_by,
        top_n=top_n,
        store_name=store_name
    )
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return ProductRankingResponse(
        data=result["data"],
        summary=result["summary"]
    )


@router.get("/hot", response_model=HotProductsResponse)
async def get_hot_products(
    top_n: int = Query(10, ge=1, le=50, description="Top N"),
    store_name: Optional[str] = Depends(common_store_param),
    service: ProductService = Depends(get_product_service)
):
    """
    获取热销商品TOP N
    
    按销量排序
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_hot_products(df, top_n=top_n, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return HotProductsResponse(
        data=result["data"],
        summary=result["summary"]
    )


@router.get("/high-profit", response_model=HighProfitProductsResponse)
async def get_high_profit_products(
    top_n: int = Query(20, ge=1, le=100, description="Top N"),
    store_name: Optional[str] = Depends(common_store_param),
    service: ProductService = Depends(get_product_service)
):
    """
    获取高利润商品TOP N
    
    按利润额排序
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_high_profit_products(df, top_n=top_n, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return HighProfitProductsResponse(
        data=result["data"],
        summary=result["summary"]
    )


@router.get("/category-analysis", response_model=ProductCategoryResponse)
async def get_category_analysis(
    store_name: Optional[str] = Depends(common_store_param),
    service: ProductService = Depends(get_product_service)
):
    """
    获取分类分析数据
    
    按一级分类统计
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_category_analysis(df, store_name=store_name)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return ProductCategoryResponse(data=result["data"])


@router.get("/inventory", response_model=InventoryResponse)
async def get_inventory_analysis(
    store_name: Optional[str] = Depends(common_store_param),
    service: ProductService = Depends(get_product_service)
):
    """
    获取库存分析数据
    
    返回低库存商品列表
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    result = service.get_inventory_analysis(df, store_name=store_name)
    
    if result.get("error"):
        return InventoryResponse(
            data=[],
            summary={
                "total_products": 0,
                "status_counts": {},
                "low_stock_count": 0
            },
            message=result["error"]
        )
    
    return InventoryResponse(
        data=result["data"],
        summary=result["summary"]
    )


@router.get("/traffic-drop")
async def get_traffic_drop_products(
    drop_threshold: float = Query(0.5, ge=0, le=1, description="下滑阈值"),
    min_sales: int = Query(3, ge=1, description="最小前日销量"),
    top_n: int = Query(20, ge=1, le=100, description="Top N"),
    store_name: Optional[str] = Depends(common_store_param),
    service: ProductService = Depends(get_product_service)
):
    """
    获取流量下滑商品
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
    
    return {
        "success": True,
        "data": result["data"],
        "summary": result["summary"]
    }


@router.get("/daily-metrics")
async def get_product_daily_metrics(
    date: Optional[str] = Query(None, description="日期(YYYY-MM-DD)，默认昨日"),
    store_name: Optional[str] = Depends(common_store_param),
    service: ProductService = Depends(get_product_service)
):
    """
    获取指定日期的商品级指标
    """
    import pandas as pd
    
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    # 解析日期
    if date:
        target_date = pd.Timestamp(date)
    else:
        target_date = service.get_base_date(df)
    
    if target_date is None:
        raise HTTPException(status_code=400, detail="无法获取日期信息")
    
    metrics = service.get_product_daily_metrics(df, target_date)
    
    if metrics.empty:
        return {
            "success": True,
            "data": [],
            "date": str(target_date.date())
        }
    
    return {
        "success": True,
        "data": service.clean_for_json(metrics.to_dict('records')),
        "date": str(target_date.date())
    }


@router.get("/list")
async def get_product_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=500, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    store_name: Optional[str] = Depends(common_store_param),
    service: ProductService = Depends(get_product_service)
):
    """
    获取商品列表（支持分页和筛选）
    """
    df = get_order_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="暂无订单数据")
    
    data = df.copy()
    
    # 门店筛选
    if store_name and '门店名称' in data.columns:
        data = data[data['门店名称'] == store_name]
    
    # 分类筛选
    category_col = None
    for col in ['一级分类名', '一级分类', 'category']:
        if col in data.columns:
            category_col = col
            break
    
    if category and category_col:
        data = data[data[category_col] == category]
    
    # 搜索
    if search and '商品名称' in data.columns:
        data = data[data['商品名称'].str.contains(search, case=False, na=False)]
    
    # 按商品聚合
    group_key = service.get_product_group_key(data)
    sales_col = service.get_sales_column(data)
    
    agg_dict = {'商品名称': 'first'}
    if sales_col in data.columns:
        agg_dict['销量'] = (sales_col, 'sum')
    if '利润额' in data.columns:
        agg_dict['利润额'] = ('利润额', 'sum')
    if '实收价格' in data.columns:
        agg_dict['销售额'] = ('实收价格', 'sum')
    
    products = data.groupby(group_key).agg(**agg_dict).reset_index()
    
    # 分页
    total = len(products)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = products.iloc[start:end]
    
    return {
        "success": True,
        "data": service.clean_for_json(page_data.to_dict('records')),
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

