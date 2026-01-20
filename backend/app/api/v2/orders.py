# -*- coding: utf-8 -*-
"""
订单 API v2 - 使用 DuckDB 查询引擎

专为千万级数据优化，查询性能提升100-600倍
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List
from datetime import date
import time

from app.services import duckdb_service

router = APIRouter()


@router.get("/overview")
async def get_order_overview_v2(
    store_name: Optional[str] = Query(None, description="门店名称"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    channel: Optional[str] = Query(None, description="渠道筛选")
) -> Dict[str, Any]:
    """
    获取订单概览（v2 - DuckDB 加速）
    
    查询路由:
    1. 优先从预聚合Parquet查询（最快）
    2. 其次从原始Parquet实时计算
    3. 无Parquet数据时返回空结果
    
    性能对比（千万级数据）:
    - v1 (Pandas): 30-60秒
    - v2 (DuckDB): < 100ms
    """
    start_time = time.time()
    
    try:
        data = duckdb_service.query_kpi(store_name, start_date, end_date, channel)
        elapsed = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": data,
            "source": "duckdb",
            "query_time_ms": round(elapsed, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend")
async def get_order_trend_v2(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    store_name: Optional[str] = Query(None, description="门店名称"),
    channel: Optional[str] = Query(None, description="渠道筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    granularity: str = Query("day", description="粒度: day/week/month")
) -> Dict[str, Any]:
    """
    获取订单趋势（v2 - DuckDB 加速）
    
    支持日/周/月粒度聚合
    """
    start_time = time.time()
    
    try:
        data = duckdb_service.query_trend(
            days=days,
            store_name=store_name,
            channel=channel,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity
        )
        elapsed = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": data,
            "source": "duckdb",
            "query_time_ms": round(elapsed, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels")
async def get_channel_stats_v2(
    store_name: Optional[str] = Query(None, description="门店名称"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    获取渠道分析（v2 - DuckDB 加速）
    """
    start_time = time.time()
    
    try:
        data = duckdb_service.query_channels(store_name, start_date, end_date)
        elapsed = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": data,
            "source": "duckdb",
            "query_time_ms": round(elapsed, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_category_stats_v2(
    store_name: Optional[str] = Query(None, description="门店名称"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    top_n: int = Query(10, ge=1, le=50, description="返回数量")
) -> Dict[str, Any]:
    """
    获取品类分析（v2 - DuckDB 加速）
    """
    start_time = time.time()
    
    try:
        data = duckdb_service.query_categories(store_name, start_date, end_date, top_n)
        elapsed = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "data": data,
            "source": "duckdb",
            "query_time_ms": round(elapsed, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_duckdb_status() -> Dict[str, Any]:
    """
    获取 DuckDB 服务状态
    """
    return {
        "success": True,
        "data": duckdb_service.get_status()
    }
