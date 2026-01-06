# -*- coding: utf-8 -*-
"""
依赖注入模块

提供FastAPI依赖注入函数
"""

import sys
from pathlib import Path
from typing import Optional
import pandas as pd

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import Depends, Query
from datetime import date

# 导入Service
from services import (
    OrderService,
    ProductService,
    DiagnosisService,
    MarketingService,
    DeliveryService,
    CustomerService,
    SceneService,
    ReportService,
    DataManagementService,
)
from services.cache.hierarchical_cache_adapter import get_cache_manager

# 导入数据加载器（复用现有）
try:
    from 真实数据处理器 import RealDataProcessor
    DATA_PROCESSOR_AVAILABLE = True
except ImportError:
    DATA_PROCESSOR_AVAILABLE = False
    print("⚠️ 真实数据处理器未找到，使用模拟数据")


# ==================== 缓存管理器 ====================

def get_cache():
    """获取缓存管理器"""
    return get_cache_manager()


# ==================== 数据加载 ====================

_cached_data: Optional[pd.DataFrame] = None


def get_order_data() -> pd.DataFrame:
    """
    获取订单数据
    
    Returns:
        订单DataFrame
    """
    global _cached_data
    
    if _cached_data is not None:
        return _cached_data
    
    # 尝试从缓存获取
    cache = get_cache_manager()
    cached = cache.get_raw_data("order_data")
    if cached is not None:
        _cached_data = pd.DataFrame(cached)
        return _cached_data
    
    # 尝试从数据处理器加载
    if DATA_PROCESSOR_AVAILABLE:
        try:
            processor = RealDataProcessor()
            data = processor.load_all_data()
            if 'sales' in data and data['sales'] is not None:
                _cached_data = data['sales']
                # 缓存数据
                cache.set_raw_data("order_data", _cached_data.to_dict('records'))
                return _cached_data
        except Exception as e:
            print(f"⚠️ 加载数据失败: {e}")
    
    # 返回空DataFrame
    return pd.DataFrame()


# ==================== Service依赖 ====================

def get_order_service() -> OrderService:
    """获取订单服务"""
    cache = get_cache_manager()
    return OrderService(cache_manager=cache)


def get_product_service() -> ProductService:
    """获取商品服务"""
    cache = get_cache_manager()
    return ProductService(cache_manager=cache)


def get_diagnosis_service() -> DiagnosisService:
    """获取诊断服务"""
    cache = get_cache_manager()
    return DiagnosisService(cache_manager=cache)


def get_marketing_service() -> MarketingService:
    """获取营销服务"""
    cache = get_cache_manager()
    return MarketingService(cache_manager=cache)


def get_delivery_service() -> DeliveryService:
    """获取配送服务"""
    cache = get_cache_manager()
    return DeliveryService(cache_manager=cache)


def get_customer_service() -> CustomerService:
    """获取客户服务"""
    cache = get_cache_manager()
    return CustomerService(cache_manager=cache)


def get_scene_service() -> SceneService:
    """获取场景服务"""
    cache = get_cache_manager()
    return SceneService(cache_manager=cache)


def get_report_service() -> ReportService:
    """获取报表服务"""
    cache = get_cache_manager()
    return ReportService(cache_manager=cache)


def get_data_management_service() -> DataManagementService:
    """获取数据管理服务"""
    cache = get_cache_manager()
    return DataManagementService(cache_manager=cache)


# ==================== 常用查询参数 ====================

def common_pagination_params(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=500, description="每页数量")
):
    """分页参数"""
    return {"page": page, "page_size": page_size}


def common_date_range_params(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
):
    """日期范围参数"""
    return {"start_date": start_date, "end_date": end_date}


def common_store_param(
    store_name: Optional[str] = Query(None, description="门店名称")
):
    """门店参数"""
    return store_name

