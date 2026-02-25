# -*- coding: utf-8 -*-
"""
订单数据概览 API

完全对齐老版本Dash的Tab1订单数据概览功能：
- 六大核心卡片指标
- 渠道表现对比
- 客单价区间分布
- 一级分类销售趋势
- 订单趋势分析
- 环比计算
- 异常诊断

业务逻辑来源: 智能门店看板_Dash版.py 中的 Tab 1 回调
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np
import hashlib
import json
import time

import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = APP_DIR.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from database.models import Order

# 尝试导入Redis缓存
try:
    import redis
    REDIS_AVAILABLE = True
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    # 测试连接
    redis_client.ping()
    print("✅ Redis缓存已连接")
except Exception as e:
    REDIS_AVAILABLE = False
    redis_client = None
    print(f"⚠️ Redis缓存不可用: {e}")

router = APIRouter()

# ==================== 缓存配置 ====================
# ✅ 优化：延长TTL到24小时（数据每天更新一次）
CACHE_TTL = 86400  # 缓存有效期24小时
ORDER_DATA_CACHE_KEY = "order_data_cache"
ORDER_DATA_TIMESTAMP_KEY = "order_data_timestamp"
DATA_VERSION_KEY = "order_data_version"  # 数据版本号（用于智能失效）

# 内存缓存（备用）
_memory_cache = {
    "order_data": None,
    "timestamp": 0,
    "store_cache": {},  # 按门店缓存: {store_name: {data: df, timestamp: time}}
    "data_version": None  # 数据版本号
}


def get_data_version(store_name: str = None) -> str:
    """
    获取数据版本号 (Global Data Versioning)
    
    优先使用Redis全局版本号 (Generation Clock)
    当发生任何写入(上传/删除)时，版本号自增，导致所有旧缓存失效
    """
    # 1. 尝试获取全局版本号 (健壮模式)
    if REDIS_AVAILABLE:
        try:
            from redis_cache_manager import REDIS_CACHE_MANAGER
            if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
                return REDIS_CACHE_MANAGER.get_global_version()
        except Exception as e:
            print(f"⚠️ 获取全局版本失败: {e}")

    # 2. 降级模式：数据库时间戳 (仅当Redis不可用时)
    session = SessionLocal()
    try:
        from sqlalchemy import func
        query = session.query(func.max(Order.updated_at))
        if store_name:
            query = query.filter(Order.store_name == store_name)
        
        last_updated = query.scalar()
        if last_updated:
            return last_updated.strftime("%Y%m%d%H%M%S")
        return "0"
    except Exception as e:
        print(f"⚠️ 获取数据版本失败: {e}")
        return "0"
    finally:
        session.close()


def check_cache_valid(store_name: str = None) -> bool:
    """
    检查缓存是否有效（基于数据版本号）
    
    返回 True 表示缓存有效，可以使用
    返回 False 表示数据已更新，需要重新加载
    """
    if not REDIS_AVAILABLE or not redis_client:
        return False
    
    try:
        version_key = f"{DATA_VERSION_KEY}:{store_name}" if store_name else DATA_VERSION_KEY
        cached_version = redis_client.get(version_key)
        current_version = get_data_version(store_name)
        
        if cached_version and cached_version == current_version:
            return True
        return False
    except Exception as e:
        print(f"⚠️ 检查缓存版本失败: {e}")
        return False

# ==================== 收费渠道列表（与老版本一致）====================
PLATFORM_FEE_CHANNELS = [
    '饿了么',
    '京东到家',
    '美团共橙',
    '美团闪购',
    '抖音',
    '抖音直播',
    '淘鲜达',
    '京东秒送',
    '美团咖啡店',
    '饿了么咖啡店'
]


def get_order_data(store_name: str = None) -> pd.DataFrame:
    """
    从数据库加载订单数据（带智能缓存）
    
    缓存策略（优化版）:
    1. 优先检查Redis缓存 + 数据版本号
    2. 版本号匹配则直接使用缓存（即使后端重启）
    3. 版本号不匹配则重新加载（数据有更新）
    4. 缓存有效期24小时（数据每天更新一次）
    
    Args:
        store_name: 门店名称，如果指定则只加载该门店数据
    """
    global _memory_cache
    current_time = time.time()
    
    # 生成缓存key
    cache_key = f"order_data:{store_name}" if store_name else "order_data:all"
    redis_cache_key = f"{ORDER_DATA_CACHE_KEY}:{store_name}" if store_name else ORDER_DATA_CACHE_KEY
    redis_timestamp_key = f"{ORDER_DATA_TIMESTAMP_KEY}:{store_name}" if store_name else ORDER_DATA_TIMESTAMP_KEY
    version_key = f"{DATA_VERSION_KEY}:{store_name}" if store_name else DATA_VERSION_KEY
    
    # 获取当前数据版本
    current_version = get_data_version(store_name)
    
    # 1. 尝试从Redis获取缓存（智能版本检查）
    if REDIS_AVAILABLE and redis_client:
        try:
            cached_version = redis_client.get(version_key)
            cached_timestamp = redis_client.get(redis_timestamp_key)
            
            # 版本号匹配 + 未过期 = 缓存有效
            if cached_version and cached_version == current_version:
                if cached_timestamp and (current_time - float(cached_timestamp) < CACHE_TTL):
                    cached_data = redis_client.get(redis_cache_key)
                    if cached_data:
                        data = json.loads(cached_data)
                        print(f"📦 使用Redis缓存数据 (门店: {store_name or '全部'}, {len(data)} 条)")
                        return pd.DataFrame(data)
        except Exception as e:
            print(f"⚠️ Redis读取失败: {e}")
    
    # 2. 尝试使用内存缓存（同样检查版本）
    cached_version = _memory_cache.get("data_version")
    if cached_version == current_version:
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
    
    # 3. 从数据库加载
    print(f"🔄 从数据库加载订单数据 (门店: {store_name or '全部'})...")
    session = SessionLocal()
    try:
        query = session.query(Order)
        
        # 如果指定门店，只加载该门店数据
        if store_name:
            query = query.filter(Order.store_name == store_name)
        
        orders = query.all()
        if not orders:
            return pd.DataFrame()
        
        # 转换为DataFrame（字段名与数据库模型一致）
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '日期': order.date,  # 数据库字段是date
                '渠道': order.channel,
                '商品名称': order.product_name,
                '一级分类名': order.category_level1,
                '三级分类名': order.category_level3,  # 数据库只有三级分类
                '月售': order.quantity if order.quantity is not None else 1,  # 默认为1
                '实收价格': float(order.actual_price or 0),
                '商品实售价': float(order.price or 0),  # 数据库字段是price
                '商品原价': float(order.original_price or 0),  # ✅ 新增：商品原价（用于GMV计算）
                '商品采购成本': float(order.cost or 0),  # 数据库字段是cost
                '利润额': float(order.profit or 0),
                '物流配送费': float(order.delivery_fee or 0),
                '平台服务费': float(order.platform_service_fee or 0),
                '平台佣金': float(order.commission or 0),
                '预计订单收入': float(order.amount or 0),  # 使用amount作为预计订单收入
                '企客后返': float(order.corporate_rebate or 0),  # 数据库字段是corporate_rebate
                '用户支付配送费': float(order.user_paid_delivery_fee or 0),
                '配送费减免金额': float(order.delivery_discount or 0),
                '满减金额': float(order.full_reduction or 0),
                '商品减免金额': float(order.product_discount or 0),
                '新客减免金额': float(order.new_customer_discount or 0),
                # ✅ 新增：商家活动成本相关字段（与Dash版本一致）
                '商家代金券': float(order.merchant_voucher or 0),
                '商家承担部分券': float(order.merchant_share or 0),
                '满赠金额': float(order.gift_amount or 0),
                '商家其他优惠': float(order.other_merchant_discount or 0),
                '打包袋金额': float(order.packaging_fee or 0),  # ✅ 新增：打包袋金额（用于GMV计算）
                '库存': order.stock,
            })
        
        df = pd.DataFrame(data)
        print(f"✅ 数据库加载完成: {len(df)} 条记录 (门店: {store_name or '全部'})")
        
        # 4. 更新缓存（包含版本号）
        # 更新内存缓存
        _memory_cache["data_version"] = current_version
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
        
        # 更新Redis缓存（包含版本号）
        if REDIS_AVAILABLE and redis_client:
            try:
                # 将日期转换为字符串以便JSON序列化
                cache_data = data.copy()
                for item in cache_data:
                    if item.get('日期'):
                        item['日期'] = str(item['日期'])
                
                redis_client.set(redis_cache_key, json.dumps(cache_data, ensure_ascii=False))
                redis_client.set(redis_timestamp_key, str(current_time))
                redis_client.set(version_key, current_version)  # ✅ 保存版本号
                # 设置过期时间（24小时）
                redis_client.expire(redis_cache_key, CACHE_TTL)
                redis_client.expire(redis_timestamp_key, CACHE_TTL)
                redis_client.expire(version_key, CACHE_TTL)
                print(f"✅ 数据已缓存到Redis (门店: {store_name or '全部'}, 版本: {current_version})")
            except Exception as e:
                print(f"⚠️ Redis缓存写入失败: {e}")
        
        return df
    finally:
        session.close()


def invalidate_cache(store_name: str = None):
    """
    清除缓存（数据更新时调用）
    
    Args:
        store_name: 指定门店则只清除该门店缓存，否则清除全部
    """
    global _memory_cache
    
    if store_name:
        # 只清除指定门店的缓存
        if "store_cache" in _memory_cache and store_name in _memory_cache["store_cache"]:
            del _memory_cache["store_cache"][store_name]
            print(f"✅ 内存缓存已清除 (门店: {store_name})")
    else:
        # 清除全部缓存
        _memory_cache = {"order_data": None, "timestamp": 0, "store_cache": {}, "data_version": None}
        print("✅ 内存缓存已全部清除")
    
    if REDIS_AVAILABLE and redis_client:
        try:
            if store_name:
                # 只清除指定门店的缓存
                redis_client.delete(f"{ORDER_DATA_CACHE_KEY}:{store_name}")
                redis_client.delete(f"{ORDER_DATA_TIMESTAMP_KEY}:{store_name}")
                redis_client.delete(f"{DATA_VERSION_KEY}:{store_name}")
                print(f"✅ Redis缓存已清除 (门店: {store_name})")
            else:
                # 清除所有订单相关的缓存
                keys = redis_client.keys(f"{ORDER_DATA_CACHE_KEY}:*")
                if keys:
                    redis_client.delete(*keys)
                keys = redis_client.keys(f"{ORDER_DATA_TIMESTAMP_KEY}:*")
                if keys:
                    redis_client.delete(*keys)
                keys = redis_client.keys(f"{DATA_VERSION_KEY}:*")
                if keys:
                    redis_client.delete(*keys)
                redis_client.delete(ORDER_DATA_CACHE_KEY)
                redis_client.delete(ORDER_DATA_TIMESTAMP_KEY)
                redis_client.delete(DATA_VERSION_KEY)
                print("✅ Redis缓存已全部清除")
        except Exception as e:
            print(f"⚠️ Redis缓存清除失败: {e}")
            redis_client.delete(ORDER_DATA_TIMESTAMP_KEY)
            print("✅ Redis缓存已清除")
        except Exception as e:
            print(f"⚠️ Redis缓存清除失败: {e}")


@router.post("/clear-cache")
async def clear_cache(store_name: Optional[str] = Query(None, description="门店名称，不指定则清除全部")):
    """
    清除订单数据缓存
    
    Args:
        store_name: 指定门店则只清除该门店缓存，否则清除全部
    """
    invalidate_cache(store_name)
    return {
        "success": True, 
        "message": f"缓存已清除 (门店: {store_name or '全部'})"
    }


def calculate_order_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    统一的订单指标计算函数（与老版本完全一致）
    
    核心计算逻辑:
    1. 订单级聚合（订单级字段用first，商品级字段用sum）
    2. 计算订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    3. 按渠道类型过滤异常订单
    """
    if df.empty or '订单ID' not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    
    # 统一订单ID类型为字符串
    df['订单ID'] = df['订单ID'].astype(str)
    
    # 兼容不同成本字段名
    cost_field = '商品采购成本' if '商品采购成本' in df.columns else '成本'
    sales_field = '月售' if '月售' in df.columns else '销量'
    
    # 空值填充
    df['物流配送费'] = df['物流配送费'].fillna(0)
    df['配送费减免金额'] = df['配送费减免金额'].fillna(0)
    df['用户支付配送费'] = df['用户支付配送费'].fillna(0)
    
    # 计算订单总收入（实收价格 × 销量）
    if '实收价格' in df.columns and sales_field in df.columns:
        df['订单总收入'] = df['实收价格'] * df[sales_field]
    
    # 订单级聚合
    agg_dict = {
        '商品实售价': 'sum',
        '预计订单收入': 'sum',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '物流配送费': 'first',
        '平台佣金': 'first',
    }
    
    if sales_field in df.columns:
        agg_dict[sales_field] = 'sum'
    if '平台服务费' in df.columns:
        agg_dict['平台服务费'] = 'sum'
    if '订单总收入' in df.columns:
        agg_dict['订单总收入'] = 'sum'
    if '利润额' in df.columns:
        agg_dict['利润额'] = 'sum'
    if '企客后返' in df.columns:
        agg_dict['企客后返'] = 'sum'
    if cost_field in df.columns:
        agg_dict[cost_field] = 'sum'
    
    # 订单级字段用first
    for field in ['满减金额', '商品减免金额', '新客减免金额', '渠道', '门店名称', '日期', 
                  '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠']:
        if field in df.columns:
            agg_dict[field] = 'first'
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    
    # 将订单总收入重命名为实收价格
    if '订单总收入' in order_agg.columns:
        order_agg['实收价格'] = order_agg['订单总收入']
    
    # 统一成本字段名
    if cost_field == '成本' and cost_field in order_agg.columns:
        order_agg['商品采购成本'] = order_agg['成本']
    
    # 关键字段兜底
    if '平台服务费' not in order_agg.columns:
        order_agg['平台服务费'] = 0
    order_agg['平台服务费'] = order_agg['平台服务费'].fillna(0)
    
    if '企客后返' not in order_agg.columns:
        order_agg['企客后返'] = 0
    order_agg['企客后返'] = order_agg['企客后返'].fillna(0)
    
    if '平台佣金' not in order_agg.columns:
        order_agg['平台佣金'] = order_agg['平台服务费']
    order_agg['平台佣金'] = order_agg['平台佣金'].fillna(0)
    
    if '利润额' not in order_agg.columns:
        order_agg['利润额'] = 0
    order_agg['利润额'] = order_agg['利润额'].fillna(0)
    
    # 计算订单实际利润（核心公式）
    # 公式: 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    order_agg['订单实际利润'] = (
        order_agg['利润额'] -
        order_agg['平台服务费'] -
        order_agg['物流配送费'] +
        order_agg['企客后返']
    )
    
    # ==================== 计算配送净成本（与Dash版本一致） ====================
    # 公式: 配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返
    order_agg['配送净成本'] = (
        order_agg['物流配送费'] -
        (order_agg['用户支付配送费'] - order_agg['配送费减免金额']) -
        order_agg['企客后返']
    )
    
    # ==================== 计算商家活动成本（对齐Dash版本：7个营销字段） ====================
    # 公式: 商家活动成本 = 满减金额 + 商品减免金额 + 商家代金券 + 商家承担部分券 + 满赠金额 + 商家其他优惠 + 新客减免金额
    # 说明: 配送费减免金额属于配送成本，不属于营销成本
    marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
    order_agg['商家活动成本'] = 0
    for field in marketing_fields:
        if field in order_agg.columns:
            order_agg['商家活动成本'] += order_agg[field].fillna(0)
    
    # 按渠道类型过滤异常订单
    if '渠道' in order_agg.columns:
        is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
        is_zero_fee = order_agg['平台服务费'] <= 0
        invalid_orders = is_fee_channel & is_zero_fee
        order_agg = order_agg[~invalid_orders].copy()
    
    return order_agg


def calculate_gmv(df: pd.DataFrame) -> Dict[str, float]:
    """
    计算门店GMV（营业额）
    
    GMV计算公式（用户确认）：
    GMV = Σ(商品原价 × 销量) + Σ(打包袋金额) + Σ(用户支付配送费)
    
    数据清洗规则（重要！）：
    1. **剔除商品原价 <= 0 的整行数据**（包括该行的打包袋金额和用户支付配送费）
    2. 商品原价是商品级字段，需要乘以销量才能得出准确的原价销售金额
    3. 打包袋金额是订单级字段，一个订单只收取一次打包费，需要用first聚合避免重复
    4. 用户支付配送费是订单级字段，清洗逻辑和打包袋金额一致
    
    营销成本率计算：
    营销成本率 = 营销成本 / GMV × 100%
    
    验证数据（惠宜选超市昆山淀山湖镇店 2026-01-18）：
    - 预期GMV: 8440.66
    - 预期营销成本: 1122
    - 预期营销成本率: ~13.30%
    
    Args:
        df: 原始订单数据DataFrame（商品级，未聚合）
    
    Returns:
        Dict包含:
        - gmv: 营业额
        - original_price_sales: 商品原价销售额
        - packaging_fee: 打包袋金额
        - user_delivery_fee: 用户支付配送费
        - marketing_cost: 营销成本（7字段）
        - marketing_cost_rate: 营销成本率
    """
    if df.empty:
        return {
            "gmv": 0,
            "original_price_sales": 0,
            "packaging_fee": 0,
            "user_delivery_fee": 0,
            "marketing_cost": 0,
            "marketing_cost_rate": 0
        }
    
    df = df.copy()
    
    # 确保必要字段存在
    sales_field = '月售' if '月售' in df.columns else '销量'
    
    # 1. 剔除商品原价 <= 0 的整行数据（关键！包括该行的打包袋金额和用户支付配送费）
    # 用户确认：商品原价=0的订单没有实际商品销售，其打包袋和配送费也不应计入GMV
    if '商品原价' in df.columns:
        df = df[df['商品原价'] > 0].copy()
    
    if df.empty:
        return {
            "gmv": 0,
            "original_price_sales": 0,
            "packaging_fee": 0,
            "user_delivery_fee": 0,
            "marketing_cost": 0,
            "marketing_cost_rate": 0
        }
    
    # 2. 计算商品原价销售额 = Σ(商品原价 × 销量)
    # 商品原价是商品级字段（单价），需要乘以销量
    if '商品原价' in df.columns and sales_field in df.columns:
        df['原价销售额'] = df['商品原价'].fillna(0) * df[sales_field].fillna(1)
        original_price_sales = df['原价销售额'].sum()
    else:
        original_price_sales = 0
    
    # 3. 计算订单级字段（打包袋金额、用户支付配送费）
    # 这些是订单级字段，需要按订单ID聚合后用first取值，避免重复计算
    # 注意：此时df已经剔除了商品原价<=0的行，所以只有有效订单的数据会被计入
    if '订单ID' in df.columns:
        # 订单级字段聚合
        order_level_agg = df.groupby('订单ID').agg({
            '打包袋金额': 'first' if '打包袋金额' in df.columns else lambda x: 0,
            '用户支付配送费': 'first' if '用户支付配送费' in df.columns else lambda x: 0,
            # 营销成本字段（订单级）
            '满减金额': 'first' if '满减金额' in df.columns else lambda x: 0,
            '商品减免金额': 'first' if '商品减免金额' in df.columns else lambda x: 0,
            '商家代金券': 'first' if '商家代金券' in df.columns else lambda x: 0,
            '商家承担部分券': 'first' if '商家承担部分券' in df.columns else lambda x: 0,
            '满赠金额': 'first' if '满赠金额' in df.columns else lambda x: 0,
            '商家其他优惠': 'first' if '商家其他优惠' in df.columns else lambda x: 0,
            '新客减免金额': 'first' if '新客减免金额' in df.columns else lambda x: 0,
        }).reset_index()
        
        packaging_fee = order_level_agg['打包袋金额'].sum() if '打包袋金额' in order_level_agg.columns else 0
        user_delivery_fee = order_level_agg['用户支付配送费'].sum() if '用户支付配送费' in order_level_agg.columns else 0
        
        # 计算营销成本（7字段）
        marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
        marketing_cost = 0
        for field in marketing_fields:
            if field in order_level_agg.columns:
                marketing_cost += order_level_agg[field].fillna(0).sum()
    else:
        packaging_fee = 0
        user_delivery_fee = 0
        marketing_cost = 0
    
    # 4. 计算GMV
    gmv = original_price_sales + packaging_fee + user_delivery_fee
    
    # 5. 计算营销成本率
    marketing_cost_rate = (marketing_cost / gmv * 100) if gmv > 0 else 0
    
    return {
        "gmv": round(gmv, 2),
        "original_price_sales": round(original_price_sales, 2),
        "packaging_fee": round(packaging_fee, 2),
        "user_delivery_fee": round(user_delivery_fee, 2),
        "marketing_cost": round(marketing_cost, 2),
        "marketing_cost_rate": round(marketing_cost_rate, 2)
    }


@router.get("/overview")
async def get_order_overview(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    use_aggregation: bool = Query(False, description="是否使用预聚合表（默认禁用，确保数据与看板系统一致）")
) -> Dict[str, Any]:
    """
    获取订单数据概览（六大核心卡片）
    
    与老版本Tab1完全一致的指标:
    - 📦 订单总数
    - 💰 商品实收额
    - 💎 总利润（订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返）
    - 🛒 平均客单价
    - 📈 总利润率
    - 🏷️ 动销商品数
    
    注意：默认使用原始查询，确保数据与看板系统一致
    （原始查询会过滤收费渠道中平台服务费=0的异常订单）
    """
    import time
    query_start = time.time()
    
    # ✅ 优先使用预聚合表（包含GMV字段）
    if use_aggregation:
        try:
            from app.services.aggregation_service import aggregation_service
            result = aggregation_service.get_store_overview(
                store_name=store_name,
                start_date=start_date,
                end_date=end_date
            )
            # 🔧 修复：检查预聚合表是否有有效数据（订单数 > 0）
            if result and result.get("total_orders", 0) > 0:
                # 预聚合表有数据
                if result.get("gmv", 0) > 0:
                    # 预聚合表有GMV数据，直接使用
                    print(f"✅ [预聚合表+GMV] overview查询耗时: {(time.time()-query_start)*1000:.1f}ms")
                    return {"success": True, "data": result}
                else:
                    # 预聚合表没有GMV数据，需要从原始数据计算GMV
                    df = get_order_data(store_name)
                    if not df.empty:
                        # 日期筛选
                        if '日期' in df.columns:
                            df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
                            if start_date:
                                df = df[df['日期'].dt.date >= start_date]
                            if end_date:
                                df = df[df['日期'].dt.date <= end_date]
                        
                        # 计算GMV和营销成本率
                        gmv_data = calculate_gmv(df)
                        result["gmv"] = gmv_data["gmv"]
                        result["marketing_cost"] = gmv_data["marketing_cost"]
                        result["marketing_cost_rate"] = gmv_data["marketing_cost_rate"]
                    else:
                        result["gmv"] = 0
                        result["marketing_cost"] = 0
                        result["marketing_cost_rate"] = 0
                    
                    print(f"✅ [预聚合表+原始GMV] overview查询耗时: {(time.time()-query_start)*1000:.1f}ms")
                    return {"success": True, "data": result}
            else:
                # 🔧 预聚合表没有数据，回退到原始查询
                print(f"⚠️ 预聚合表无数据(store={store_name})，回退到原始查询")
        except Exception as e:
            print(f"⚠️ 预聚合表查询失败，回退到原始查询: {e}")
    
    # 回退到原始查询
    # 按门店加载数据（利用缓存）
    df = get_order_data(store_name)
    if df.empty:
        return {
            "success": True,
            "data": {
                "total_orders": 0,
                "total_actual_sales": 0,
                "total_profit": 0,
                "avg_order_value": 0,
                "profit_rate": 0,
                "active_products": 0,
            }
        }
    
    # 日期筛选
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        if start_date:
            df = df[df['日期'].dt.date >= start_date]
        if end_date:
            df = df[df['日期'].dt.date <= end_date]
    
    if df.empty:
        return {
            "success": True,
            "data": {
                "total_orders": 0,
                "total_actual_sales": 0,
                "total_profit": 0,
                "avg_order_value": 0,
                "profit_rate": 0,
                "active_products": 0,
            }
        }
    
    # 计算订单级指标
    order_agg = calculate_order_metrics(df)
    
    # 六大核心卡片
    total_orders = len(order_agg)
    total_actual_sales = order_agg['实收价格'].sum() if '实收价格' in order_agg.columns else 0
    total_profit = order_agg['订单实际利润'].sum() if '订单实际利润' in order_agg.columns else 0
    avg_order_value = total_actual_sales / total_orders if total_orders > 0 else 0
    profit_rate = (total_profit / total_actual_sales * 100) if total_actual_sales > 0 else 0
    
    # 动销商品数（有销量的SKU）
    sales_field = '月售' if '月售' in df.columns else '销量'
    if '商品名称' in df.columns and sales_field in df.columns:
        active_products = df[df[sales_field] > 0]['商品名称'].nunique()
    else:
        active_products = df['商品名称'].nunique() if '商品名称' in df.columns else 0
    
    # ✅ 新增：计算GMV和营销成本率（基于用户确认的公式）
    gmv_data = calculate_gmv(df)
    
    print(f"⚠️ [原始查询] overview查询耗时: {(time.time()-query_start)*1000:.1f}ms")
    
    return {
        "success": True,
        "data": {
            "total_orders": int(total_orders),
            "total_actual_sales": round(float(total_actual_sales), 2),
            "total_profit": round(float(total_profit), 2),
            "avg_order_value": round(float(avg_order_value), 2),
            "profit_rate": round(float(profit_rate), 2),
            "active_products": int(active_products),
            # ✅ 新增：GMV和营销成本率
            "gmv": gmv_data["gmv"],
            "marketing_cost": gmv_data["marketing_cost"],
            "marketing_cost_rate": gmv_data["marketing_cost_rate"],
        }
    }


@router.get("/all-stores-overview")
async def get_all_stores_overview(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    channels: Optional[str] = Query(None, description="渠道筛选，多个渠道用逗号分隔"),
) -> Dict[str, Any]:
    """
    获取全门店销售总览数据（经营总览 - 全门店横向对比）
    
    不依赖 selectedStore，始终加载所有门店进行对比。
    复用 calculate_order_metrics 和 calculate_gmv 确保计算结果与单门店概览一致。
    
    返回每个门店的 8 个指标：
    - 销售额、订单量、利润、利润率
    - 客单价、营销成本率、单均配送费、单均利润
    """
    import time
    query_start = time.time()
    
    # 加载全部门店数据（不指定 store_name）
    df = get_order_data(store_name=None)
    
    if df.empty or '门店名称' not in df.columns:
        return {"success": True, "data": {"stores": []}}
    
    # 渠道筛选（支持多选，逗号分隔）
    if channels and '渠道' in df.columns:
        channel_list = [ch.strip() for ch in channels.split(',') if ch.strip()]
        if channel_list:
            df = df[df['渠道'].isin(channel_list)]
            if df.empty:
                return {"success": True, "data": {"stores": []}}
    
    # 日期预处理
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    
    # 1. 计算当前周期数据
    current_df = df.copy()
    
    # DEBUG: Print data types
    print(f"DEBUG: start_date={start_date} type={type(start_date)}, end_date={end_date} type={type(end_date)}, channels={channels}")
    
    # 强制确保日期列为 datetime
    if '日期' in current_df.columns:
         current_df['日期'] = pd.to_datetime(current_df['日期'])

    if start_date:
        # start_date 已经是 date 对象 (Line 767)
        current_df = current_df[current_df['日期'].dt.date >= start_date]
    if end_date:
        current_df = current_df[current_df['日期'].dt.date <= end_date]
        
    if current_df.empty:
        return {"success": True, "data": {"stores": []}}

    # 2. 计算环比周期数据 (Previous Period)
    prev_start_date = None
    prev_end_date = None
    prev_metrics_map = {}  # {store_name: {metric: value, ...}}
    
    # 当未指定日期范围时，自动使用最近7天 vs 前7天计算环比
    effective_start = start_date
    effective_end = end_date
    auto_trend_mode = False
    current_sales_map = {}  # 自动环比模式下的当期销售额
    if not start_date or not end_date:
        if '日期' in current_df.columns and not current_df.empty:
            max_date = current_df['日期'].dt.date.max()
            effective_end = max_date
            effective_start = max_date - timedelta(days=6)  # 最近7天
            auto_trend_mode = True
            # 计算当期（最近7天）每门店的销售额
            curr_mask = (current_df['日期'].dt.date >= effective_start) & (current_df['日期'].dt.date <= effective_end)
            curr_trend_df = current_df[curr_mask]
            if not curr_trend_df.empty and '实收价格' in curr_trend_df.columns:
                current_sales_map = curr_trend_df.groupby('门店名称')['实收价格'].sum().to_dict()
    
    if effective_start and effective_end:
        duration = effective_end - effective_start
        prev_end_date = effective_start - timedelta(days=1)
        prev_start_date = prev_end_date - duration
        
        prev_mask = (df['日期'].dt.date >= prev_start_date) & (df['日期'].dt.date <= prev_end_date)
        prev_df = df[prev_mask]
        
        if not prev_df.empty:
            # 预计算所有门店的上期销售额，避免循环内重复过滤
            # 注意：需确保 '实收价格' 列存在且为数值
            if '实收价格' in prev_df.columns:
                # 预计算所有门店的上期全部指标
                for prev_store in prev_df['门店名称'].dropna().unique():
                    prev_store_df = prev_df[prev_df['门店名称'] == prev_store]
                    prev_order_agg = calculate_order_metrics(prev_store_df)
                    if prev_order_agg.empty:
                        continue
                    prev_oc = len(prev_order_agg)
                    prev_ts = float(prev_order_agg['实收价格'].sum()) if '实收价格' in prev_order_agg.columns else 0
                    prev_tp = float(prev_order_agg['订单实际利润'].sum()) if '订单实际利润' in prev_order_agg.columns else 0
                    prev_tdf = float(prev_order_agg['物流配送费'].sum()) if '物流配送费' in prev_order_agg.columns else 0
                    prev_pr = (prev_tp / prev_ts * 100) if prev_ts > 0 else 0
                    prev_aov = prev_ts / prev_oc if prev_oc > 0 else 0
                    prev_adf = prev_tdf / prev_oc if prev_oc > 0 else 0
                    prev_ap = prev_tp / prev_oc if prev_oc > 0 else 0
                    prev_gmv = calculate_gmv(prev_store_df)
                    prev_mcr = prev_gmv["marketing_cost_rate"]
                    prev_metrics_map[prev_store] = {
                        'total_sales': prev_ts, 'order_count': prev_oc,
                        'total_profit': prev_tp, 'profit_rate': prev_pr,
                        'avg_order_value': prev_aov, 'marketing_cost_rate': prev_mcr,
                        'avg_delivery_fee': prev_adf, 'avg_profit': prev_ap,
                    }

    # 自动环比模式：也需要计算当期（最近7天）的指标用于对比
    current_trend_metrics_map = {}
    if auto_trend_mode and effective_start and effective_end:
        curr_mask = (current_df['日期'].dt.date >= effective_start) & (current_df['日期'].dt.date <= effective_end)
        curr_trend_df = current_df[curr_mask]
        if not curr_trend_df.empty:
            for ct_store in curr_trend_df['门店名称'].dropna().unique():
                ct_store_df = curr_trend_df[curr_trend_df['门店名称'] == ct_store]
                ct_order_agg = calculate_order_metrics(ct_store_df)
                if ct_order_agg.empty:
                    continue
                ct_oc = len(ct_order_agg)
                ct_ts = float(ct_order_agg['实收价格'].sum()) if '实收价格' in ct_order_agg.columns else 0
                ct_tp = float(ct_order_agg['订单实际利润'].sum()) if '订单实际利润' in ct_order_agg.columns else 0
                ct_tdf = float(ct_order_agg['物流配送费'].sum()) if '物流配送费' in ct_order_agg.columns else 0
                ct_pr = (ct_tp / ct_ts * 100) if ct_ts > 0 else 0
                ct_aov = ct_ts / ct_oc if ct_oc > 0 else 0
                ct_adf = ct_tdf / ct_oc if ct_oc > 0 else 0
                ct_ap = ct_tp / ct_oc if ct_oc > 0 else 0
                ct_gmv = calculate_gmv(ct_store_df)
                ct_mcr = ct_gmv["marketing_cost_rate"]
                current_trend_metrics_map[ct_store] = {
                    'total_sales': ct_ts, 'order_count': ct_oc,
                    'total_profit': ct_tp, 'profit_rate': ct_pr,
                    'avg_order_value': ct_aov, 'marketing_cost_rate': ct_mcr,
                    'avg_delivery_fee': ct_adf, 'avg_profit': ct_ap,
                }

    # 按门店分组计算
    store_names = current_df['门店名称'].dropna().unique().tolist()
    stores_result = []
    
    # 环比计算辅助函数
    def calc_trend_pct(curr_val: float, prev_val: float) -> float:
        """百分比变化率，用于绝对值指标"""
        if prev_val > 0:
            return round(((curr_val - prev_val) / prev_val) * 100, 1)
        return 0.0
    
    def calc_trend_pt(curr_val: float, prev_val: float) -> float:
        """百分点差值，用于率类指标"""
        return round(curr_val - prev_val, 1)
    
    for store in store_names:
        store_df = current_df[current_df['门店名称'] == store]
        if store_df.empty:
            continue
        
        # 3. 订单级聚合 (Current Metrics)
        order_agg = calculate_order_metrics(store_df)
        if order_agg.empty:
            continue
        
        order_count = len(order_agg)
        total_sales = float(order_agg['实收价格'].sum()) if '实收价格' in order_agg.columns else 0
        total_profit = float(order_agg['订单实际利润'].sum()) if '订单实际利润' in order_agg.columns else 0
        total_delivery_fee = float(order_agg['物流配送费'].sum()) if '物流配送费' in order_agg.columns else 0
        
        profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
        avg_order_value = total_sales / order_count if order_count > 0 else 0
        avg_delivery_fee = total_delivery_fee / order_count if order_count > 0 else 0
        avg_profit = total_profit / order_count if order_count > 0 else 0
        
        # 4. GMV & 营销成本率
        gmv_data = calculate_gmv(store_df)
        marketing_cost_rate = gmv_data["marketing_cost_rate"]
        
        # 5. 每个指标的环比
        # 自动环比模式用 current_trend_metrics_map，有日期范围时用当前完整数据
        if auto_trend_mode:
            curr_m = current_trend_metrics_map.get(store, {})
        else:
            curr_m = {
                'total_sales': total_sales, 'order_count': order_count,
                'total_profit': total_profit, 'profit_rate': profit_rate,
                'avg_order_value': avg_order_value, 'marketing_cost_rate': marketing_cost_rate,
                'avg_delivery_fee': avg_delivery_fee, 'avg_profit': avg_profit,
            }
        prev_m = prev_metrics_map.get(store, {})
        
        # 上期无数据时，所有环比返回 None（前端不渲染）
        if not prev_m:
            trends = {
                'trend_sales': None, 'trend_orders': None,
                'trend_profit': None, 'trend_profit_rate': None,
                'trend_avg_value': None, 'trend_marketing_rate': None,
                'trend_delivery_fee': None, 'trend_avg_profit': None,
            }
        else:
            trends = {
                'trend_sales': calc_trend_pct(curr_m.get('total_sales', 0), prev_m.get('total_sales', 0)),
                'trend_orders': calc_trend_pct(curr_m.get('order_count', 0), prev_m.get('order_count', 0)),
                'trend_profit': calc_trend_pct(curr_m.get('total_profit', 0), prev_m.get('total_profit', 0)),
                'trend_profit_rate': calc_trend_pt(curr_m.get('profit_rate', 0), prev_m.get('profit_rate', 0)),
                'trend_avg_value': calc_trend_pct(curr_m.get('avg_order_value', 0), prev_m.get('avg_order_value', 0)),
                'trend_marketing_rate': calc_trend_pt(curr_m.get('marketing_cost_rate', 0), prev_m.get('marketing_cost_rate', 0)),
                'trend_delivery_fee': calc_trend_pct(curr_m.get('avg_delivery_fee', 0), prev_m.get('avg_delivery_fee', 0)),
                'trend_avg_profit': calc_trend_pct(curr_m.get('avg_profit', 0), prev_m.get('avg_profit', 0)),
            }

        stores_result.append({
            "store_name": store,
            "total_sales": round(total_sales, 2),
            "order_count": int(order_count),
            "total_profit": round(total_profit, 2),
            "profit_rate": round(profit_rate, 2),
            "avg_order_value": round(avg_order_value, 2),
            "marketing_cost_rate": round(marketing_cost_rate, 2),
            "avg_delivery_fee": round(avg_delivery_fee, 2),
            "avg_profit": round(avg_profit, 2),
            **trends,
        })
    
    # 按销售额降序排列
    stores_result.sort(key=lambda x: x["total_sales"], reverse=True)
    
    print(f"📊 [全门店总览] {len(stores_result)} 个门店, 耗时: {(time.time()-query_start)*1000:.1f}ms")
    
    return {"success": True, "data": {"stores": stores_result}}


@router.get("/channels")
async def get_channel_stats(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    获取渠道表现对比数据
    
    与老版本Tab1渠道卡片完全一致
    注意：排除咖啡渠道（美团咖啡店、饿了么咖啡店）
    """
    # 按门店加载数据
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": []}
    
    # 日期筛选
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    if start_date:
        df = df[df['日期'].dt.date >= start_date]
    if end_date:
        df = df[df['日期'].dt.date <= end_date]
    
    if df.empty or '渠道' not in df.columns:
        return {"success": True, "data": []}
    
    # 计算订单级指标
    order_agg = calculate_order_metrics(df)
    
    if order_agg.empty or '渠道' not in order_agg.columns:
        return {"success": True, "data": []}
    
    # 排除咖啡渠道（与老版本一致）
    CHANNELS_TO_REMOVE = ['美团咖啡店', '饿了么咖啡店']
    order_agg = order_agg[~order_agg['渠道'].isin(CHANNELS_TO_REMOVE)]
    
    if order_agg.empty:
        return {"success": True, "data": []}
    
    # 按渠道聚合
    channel_stats = order_agg.groupby('渠道').agg({
        '订单ID': 'count',
        '实收价格': 'sum',
        '订单实际利润': 'sum',
    }).reset_index()
    
    channel_stats.columns = ['channel', 'order_count', 'amount', 'profit']
    
    # 计算派生指标
    total_orders = channel_stats['order_count'].sum()
    total_amount = channel_stats['amount'].sum()
    
    channel_stats['order_ratio'] = (channel_stats['order_count'] / total_orders * 100) if total_orders > 0 else 0
    channel_stats['amount_ratio'] = (channel_stats['amount'] / total_amount * 100) if total_amount > 0 else 0
    channel_stats['avg_value'] = channel_stats.apply(
        lambda r: r['amount'] / r['order_count'] if r['order_count'] > 0 else 0, axis=1
    )
    channel_stats['profit_rate'] = channel_stats.apply(
        lambda r: r['profit'] / r['amount'] * 100 if r['amount'] > 0 else 0, axis=1
    )
    
    # 按订单数排序
    channel_stats = channel_stats.sort_values('order_count', ascending=False)
    
    # 转换为列表
    result = []
    for _, row in channel_stats.iterrows():
        result.append({
            "channel": row['channel'],
            "order_count": int(row['order_count']),
            "amount": round(float(row['amount']), 2),
            "profit": round(float(row['profit']), 2),
            "order_ratio": round(float(row['order_ratio']), 2),
            "amount_ratio": round(float(row['amount_ratio']), 2),
            "avg_value": round(float(row['avg_value']), 2),
            "profit_rate": round(float(row['profit_rate']), 2),
        })
    
    return {"success": True, "data": result}


@router.get("/trend")
async def get_order_trend(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    channel: Optional[str] = Query(None, description="渠道筛选，'all'或空表示全部渠道"),
    start_date: Optional[str] = Query(None, description="日期范围开始(YYYY-MM-DD格式)"),
    end_date: Optional[str] = Query(None, description="日期范围结束(YYYY-MM-DD格式)"),
    granularity: str = Query("day", description="粒度: day/week/month"),
    use_aggregation: bool = Query(False, description="是否使用预聚合表（默认禁用，确保数据一致性）")
) -> Dict[str, Any]:
    """
    获取订单趋势数据（与Dash版本销售趋势分析一致）
    
    返回每日/每周/每月的订单数、销售额、利润、客单价、利润率
    
    支持两种日期筛选方式：
    - days: 最近N天（默认30天）
    - start_date + end_date: 指定日期范围（优先级更高）
    
    计算逻辑与Dash版本 calculate_daily_sales_with_channel 完全一致：
    - 利润率 = 总利润 / 销售额 * 100
    - 渠道筛选：支持按渠道过滤数据
    
    注意：默认使用原始查询，确保数据与看板系统一致
    """
    import time
    query_start = time.time()
    
    empty_result = {
        "success": True, 
        "data": {
            "dates": [], "order_counts": [], "amounts": [], 
            "profits": [], "avg_values": [], "profit_rates": []
        }
    }
    
    # ✅ 优先使用预聚合表（仅支持日粒度，无渠道筛选时）
    if use_aggregation and granularity == 'day':
        try:
            from app.services.aggregation_service import aggregation_service
            
            # 解析日期参数
            from datetime import date as date_type
            agg_start = None
            agg_end = None
            
            if start_date and end_date:
                try:
                    agg_start = date_type.fromisoformat(start_date)
                    agg_end = date_type.fromisoformat(end_date)
                except:
                    pass
            
            # 映射渠道参数
            agg_channel = None
            if channel and channel != 'all':
                agg_channel = channel
            
            result = aggregation_service.get_daily_trend(
                store_name=store_name,
                start_date=agg_start,
                end_date=agg_end,
                channel=agg_channel
            )
            
            if result and len(result) > 0:
                # 转换为API响应格式
                dates = [r['date'] for r in result]
                order_counts = [r['orders'] for r in result]
                amounts = [r['revenue'] for r in result]
                profits = [r['profit'] for r in result]
                avg_values = [round(r['revenue'] / r['orders'], 2) if r['orders'] > 0 else 0 for r in result]
                profit_rates = [round(r['profit'] / r['revenue'] * 100, 2) if r['revenue'] > 0 else 0 for r in result]
                
                print(f"✅ [预聚合表] trend查询耗时: {(time.time()-query_start)*1000:.1f}ms, {len(result)}条记录")
                
                return {
                    "success": True,
                    "data": {
                        "dates": dates,
                        "order_counts": order_counts,
                        "amounts": amounts,
                        "profits": profits,
                        "avg_values": avg_values,
                        "profit_rates": profit_rates,
                    }
                }
        except Exception as e:
            print(f"⚠️ 预聚合表查询失败，回退到原始查询: {e}")
    
    # 回退到原始查询
    # 按门店加载数据（利用缓存）
    df = get_order_data(store_name)
    
    if df.empty:
        return empty_result
    
    if '日期' not in df.columns:
        return {"success": False, "error": "缺少日期字段"}
    
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    
    if df.empty:
        return empty_result
    
    # 🆕 日期筛选：优先使用日期范围，否则使用最近N天
    if start_date and end_date:
        try:
            range_start = pd.to_datetime(start_date)
            range_end = pd.to_datetime(end_date)
            df = df[(df['日期'].dt.date >= range_start.date()) & (df['日期'].dt.date <= range_end.date())]
        except:
            # 日期解析失败，回退到默认行为
            max_date = df['日期'].max()
            min_date = max_date - timedelta(days=days)
            df = df[df['日期'] >= min_date]
    else:
        # 筛选最近N天
        max_date = df['日期'].max()
        if pd.isna(max_date):
            return empty_result
        
        min_date = max_date - timedelta(days=days)
        df = df[df['日期'] >= min_date]
    
    if df.empty:
        return empty_result
    
    # 先聚合到订单级（与Dash版本一致）
    order_agg = calculate_order_metrics(df)
    
    if order_agg.empty:
        return empty_result
    
    # 🆕 渠道筛选（与Dash版本 calculate_daily_sales_with_channel 一致）
    if channel and channel != 'all' and '渠道' in order_agg.columns:
        before_filter = len(order_agg)
        order_agg = order_agg[order_agg['渠道'] == channel].copy()
        after_filter = len(order_agg)
        print(f"🔍 [trend API] 渠道筛选: {before_filter} -> {after_filter} 订单 (渠道='{channel}')")
        
        if order_agg.empty:
            return empty_result
    
    # 根据粒度分组
    if '日期' in order_agg.columns:
        order_agg['日期'] = pd.to_datetime(order_agg['日期'])
        if granularity == 'week':
            order_agg['period'] = order_agg['日期'].dt.to_period('W').apply(lambda x: x.start_time)
        elif granularity == 'month':
            order_agg['period'] = order_agg['日期'].dt.to_period('M').apply(lambda x: x.start_time)
        else:
            order_agg['period'] = order_agg['日期'].dt.date
        
        # 按周期聚合（与Dash版本一致）
        daily = order_agg.groupby('period').agg({
            '订单ID': 'count',
            '实收价格': 'sum',
            '订单实际利润': 'sum',
        }).reset_index()
        
        daily.columns = ['date', 'order_count', 'amount', 'profit']
    else:
        # 备用方案：按原始数据日期聚合
        if granularity == 'week':
            df['period'] = df['日期'].dt.to_period('W').apply(lambda x: x.start_time)
        elif granularity == 'month':
            df['period'] = df['日期'].dt.to_period('M').apply(lambda x: x.start_time)
        else:
            df['period'] = df['日期'].dt.date
            
        daily = df.groupby('period').agg({
            '订单ID': 'nunique' if '订单ID' in df.columns else 'count',
            '实收价格': 'sum' if '实收价格' in df.columns else lambda x: 0,
            '利润额': 'sum' if '利润额' in df.columns else lambda x: 0,
        }).reset_index()
        daily.columns = ['date', 'order_count', 'amount', 'profit']
    
    daily = daily.sort_values('date')
    
    # 计算客单价
    daily['avg_value'] = daily.apply(
        lambda r: r['amount'] / r['order_count'] if r['order_count'] > 0 else 0, axis=1
    )
    
    # 🆕 计算利润率（与Dash版本一致：利润率 = 总利润 / 销售额 * 100）
    daily['profit_rate'] = daily.apply(
        lambda r: round(r['profit'] / r['amount'] * 100, 2) if r['amount'] > 0 else 0, axis=1
    )
    
    print(f"⚠️ [原始查询] trend查询耗时: {(time.time()-query_start)*1000:.1f}ms")
    
    return {
        "success": True,
        "data": {
            "dates": [str(d) for d in daily['date'].tolist()],
            "order_counts": [int(x) for x in daily['order_count'].tolist()],
            "amounts": [round(float(x), 2) for x in daily['amount'].tolist()],
            "profits": [round(float(x), 2) for x in daily['profit'].tolist()],
            "avg_values": [round(float(x), 2) for x in daily['avg_value'].tolist()],
            "profit_rates": [float(x) for x in daily['profit_rate'].tolist()],
        }
    }


@router.get("/list")
async def get_order_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    store_name: Optional[str] = Query(None, description="门店筛选"),
    channel: Optional[str] = Query(None, description="渠道筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    sort_by: str = Query("date", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向")
) -> Dict[str, Any]:
    """
    获取订单列表（支持分页和筛选）
    """
    # 按门店加载数据（利用缓存）
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
    
    # 渠道筛选
    if channel and '渠道' in df.columns:
        df = df[df['渠道'] == channel]
    
    # 日期筛选
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        if start_date:
            df = df[df['日期'].dt.date >= start_date]
        if end_date:
            df = df[df['日期'].dt.date <= end_date]
    
    if df.empty:
        return {"success": True, "data": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
    
    # 计算订单级指标
    order_agg = calculate_order_metrics(df)
    
    # 排序
    sort_col_map = {
        'date': '日期',
        'amount': '实收价格',
        'profit': '订单实际利润',
    }
    sort_col = sort_col_map.get(sort_by, '日期')
    if sort_col in order_agg.columns:
        order_agg = order_agg.sort_values(sort_col, ascending=(sort_order == 'asc'))
    
    # 分页
    total = len(order_agg)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = order_agg.iloc[start:end]
    
    # 选择展示字段
    result = []
    for _, row in page_data.iterrows():
        item = {
            "order_id": row.get('订单ID', ''),
            "order_date": str(row.get('日期', ''))[:10] if pd.notna(row.get('日期')) else '',
            "store_name": row.get('门店名称', ''),
            "channel": row.get('渠道', ''),
            "amount": round(float(row.get('实收价格', 0)), 2),
            "profit": round(float(row.get('订单实际利润', 0)), 2),
            "profit_rate": round(float(row.get('订单实际利润', 0)) / float(row.get('实收价格', 1)) * 100, 2) if row.get('实收价格', 0) > 0 else 0,
        }
        result.append(item)
    
    return {
        "success": True,
        "data": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/stores")
async def get_store_list() -> Dict[str, Any]:
    """获取门店列表（直接从数据库查询）"""
    try:
        from database.connection import SessionLocal
        from database.models import Order
        from sqlalchemy import distinct
        
        session = SessionLocal()
        try:
            # 直接查询数据库中的门店列表
            stores = session.query(distinct(Order.store_name)).filter(
                Order.store_name.isnot(None)
            ).all()
            
            store_list = sorted([s[0] for s in stores if s[0]])
            print(f"✅ 门店列表查询成功: {len(store_list)} 个门店")
            return {"success": True, "data": store_list}
        finally:
            session.close()
    except Exception as e:
        print(f"⚠️ 门店列表查询失败: {e}")
        # 备用方案：从缓存数据获取
        df = get_order_data()
        if df.empty or '门店名称' not in df.columns:
            return {"success": True, "data": []}
        
        stores = sorted(df['门店名称'].dropna().unique().tolist())
        return {"success": True, "data": stores}


@router.get("/channel-list")
async def get_channel_list(
    store_name: Optional[str] = Query(None, description="门店名称筛选")
) -> Dict[str, Any]:
    """获取渠道列表（直接从数据库查询，支持门店筛选）"""
    try:
        from database.connection import SessionLocal
        from database.models import Order
        from sqlalchemy import distinct
        
        session = SessionLocal()
        try:
            # 构建查询
            query = session.query(distinct(Order.channel)).filter(
                Order.channel.isnot(None)
            )
            
            # 如果指定了门店，只返回该门店的渠道
            if store_name:
                query = query.filter(Order.store_name == store_name)
            
            channels = query.all()
            
            channel_list = sorted([c[0] for c in channels if c[0]])
            print(f"✅ 渠道列表查询成功: {len(channel_list)} 个渠道, 门店: {store_name or '全部'}")
            return {"success": True, "data": channel_list}
        finally:
            session.close()
    except Exception as e:
        print(f"⚠️ 渠道列表查询失败: {e}")
        # 备用方案：从缓存数据获取
        df = get_order_data(store_name)
        if df.empty or '渠道' not in df.columns:
            return {"success": True, "data": []}
        
        channels = sorted(df['渠道'].dropna().unique().tolist())
        return {"success": True, "data": channels}


# [Phase 2] Migrated to orders_analysis.py


# [Phase 2] Migrated to orders_analysis.py


# [Phase 2] Migrated to orders_analysis.py


# [Phase 2] Migrated to orders_analysis.py


@router.get("/comparison")
async def get_order_comparison(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    获取订单环比数据（与老版本完全一致）
    
    计算当前周期与上一周期的环比变化:
    - 订单数环比
    - 销售额环比
    - 利润环比
    - 客单价环比
    - 利润率环比（使用差值）
    - 动销商品数环比
    
    注意：如果不传日期参数，使用数据的完整日期范围作为当前周期
    """
    # 按门店加载数据（利用缓存）
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": {"current": {}, "previous": {}, "changes": {}, "period": {}}}
    
    if '日期' not in df.columns:
        return {"success": True, "data": {"current": {}, "previous": {}, "changes": {}, "period": {}}}
    
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])  # 移除无效日期
    
    if df.empty:
        return {"success": True, "data": {"current": {}, "previous": {}, "changes": {}, "period": {}}}
    
    # 确定日期范围
    min_date_in_data = df['日期'].min()
    max_date_in_data = df['日期'].max()
    
    if pd.isna(max_date_in_data) or pd.isna(min_date_in_data):
        return {"success": True, "data": {"current": {}, "previous": {}, "changes": {}, "period": {}}}
    
    # 如果不传日期参数，使用数据的完整日期范围（全部数据）
    if start_date is None and end_date is None:
        start_date = min_date_in_data.date()
        end_date = max_date_in_data.date()
    elif start_date is None:
        start_date = min_date_in_data.date()
    elif end_date is None:
        end_date = max_date_in_data.date()
    
    # 计算周期长度
    period_days = (end_date - start_date).days + 1
    if period_days <= 0:
        period_days = 1
    
    # 计算上一周期日期范围
    prev_end_date = start_date - timedelta(days=1)
    prev_start_date = prev_end_date - timedelta(days=period_days - 1)
    
    # 当前周期数据
    current_df = df[(df['日期'].dt.date >= start_date) & (df['日期'].dt.date <= end_date)]
    # 上一周期数据
    prev_df = df[(df['日期'].dt.date >= prev_start_date) & (df['日期'].dt.date <= prev_end_date)]
    
    print(f"📊 环比计算: 当前周期 {start_date} ~ {end_date} ({len(current_df)}条)")
    print(f"            上一周期 {prev_start_date} ~ {prev_end_date} ({len(prev_df)}条)")
    # 计算当前周期指标
    current_metrics = calculate_period_metrics(current_df)
    # 计算上一周期指标
    prev_metrics = calculate_period_metrics(prev_df)
    
    # 计算环比变化
    changes = {}
    for key in ['order_count', 'total_sales', 'total_profit', 'avg_order_value', 'active_products']:
        curr_val = current_metrics.get(key, 0)
        prev_val = prev_metrics.get(key, 0)
        if prev_val > 0:
            change_rate = round((curr_val - prev_val) / prev_val * 100, 2)
        elif curr_val > 0:
            change_rate = 100.0
        else:
            change_rate = 0.0
        changes[key] = change_rate
    
    # 利润率使用差值（不是百分比变化）
    changes['profit_rate'] = round(current_metrics.get('profit_rate', 0) - prev_metrics.get('profit_rate', 0), 2)
    
    return {
        "success": True,
        "data": {
            "current": current_metrics,
            "previous": prev_metrics,
            "changes": changes,
            "period": {
                "current_start": str(start_date),
                "current_end": str(end_date),
                "previous_start": str(prev_start_date),
                "previous_end": str(prev_end_date),
                "period_days": period_days
            }
        }
    }


def calculate_period_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """计算单个周期的指标"""
    if df.empty:
        return {
            "order_count": 0,
            "total_sales": 0,
            "total_profit": 0,
            "avg_order_value": 0,
            "profit_rate": 0,
            "active_products": 0
        }
    
    order_agg = calculate_order_metrics(df)
    
    order_count = len(order_agg)
    total_sales = order_agg['实收价格'].sum() if '实收价格' in order_agg.columns else 0
    total_profit = order_agg['订单实际利润'].sum() if '订单实际利润' in order_agg.columns else 0
    avg_order_value = total_sales / order_count if order_count > 0 else 0
    profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
    
    # 动销商品数
    sales_field = '月售' if '月售' in df.columns else '销量'
    if '商品名称' in df.columns and sales_field in df.columns:
        active_products = df[df[sales_field] > 0]['商品名称'].nunique()
    else:
        active_products = df['商品名称'].nunique() if '商品名称' in df.columns else 0
    
    return {
        "order_count": int(order_count),
        "total_sales": round(float(total_sales), 2),
        "total_profit": round(float(total_profit), 2),
        "avg_order_value": round(float(avg_order_value), 2),
        "profit_rate": round(float(profit_rate), 2),
        "active_products": int(active_products)
    }


@router.get("/channel-comparison")
async def get_channel_comparison(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    获取渠道环比对比数据（与老版本完全一致）
    
    每个渠道包含:
    - 订单数 + 环比
    - 销售额 + 环比
    - 利润额 + 环比
    - 客单价 + 环比
    - 利润率 + 环比
    
    注意：排除咖啡渠道（美团咖啡店、饿了么咖啡店）
    
    日期逻辑：
    - 如果传了日期范围，使用传入的日期范围
    - 如果没传日期范围，使用数据的完整日期范围
    - 环比计算：当前周期 vs 上一个相同长度的周期
    """
    # 按门店加载数据（利用缓存）
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": []}
    
    if '日期' not in df.columns or '渠道' not in df.columns:
        return {"success": True, "data": []}
    
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    
    if df.empty:
        return {"success": True, "data": []}
    
    # 排除咖啡渠道（与老版本一致）
    CHANNELS_TO_REMOVE = ['美团咖啡店', '饿了么咖啡店']
    df = df[~df['渠道'].isin(CHANNELS_TO_REMOVE)]
    
    if df.empty:
        return {"success": True, "data": []}
    
    # 确定日期范围
    min_date = df['日期'].min()
    max_date = df['日期'].max()
    if pd.isna(max_date) or pd.isna(min_date):
        return {"success": True, "data": []}
    
    # 判断是否使用全部数据（没有传日期参数）
    use_full_data = (start_date is None and end_date is None)
    
    # 如果没有传日期参数，使用数据的完整日期范围
    if start_date is None and end_date is None:
        start_date = min_date.date()
        end_date = max_date.date()
    elif start_date is None:
        start_date = min_date.date()
    elif end_date is None:
        end_date = max_date.date()
    
    period_days = (end_date - start_date).days + 1
    if period_days <= 0:
        period_days = 1
    
    # 计算上一周期（用于环比）
    prev_end_date = start_date - timedelta(days=1)
    prev_start_date = prev_end_date - timedelta(days=period_days - 1)
    
    # 当前周期数据
    current_df = df[(df['日期'].dt.date >= start_date) & (df['日期'].dt.date <= end_date)]
    # 上一周期数据（用于环比）
    prev_df = df[(df['日期'].dt.date >= prev_start_date) & (df['日期'].dt.date <= prev_end_date)]
    
    # 如果使用全部数据或上一周期没有数据，则不计算环比
    has_prev_data = len(prev_df) > 0 and not use_full_data
    
    # 获取当前周期的所有渠道
    channels = current_df['渠道'].dropna().unique().tolist()
    
    result = []
    for channel in channels:
        # 当前周期渠道数据
        curr_ch = current_df[current_df['渠道'] == channel]
        curr_metrics = calculate_channel_metrics(curr_ch)
        
        # 如果有上一周期数据，计算环比
        if has_prev_data:
            # 上一周期渠道数据
            prev_ch = prev_df[prev_df['渠道'] == channel]
            prev_metrics = calculate_channel_metrics(prev_ch)
            
            # 计算环比
            changes = {}
            for key in ['order_count', 'amount', 'profit', 'avg_value']:
                curr_val = curr_metrics.get(key, 0)
                prev_val = prev_metrics.get(key, 0)
                if prev_val > 0:
                    changes[key] = round((curr_val - prev_val) / prev_val * 100, 2)
                elif curr_val > 0:
                    changes[key] = 100.0
                else:
                    changes[key] = 0.0
            
            # 利润率用差值
            changes['profit_rate'] = round(curr_metrics.get('profit_rate', 0) - prev_metrics.get('profit_rate', 0), 2)
        else:
            # 没有上一周期数据，环比显示为null
            prev_metrics = {"order_count": 0, "amount": 0, "profit": 0, "avg_value": 0, "profit_rate": 0}
            changes = {"order_count": None, "amount": None, "profit": None, "avg_value": None, "profit_rate": None}
        
        # 评级（基于当前数据）
        rating = get_channel_rating(curr_metrics, changes if has_prev_data else {})
        
        result.append({
            "channel": channel,
            "current": curr_metrics,
            "previous": prev_metrics if has_prev_data else None,
            "changes": changes,
            "rating": rating
        })
    
    # 按订单数排序
    result.sort(key=lambda x: x['current'].get('order_count', 0), reverse=True)
    
    return {"success": True, "data": result}


def calculate_channel_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    计算单个渠道的完整指标（包含成本结构）
    
    与老版本Dash完全一致的指标:
    - 基础指标: 订单数、销售额、利润、客单价、利润率
    - 成本结构: 商品成本、耗材成本、商品减免、活动补贴、配送成本、平台服务费
    - 单均经济: 单均利润、单均营销、单均配送
    """
    if df.empty:
        return {
            "order_count": 0,
            "amount": 0,
            "profit": 0,
            "avg_value": 0,
            "profit_rate": 0,
            # 成本结构
            "product_cost": 0,
            "product_cost_rate": 0,
            "consumable_cost": 0,
            "consumable_cost_rate": 0,
            "product_discount": 0,
            "product_discount_rate": 0,
            "activity_subsidy": 0,
            "activity_subsidy_rate": 0,
            "delivery_cost": 0,
            "delivery_cost_rate": 0,
            "platform_fee": 0,
            "platform_fee_rate": 0,
            "total_cost_rate": 0,
            # 单均经济
            "avg_profit_per_order": 0,
            "avg_marketing_per_order": 0,
            "avg_delivery_per_order": 0,
        }
    
    order_agg = calculate_order_metrics(df)
    
    order_count = len(order_agg)
    amount = order_agg['实收价格'].sum() if '实收价格' in order_agg.columns else 0
    profit = order_agg['订单实际利润'].sum() if '订单实际利润' in order_agg.columns else 0
    avg_value = amount / order_count if order_count > 0 else 0
    profit_rate = (profit / amount * 100) if amount > 0 else 0
    
    # 成本结构计算
    # 商品成本（从原始df计算，因为是商品级字段）
    product_cost = 0
    if '商品采购成本' in df.columns:
        product_cost = df['商品采购成本'].sum()
    
    # 耗材成本（一级分类为"耗材"的商品成本）
    consumable_cost = 0
    if '一级分类名' in df.columns and '商品采购成本' in df.columns:
        consumable_mask = df['一级分类名'] == '耗材'
        consumable_cost = df.loc[consumable_mask, '商品采购成本'].sum()
        # 从商品成本中扣除耗材成本
        product_cost = product_cost - consumable_cost
    
    # 商品减免金额（订单级字段，从order_agg计算）
    product_discount = 0
    if '商品减免金额' in order_agg.columns:
        product_discount = order_agg['商品减免金额'].sum()
    
    # 营销成本（7个营销字段，对齐Dash版本，剔除配送费减免金额）
    # 配送费减免金额属于配送成本，不属于营销成本
    marketing_cost = 0
    marketing_fields = ['满减金额', '商品减免金额', '商家代金券', 
                       '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
    
    # 调试：打印各字段的值
    print(f"\n[DEBUG] 营销成本计算 - 订单数: {order_count}")
    for field in marketing_fields:
        if field in order_agg.columns:
            field_sum = order_agg[field].fillna(0).sum()
            marketing_cost += field_sum
            print(f"[DEBUG]   {field}: ¥{field_sum:.2f}")
        else:
            print(f"[DEBUG]   {field}: 字段不存在")
    print(f"[DEBUG] 营销成本总计: ¥{marketing_cost:.2f}")
    
    # 活动补贴 = 营销成本 - 商品减免
    activity_subsidy = max(0, marketing_cost - product_discount)
    
    # 配送净成本 = 物流配送费 - 用户支付配送费 + 配送费减免金额
    delivery_cost = 0
    if '物流配送费' in order_agg.columns:
        delivery_cost = order_agg['物流配送费'].sum()
    if '用户支付配送费' in order_agg.columns:
        delivery_cost -= order_agg['用户支付配送费'].sum()
    if '配送费减免金额' in order_agg.columns:
        delivery_cost += order_agg['配送费减免金额'].sum()
    
    # 平台服务费
    platform_fee = 0
    if '平台服务费' in order_agg.columns:
        platform_fee = order_agg['平台服务费'].sum()
    
    # 计算成本率
    product_cost_rate = (product_cost / amount * 100) if amount > 0 else 0
    consumable_cost_rate = (consumable_cost / amount * 100) if amount > 0 else 0
    product_discount_rate = (product_discount / amount * 100) if amount > 0 else 0
    activity_subsidy_rate = (activity_subsidy / amount * 100) if amount > 0 else 0
    delivery_cost_rate = (delivery_cost / amount * 100) if amount > 0 else 0
    platform_fee_rate = (platform_fee / amount * 100) if amount > 0 else 0
    
    # 总成本率
    total_cost_rate = product_cost_rate + consumable_cost_rate + product_discount_rate + activity_subsidy_rate + delivery_cost_rate + platform_fee_rate
    
    # 单均经济
    avg_profit_per_order = profit / order_count if order_count > 0 else 0
    avg_marketing_per_order = marketing_cost / order_count if order_count > 0 else 0
    avg_delivery_per_order = delivery_cost / order_count if order_count > 0 else 0
    
    return {
        "order_count": int(order_count),
        "amount": round(float(amount), 2),
        "profit": round(float(profit), 2),
        "avg_value": round(float(avg_value), 2),
        "profit_rate": round(float(profit_rate), 2),
        # 成本结构
        "product_cost": round(float(product_cost), 2),
        "product_cost_rate": round(float(product_cost_rate), 2),
        "consumable_cost": round(float(consumable_cost), 2),
        "consumable_cost_rate": round(float(consumable_cost_rate), 2),
        "product_discount": round(float(product_discount), 2),
        "product_discount_rate": round(float(product_discount_rate), 2),
        "activity_subsidy": round(float(activity_subsidy), 2),
        "activity_subsidy_rate": round(float(activity_subsidy_rate), 2),
        "delivery_cost": round(float(delivery_cost), 2),
        "delivery_cost_rate": round(float(delivery_cost_rate), 2),
        "platform_fee": round(float(platform_fee), 2),
        "platform_fee_rate": round(float(platform_fee_rate), 2),
        "total_cost_rate": round(float(total_cost_rate), 2),
        # 单均经济
        "avg_profit_per_order": round(float(avg_profit_per_order), 2),
        "avg_marketing_per_order": round(float(avg_marketing_per_order), 2),
        "avg_delivery_per_order": round(float(avg_delivery_per_order), 2),
    }


def get_channel_rating(metrics: Dict, changes: Dict) -> str:
    """根据指标和环比获取渠道评级"""
    profit_rate = metrics.get('profit_rate', 0)
    profit_change = changes.get('profit', 0)
    amount_change = changes.get('amount', 0)
    
    # 优秀: 利润率>15% 且 (销售额环比>0 或 利润环比>0)
    if profit_rate > 15 and (amount_change > 0 or profit_change > 0):
        return "优秀"
    # 良好: 利润率>10% 且 销售额环比>-10%
    elif profit_rate > 10 and amount_change > -10:
        return "良好"
    # 需改进
    else:
        return "需改进"


# [Phase 2] Migrated to orders_analysis.py


# ==================== 导出功能 ====================

from fastapi.responses import StreamingResponse
import io

@router.get("/export")
async def export_orders(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
):
    """
    导出订单数据到Excel
    
    与老版本导出功能一致，包含:
    - 订单ID
    - 日期
    - 门店名称
    - 渠道
    - 实收价格
    - 订单实际利润
    - 利润率
    """
    # 按门店加载数据（利用缓存）
    df = get_order_data(store_name)
    
    if df.empty:
        # 返回空Excel
        output = io.BytesIO()
        pd.DataFrame().to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=订单数据_空.xlsx"}
        )
    
    # 日期筛选
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        if start_date:
            df = df[df['日期'].dt.date >= start_date]
        if end_date:
            df = df[df['日期'].dt.date <= end_date]
    
    if df.empty:
        output = io.BytesIO()
        pd.DataFrame().to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=订单数据_空.xlsx"}
        )
    
    # 计算订单级指标
    order_agg = calculate_order_metrics(df)
    
    # 计算利润率
    order_agg['利润率'] = order_agg.apply(
        lambda r: round(r['订单实际利润'] / r['实收价格'] * 100, 2) if r.get('实收价格', 0) > 0 else 0, 
        axis=1
    )
    
    # 选择导出字段
    export_cols = ['订单ID', '日期', '门店名称', '渠道', '实收价格', '订单实际利润', '利润率']
    available_cols = [c for c in export_cols if c in order_agg.columns]
    export_df = order_agg[available_cols].copy()
    
    # 格式化日期
    if '日期' in export_df.columns:
        export_df['日期'] = pd.to_datetime(export_df['日期']).dt.strftime('%Y-%m-%d')
    
    # 重命名列（更友好的显示名）
    column_rename = {
        '订单ID': '订单编号',
        '日期': '订单日期',
        '门店名称': '门店',
        '渠道': '销售渠道',
        '实收价格': '订单金额(元)',
        '订单实际利润': '利润(元)',
        '利润率': '利润率(%)'
    }
    export_df = export_df.rename(columns={k: v for k, v in column_rename.items() if k in export_df.columns})
    
    # 生成Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='订单数据')
        
        # 调整列宽
        worksheet = writer.sheets['订单数据']
        for idx, col in enumerate(export_df.columns):
            max_length = max(
                export_df[col].astype(str).map(len).max() if len(export_df) > 0 else 0,
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 30)
    
    output.seek(0)
    
    # 生成文件名
    filename = f"订单经营分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )



@router.get("/date-range")
async def get_date_range(
    store_name: Optional[str] = Query(None, description="门店名称筛选")
) -> Dict[str, Any]:
    """
    获取门店数据的日期范围
    
    用于前端日历选择器限制可选日期范围
    """
    # 按门店加载数据（利用缓存）
    df = get_order_data(store_name)
    if df.empty:
        return {
            "success": True,
            "data": {
                "min_date": None,
                "max_date": None,
                "total_days": 0
            }
        }
    
    if '日期' not in df.columns:
        return {
            "success": True,
            "data": {
                "min_date": None,
                "max_date": None,
                "total_days": 0
            }
        }
    
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    
    if df.empty:
        return {
            "success": True,
            "data": {
                "min_date": None,
                "max_date": None,
                "total_days": 0
            }
        }
    
    min_date = df['日期'].min()
    max_date = df['日期'].max()
    total_days = (max_date - min_date).days + 1
    
    return {
        "success": True,
        "data": {
            "min_date": min_date.strftime('%Y-%m-%d'),
            "max_date": max_date.strftime('%Y-%m-%d'),
            "total_days": total_days
        }
    }


# ==================== 图表联动API（销售趋势下钻） ====================

# [Phase 2] Migrated to orders_analysis.py


# [Phase 2] Migrated to orders_analysis.py


# ==================== 分时利润分析 API ====================

# [Phase 3] Migrated to orders_delivery.py


# [Phase 3] Migrated to orders_delivery.py


# ==================== 成本结构分析API（资金流向全景桑基图专用） ====================

# [Phase 3] Migrated to orders_delivery.py
# [Phase 3] Migrated to orders_delivery.py
# [Phase 3] Migrated to orders_delivery.py


# [Phase 3] Migrated to orders_delivery.py


# [Phase 3] Migrated to orders_delivery.py


# ==================== 配送溢价雷达数据 API ====================

# [Phase 3] Migrated to orders_delivery.py

