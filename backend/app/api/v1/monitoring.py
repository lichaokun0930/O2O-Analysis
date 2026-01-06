# -*- coding: utf-8 -*-
"""
系统监控 API

提供:
- 健康检查
- 系统指标
- 缓存状态
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import psutil
import os

import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dependencies import get_cache, get_order_data
from config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    健康检查
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION
    }


@router.get("/metrics")
async def get_system_metrics():
    """
    获取系统指标
    """
    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # 内存
    memory = psutil.virtual_memory()
    
    # 磁盘
    disk = psutil.disk_usage('/')
    
    # 数据状态
    df = get_order_data()
    data_rows = len(df) if not df.empty else 0
    
    return {
        "success": True,
        "data": {
            "cpu": {
                "percent": cpu_percent
            },
            "memory": {
                "total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
                "used_gb": round(memory.used / 1024 / 1024 / 1024, 2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                "percent": disk.percent
            },
            "data": {
                "order_rows": data_rows
            },
            "timestamp": datetime.now().isoformat()
        }
    }


@router.get("/cache")
async def get_cache_status():
    """
    获取缓存状态
    """
    cache = get_cache()
    
    if cache is None or not cache.enabled:
        return {
            "success": True,
            "data": {
                "enabled": False,
                "message": "缓存未启用"
            }
        }
    
    stats = cache.get_stats()
    
    return {
        "success": True,
        "data": {
            "enabled": True,
            **stats
        }
    }


@router.get("/config")
async def get_config_info():
    """
    获取配置信息（非敏感）
    """
    return {
        "success": True,
        "data": {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
            "api_prefix": settings.API_PREFIX,
            "default_page_size": settings.DEFAULT_PAGE_SIZE,
            "max_page_size": settings.MAX_PAGE_SIZE,
            "cache_ttl": {
                "short": settings.CACHE_TTL_SHORT,
                "medium": settings.CACHE_TTL_MEDIUM,
                "long": settings.CACHE_TTL_LONG
            }
        }
    }


@router.get("/ready")
async def readiness_check():
    """
    就绪检查（用于K8s）
    """
    # 检查数据是否可用
    df = get_order_data()
    data_ready = not df.empty
    
    # 检查缓存
    cache = get_cache()
    cache_ready = cache is not None and cache.enabled
    
    if data_ready:
        return {
            "status": "ready",
            "data": True,
            "cache": cache_ready
        }
    else:
        return {
            "status": "not_ready",
            "data": False,
            "cache": cache_ready
        }


@router.get("/live")
async def liveness_check():
    """
    存活检查（用于K8s）
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }

