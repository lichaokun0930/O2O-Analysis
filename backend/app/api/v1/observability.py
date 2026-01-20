# -*- coding: utf-8 -*-
"""
可观测性 API

提供:
- 日志聚合查询
- 健康监控
- 错误追踪
- 性能指标
"""

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, date
from typing import Optional

router = APIRouter()


@router.get("/health/full")
async def full_health_check():
    """
    完整健康检查
    
    检查所有服务依赖:
    - 数据库 (PostgreSQL)
    - 缓存 (Redis)
    - OLAP引擎 (DuckDB)
    - 系统资源 (CPU/内存/磁盘)
    """
    from ...services.health_service import health_service
    return health_service.get_full_health_check()


@router.get("/health/database")
async def database_health():
    """数据库健康检查"""
    from ...services.health_service import health_service
    result = health_service.check_database()
    return {
        "status": result.status,
        "message": result.message,
        "latency_ms": result.latency_ms
    }


@router.get("/health/redis")
async def redis_health():
    """Redis健康检查"""
    from ...services.health_service import health_service
    result = health_service.check_redis()
    return {
        "status": result.status,
        "message": result.message,
        "latency_ms": result.latency_ms,
        "details": result.details
    }


@router.get("/health/system")
async def system_health():
    """系统资源检查"""
    from ...services.health_service import health_service
    result = health_service.check_system()
    return {
        "status": result.status,
        "message": result.message,
        "details": result.details
    }


@router.get("/metrics")
async def get_metrics():
    """
    获取性能指标
    
    返回:
    - 当前指标 (CPU/内存/QPS/错误率/延迟)
    - 1小时平均值
    - 告警阈值
    """
    from ...services.health_service import health_service
    return health_service.get_metrics_summary()


@router.get("/alerts")
async def get_alerts():
    """
    获取当前告警
    
    返回超过阈值的告警列表
    """
    from ...services.health_service import health_service
    alerts = health_service.get_alerts()
    return {
        "count": len(alerts),
        "alerts": alerts,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/logs")
async def get_logs(
    level: str = Query("ALL", description="日志级别: ALL/INFO/WARNING/ERROR"),
    limit: int = Query(100, ge=1, le=500, description="返回条数")
):
    """
    获取最近日志
    
    支持按级别筛选
    """
    from ...services.logging_service import logging_service
    logs = logging_service.get_recent_logs(level=level, limit=limit)
    return {
        "count": len(logs),
        "logs": logs,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/logs/errors")
async def get_error_logs(days: int = Query(7, ge=1, le=30, description="统计天数")):
    """
    获取错误日志统计
    
    返回按日期的错误数量
    """
    from ...services.logging_service import logging_service
    return logging_service.get_error_summary(days=days)


@router.get("/logs/slow-requests")
async def get_slow_requests(limit: int = Query(50, ge=1, le=200)):
    """
    获取慢请求列表
    
    返回响应时间超过500ms的请求
    """
    from ...services.logging_service import logging_service
    requests = logging_service.get_slow_requests(limit=limit)
    return {
        "count": len(requests),
        "threshold_ms": 500,
        "requests": requests
    }


@router.get("/errors")
async def get_errors(limit: int = Query(50, ge=1, le=200)):
    """
    获取最近错误列表
    
    按最后出现时间排序
    """
    from ...services.error_tracking_service import error_tracking_service
    errors = error_tracking_service.get_recent_errors(limit=limit)
    return {
        "count": len(errors),
        "errors": errors,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/errors/summary")
async def get_error_summary(hours: int = Query(24, ge=1, le=168, description="统计小时数")):
    """
    获取错误统计摘要
    
    返回:
    - 总错误数
    - 按类型统计
    - 按小时趋势
    """
    from ...services.error_tracking_service import error_tracking_service
    return error_tracking_service.get_error_summary(hours=hours)


@router.get("/errors/top")
async def get_top_errors(limit: int = Query(10, ge=1, le=50)):
    """
    获取出现次数最多的错误
    """
    from ...services.error_tracking_service import error_tracking_service
    errors = error_tracking_service.get_top_errors(limit=limit)
    return {
        "count": len(errors),
        "errors": errors
    }


@router.get("/errors/{error_id}")
async def get_error_detail(error_id: str):
    """
    获取错误详情
    
    包含完整堆栈和上下文
    """
    from ...services.error_tracking_service import error_tracking_service
    error = error_tracking_service.get_error(error_id)
    if not error:
        raise HTTPException(status_code=404, detail="错误不存在")
    return error


@router.delete("/errors/cleanup")
async def cleanup_old_errors(days: int = Query(7, ge=1, le=30)):
    """
    清理旧错误记录
    """
    from ...services.error_tracking_service import error_tracking_service
    deleted = error_tracking_service.clear_old_errors(days=days)
    return {
        "deleted": deleted,
        "message": f"已清理 {deleted} 条超过 {days} 天的错误记录"
    }


@router.get("/dashboard")
async def get_observability_dashboard():
    """
    可观测性仪表板数据
    
    一次性获取所有监控数据
    """
    from ...services.health_service import health_service
    from ...services.logging_service import logging_service
    from ...services.error_tracking_service import error_tracking_service
    
    return {
        "timestamp": datetime.now().isoformat(),
        "health": health_service.get_full_health_check(),
        "metrics": health_service.get_metrics_summary(),
        "alerts": health_service.get_alerts(),
        "error_summary": error_tracking_service.get_error_summary(hours=24),
        "recent_errors": error_tracking_service.get_recent_errors(limit=10),
        "slow_requests": logging_service.get_slow_requests(limit=10)
    }


# ==================== 后端优化监控 API ====================

@router.get("/rate-limit/stats")
async def get_rate_limit_stats():
    """
    获取限流统计
    
    返回:
    - 总请求数
    - 被拦截请求数
    - 拦截率
    """
    from ...services.rate_limiter_service import rate_limiter_service
    return {
        "timestamp": datetime.now().isoformat(),
        **rate_limiter_service.get_stats()
    }


@router.post("/rate-limit/reset")
async def reset_rate_limit_stats():
    """重置限流统计"""
    from ...services.rate_limiter_service import rate_limiter_service
    rate_limiter_service.reset_stats()
    return {"message": "限流统计已重置"}


@router.get("/cache/warmup/status")
async def get_cache_warmup_status():
    """
    获取缓存预热状态
    
    返回:
    - 预热任务列表
    - 预热统计
    """
    from ...services.cache_warmup_service import cache_warmup_service
    return {
        "timestamp": datetime.now().isoformat(),
        **cache_warmup_service.get_status()
    }


@router.post("/cache/warmup/trigger")
async def trigger_cache_warmup(force: bool = Query(False, description="是否强制预热")):
    """
    手动触发缓存预热
    """
    from ...services.cache_warmup_service import cache_warmup_service
    result = await cache_warmup_service.warmup_all(force=force)
    return result


@router.get("/cache/protection/stats")
async def get_cache_protection_stats():
    """
    获取缓存保护统计
    
    返回:
    - 缓存命中率
    - 穿透拦截数
    - 空值缓存命中数
    """
    from ...services.cache_protection_service import cache_protection_service
    return {
        "timestamp": datetime.now().isoformat(),
        **cache_protection_service.get_stats()
    }


@router.get("/slow-queries")
async def get_slow_queries(
    limit: int = Query(20, ge=1, le=100),
    min_duration_ms: Optional[float] = Query(None, description="最小耗时(ms)")
):
    """
    获取慢查询列表
    """
    from ...services.slow_query_service import slow_query_service
    queries = slow_query_service.get_slow_queries(
        limit=limit,
        min_duration_ms=min_duration_ms
    )
    return {
        "timestamp": datetime.now().isoformat(),
        "count": len(queries),
        "queries": queries
    }


@router.get("/slow-queries/stats")
async def get_slow_query_stats(
    order_by: str = Query("avg_duration_ms", description="排序字段"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    获取查询统计
    
    按平均耗时、总耗时、调用次数等排序
    """
    from ...services.slow_query_service import slow_query_service
    stats = slow_query_service.get_query_stats(order_by=order_by, limit=limit)
    return {
        "timestamp": datetime.now().isoformat(),
        "count": len(stats),
        "stats": stats
    }


@router.get("/slow-queries/summary")
async def get_slow_query_summary():
    """
    获取慢查询汇总
    """
    from ...services.slow_query_service import slow_query_service
    return {
        "timestamp": datetime.now().isoformat(),
        **slow_query_service.get_summary()
    }


@router.delete("/slow-queries/clear")
async def clear_slow_query_stats():
    """清空慢查询统计"""
    from ...services.slow_query_service import slow_query_service
    slow_query_service.clear_stats()
    return {"message": "慢查询统计已清空"}


@router.get("/database/pool")
async def get_database_pool_status():
    """
    获取数据库连接池状态
    """
    from database.connection import get_pool_status
    return {
        "timestamp": datetime.now().isoformat(),
        **get_pool_status()
    }


@router.get("/backend/status")
async def get_backend_status():
    """
    获取后端优化状态汇总
    
    一次性获取所有后端优化相关数据
    """
    from ...services.rate_limiter_service import rate_limiter_service
    from ...services.cache_warmup_service import cache_warmup_service
    from ...services.cache_protection_service import cache_protection_service
    from ...services.slow_query_service import slow_query_service
    from database.connection import get_pool_status
    
    return {
        "timestamp": datetime.now().isoformat(),
        "rate_limiter": rate_limiter_service.get_stats(),
        "cache_warmup": cache_warmup_service.get_status(),
        "cache_protection": cache_protection_service.get_stats(),
        "slow_queries": slow_query_service.get_summary(),
        "database_pool": get_pool_status()
    }



# ==================== 智能查询路由 API ====================

@router.get("/query-router/status")
async def get_query_router_status():
    """
    获取智能查询路由状态
    
    返回:
    - 当前引擎
    - 数据量级别
    - 切换阈值
    - 引擎可用性
    """
    from ...services.query_router_service import query_router_service
    return {
        "timestamp": datetime.now().isoformat(),
        **query_router_service.get_status()
    }


@router.post("/query-router/refresh")
async def refresh_query_router():
    """
    刷新智能路由状态（重新检测数据量）
    """
    from ...services.query_router_service import query_router_service
    report = query_router_service.initialize()
    return {
        "success": True,
        "message": "智能路由状态已刷新",
        **report
    }


@router.post("/query-router/force-engine")
async def force_query_engine(engine: str = Query(..., description="引擎类型: postgresql 或 duckdb")):
    """
    强制切换查询引擎（仅用于测试）
    
    Args:
        engine: "postgresql" 或 "duckdb"
    """
    from ...services.query_router_service import query_router_service
    result = query_router_service.force_engine(engine)
    return result


@router.get("/query-router/test")
async def test_smart_routing(
    store_name: Optional[str] = Query(None, description="门店名称"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
):
    """
    测试智能路由查询
    
    同时使用两个引擎查询，对比结果和性能
    """
    from ...services.query_router_service import query_router_service
    from ...services.duckdb_service import duckdb_service
    from ...services.aggregation_service import aggregation_service
    import time
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "params": {
            "store_name": store_name,
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
        },
        "smart_routing": {},
        "postgresql": {},
        "duckdb": {},
        "comparison": {}
    }
    
    # 1. 智能路由查询
    try:
        router_result = query_router_service.query_overview(store_name, start_date, end_date)
        results["smart_routing"] = {
            "success": True,
            "engine": router_result.engine.value,
            "source": router_result.source,
            "query_time_ms": router_result.query_time_ms,
            "data": router_result.data
        }
    except Exception as e:
        results["smart_routing"] = {"success": False, "error": str(e)}
    
    # 2. PostgreSQL 直接查询
    try:
        start_time = time.time()
        pg_data = aggregation_service.get_store_overview(store_name, start_date, end_date)
        pg_time = (time.time() - start_time) * 1000
        results["postgresql"] = {
            "success": True,
            "query_time_ms": round(pg_time, 2),
            "data": pg_data
        }
    except Exception as e:
        results["postgresql"] = {"success": False, "error": str(e)}
    
    # 3. DuckDB 直接查询
    try:
        start_time = time.time()
        dk_data = duckdb_service.query_kpi(store_name, start_date, end_date)
        dk_time = (time.time() - start_time) * 1000
        results["duckdb"] = {
            "success": True,
            "query_time_ms": round(dk_time, 2),
            "data": dk_data
        }
    except Exception as e:
        results["duckdb"] = {"success": False, "error": str(e)}
    
    # 4. 性能对比
    if results["postgresql"].get("success") and results["duckdb"].get("success"):
        pg_time = results["postgresql"]["query_time_ms"]
        dk_time = results["duckdb"]["query_time_ms"]
        
        results["comparison"] = {
            "postgresql_ms": pg_time,
            "duckdb_ms": dk_time,
            "faster_engine": "duckdb" if dk_time < pg_time else "postgresql",
            "speedup": round(pg_time / dk_time, 2) if dk_time > 0 else 0,
            "recommendation": "DuckDB更快" if dk_time < pg_time else "PostgreSQL更快"
        }
    
    return results
