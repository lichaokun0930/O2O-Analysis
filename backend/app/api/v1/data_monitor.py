# -*- coding: utf-8 -*-
"""
数据量监控 API

提供数据量统计、阈值告警、优化建议等功能
用于监控系统是否需要升级到千万级架构
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services import data_monitor_service, duckdb_service, parquet_sync_service

router = APIRouter(prefix="/monitor", tags=["数据监控"])


@router.get("/stats")
async def get_data_stats() -> Dict[str, Any]:
    """
    获取数据量统计信息
    
    返回:
    - total_records: 总记录数
    - unique_orders: 唯一订单数
    - store_count: 门店数
    - date_range: 数据日期范围
    - recent_7days: 最近7天新增
    - daily_growth: 日均增长
    - thresholds: 阈值配置
    - predictions: 达到阈值预估时间
    - recommendation: 优化建议
    """
    try:
        stats = data_monitor_service.get_data_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alert")
async def check_alert() -> Dict[str, Any]:
    """
    检查是否需要告警
    
    返回告警信息（如果有）
    """
    alert = data_monitor_service.check_and_alert()
    return {
        "success": True,
        "has_alert": alert is not None,
        "message": alert
    }


@router.get("/services-status")
async def get_services_status() -> Dict[str, Any]:
    """
    获取千万级优化服务状态
    
    返回DuckDB、Parquet同步服务的状态
    """
    return {
        "success": True,
        "data": {
            "duckdb": duckdb_service.get_status(),
            "parquet_sync": parquet_sync_service.get_status(),
        }
    }


@router.post("/enable-duckdb")
async def enable_duckdb() -> Dict[str, Any]:
    """
    启用DuckDB服务（手动触发）
    
    注意：通常在数据量超过300万时启用
    """
    try:
        duckdb_service.enable()
        return {
            "success": True,
            "message": "DuckDB服务已启用",
            "status": duckdb_service.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disable-duckdb")
async def disable_duckdb() -> Dict[str, Any]:
    """
    禁用DuckDB服务
    """
    try:
        duckdb_service.disable()
        return {
            "success": True,
            "message": "DuckDB服务已禁用",
            "status": duckdb_service.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
