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

import time

# 内存缓存
_memory_cache = {
    "order_data": None,
    "timestamp": 0,
    "store_cache": {}  # 按门店缓存
}
# ✅ 优化：延长TTL到24小时（数据每天更新一次）
CACHE_TTL = 86400  # 24小时


def get_order_data(store_name: str = None) -> pd.DataFrame:
    """
    获取订单数据（带缓存）
    
    Args:
        store_name: 门店名称，如果指定则只加载该门店数据
    
    Returns:
        订单DataFrame
    """
    global _memory_cache
    current_time = time.time()
    
    # 1. 尝试使用内存缓存
    if store_name:
        store_cache = _memory_cache.get("store_cache", {}).get(store_name)
        if store_cache and current_time - store_cache.get("timestamp", 0) < CACHE_TTL:
            print(f"📦 使用内存缓存数据 (门店: {store_name})")
            return store_cache["data"].copy()
    else:
        if _memory_cache["order_data"] is not None:
            if current_time - _memory_cache["timestamp"] < CACHE_TTL:
                print(f"📦 使用内存缓存数据 (全部门店)")
                return _memory_cache["order_data"].copy()
    
    # 2. 从数据库加载
    print(f"🔄 从数据库加载订单数据 (门店: {store_name or '全部'})...")
    
    try:
        # 导入数据库连接
        import sys
        from pathlib import Path
        db_path = Path(__file__).resolve().parent / "database"
        if str(db_path) not in sys.path:
            sys.path.insert(0, str(db_path))
        
        from database.connection import SessionLocal
        from database.models import Order
        
        session = SessionLocal()
        try:
            query = session.query(Order)
            
            # 如果指定门店，只加载该门店数据
            if store_name:
                query = query.filter(Order.store_name == store_name)
            
            orders = query.all()
            if not orders:
                return pd.DataFrame()
            
            # 转换为DataFrame
            data = []
            for order in orders:
                data.append({
                    '订单ID': order.order_id,
                    '门店名称': order.store_name,
                    '日期': order.date,
                    '渠道': order.channel,
                    '商品名称': order.product_name,
                    '一级分类名': order.category_level1,
                    '三级分类名': order.category_level3,
                    '月售': order.quantity,
                    '实收价格': float(order.actual_price or 0),
                    '商品实售价': float(order.price or 0),
                    '商品采购成本': float(order.cost or 0),
                    '利润额': float(order.profit or 0),
                    '物流配送费': float(order.delivery_fee or 0),
                    '平台服务费': float(order.platform_service_fee or 0),
                    '平台佣金': float(order.commission or 0),
                    '预计订单收入': float(order.amount or 0),
                    '企客后返': float(order.corporate_rebate or 0),
                    '用户支付配送费': float(order.user_paid_delivery_fee or 0),
                    '配送费减免金额': float(order.delivery_discount or 0),
                    '满减金额': float(order.full_reduction or 0),
                    '商品减免金额': float(order.product_discount or 0),
                    '新客减免金额': float(order.new_customer_discount or 0),
                    '库存': order.stock,
                })
            
            df = pd.DataFrame(data)
            print(f"✅ 数据库加载完成: {len(df)} 条记录 (门店: {store_name or '全部'})")
            
            # 3. 更新内存缓存
            if store_name:
                if "store_cache" not in _memory_cache:
                    _memory_cache["store_cache"] = {}
                _memory_cache["store_cache"][store_name] = {
                    "data": df.copy(),
                    "timestamp": current_time
                }
            else:
                _memory_cache["order_data"] = df.copy()
                _memory_cache["timestamp"] = current_time
            
            return df
        finally:
            session.close()
            
    except Exception as e:
        print(f"⚠️ 数据库加载失败: {e}")
        
        # 备用方案：尝试从数据处理器加载
        if DATA_PROCESSOR_AVAILABLE:
            try:
                processor = RealDataProcessor()
                data = processor.load_all_data()
                if 'sales' in data and data['sales'] is not None:
                    df = data['sales']
                    if store_name and '门店名称' in df.columns:
                        df = df[df['门店名称'] == store_name]
                    return df
            except Exception as e2:
                print(f"⚠️ 数据处理器加载失败: {e2}")
    
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

