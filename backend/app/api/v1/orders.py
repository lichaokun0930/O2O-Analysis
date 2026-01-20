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
    获取数据版本号（基于数据库最后更新时间）
    
    版本号 = 门店最新订单的updated_at时间戳
    当数据有更新时，版本号会变化，触发缓存失效
    """
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
    use_aggregation: bool = Query(True, description="是否使用预聚合表（性能优化）")
) -> Dict[str, Any]:
    """
    获取订单数据概览（六大核心卡片）
    
    与老版本Tab1完全一致的指标:
    - 📦 订单总数
    - 💰 商品实收额
    - 💎 总利润
    - 🛒 平均客单价
    - 📈 总利润率
    - 🏷️ 动销商品数
    
    优化：优先使用预聚合表，查询时间从~500ms降到~2ms
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
            if result:
                # 检查预聚合表是否有GMV数据
                if result.get("gmv", 0) > 0:
                    # 预聚合表有GMV数据，直接使用
                    print(f"✅ [预聚合表+GMV] overview查询耗时: {(time.time()-query_start)*1000:.1f}ms")
                    return {"success": True, "data": result}
                else:
                    # 预聚合表没有GMV数据，需要从原始数据计算
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
    use_aggregation: bool = Query(True, description="是否使用预聚合表（性能优化）")
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
    
    优化：优先使用预聚合表，查询时间从~200ms降到~5ms
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


@router.get("/profit-distribution")
async def get_profit_distribution(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    获取利润区间分布
    
    与老版本的利润区间分布图一致
    """
    # 按门店加载数据（利用缓存）
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": {"labels": [], "counts": [], "colors": []}}
    
    # 日期筛选
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        if start_date:
            df = df[df['日期'].dt.date >= start_date]
        if end_date:
            df = df[df['日期'].dt.date <= end_date]
    
    if df.empty:
        return {"success": True, "data": {"labels": [], "counts": [], "colors": []}}
    
    # 计算订单级指标
    order_agg = calculate_order_metrics(df)
    
    if order_agg.empty or '订单实际利润' not in order_agg.columns:
        return {"success": True, "data": {"labels": [], "counts": [], "colors": []}}
    
    profit_values = order_agg['订单实际利润'].values
    
    # 定义利润区间
    bins = [-np.inf, -100, -50, -20, 0, 20, 50, 100, np.inf]
    labels = ['重度亏损(<-100)', '中度亏损(-100~-50)', '轻度亏损(-50~-20)', 
              '微亏损(-20~0)', '微盈利(0~20)', '良好盈利(20~50)', 
              '优秀盈利(50~100)', '超级盈利(>100)']
    
    # 统计各区间订单数
    counts, _ = np.histogram(profit_values, bins=bins)
    
    # 颜色（亏损红色系，盈利绿色系）
    colors = ['#C0392B', '#E74C3C', '#FF6B6B', '#FFA07A',
              '#98FB98', '#2ECC71', '#27AE60', '#229954']
    
    return {
        "success": True,
        "data": {
            "labels": labels,
            "counts": [int(c) for c in counts.tolist()],
            "colors": colors,
            "total_orders": len(profit_values)
        }
    }


@router.get("/price-distribution")
async def get_price_distribution(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    获取客单价区间分布（与老版本完全一致）
    
    8个标准价格区间:
    - ¥0-10, ¥10-20, ¥20-30, ¥30-40, ¥40-50, ¥50-100, ¥100-200, ¥200+
    
    4大业务价格组:
    - 流量区 (< ¥15): 引流低价商品
    - 主流区 (¥15-30): 日常高频商品
    - 利润区 (¥30-50): 毛利贡献主力
    - 高价区 (≥ ¥50): 高端/大单商品
    """
    # 按门店加载数据（利用缓存）
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": {"price_ranges": [], "business_zones": {}, "avg_basket_depth": 0}}
    
    # 日期筛选
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        if start_date:
            df = df[df['日期'].dt.date >= start_date]
        if end_date:
            df = df[df['日期'].dt.date <= end_date]
    
    if df.empty:
        return {"success": True, "data": {"price_ranges": [], "business_zones": {}, "avg_basket_depth": 0}}
    
    # 计算订单级指标
    order_agg = calculate_order_metrics(df)
    
    if order_agg.empty or '实收价格' not in order_agg.columns:
        return {"success": True, "data": {"price_ranges": [], "business_zones": {}, "avg_basket_depth": 0}}
    
    prices = order_agg['实收价格'].values
    total_orders = len(prices)
    
    # 8个标准价格区间
    price_ranges = [
        (0, 10, '¥0-10'),
        (10, 20, '¥10-20'),
        (20, 30, '¥20-30'),
        (30, 40, '¥30-40'),
        (40, 50, '¥40-50'),
        (50, 100, '¥50-100'),
        (100, 200, '¥100-200'),
        (200, float('inf'), '¥200+')
    ]
    
    range_data = []
    for low, high, label in price_ranges:
        if high == float('inf'):
            count = int(np.sum(prices >= low))
        else:
            count = int(np.sum((prices >= low) & (prices < high)))
        
        ratio = round(count / total_orders * 100, 2) if total_orders > 0 else 0
        range_data.append({
            "label": label,
            "count": count,
            "ratio": ratio,
            "color": get_price_range_color(low)
        })
    
    # 4大业务价格组
    flow_zone = int(np.sum(prices < 15))  # 流量区
    main_zone = int(np.sum((prices >= 15) & (prices < 30)))  # 主流区
    profit_zone = int(np.sum((prices >= 30) & (prices < 50)))  # 利润区
    high_zone = int(np.sum(prices >= 50))  # 高价区
    
    business_zones = {
        "flow_zone": {"label": "流量区(<¥15)", "count": flow_zone, "ratio": round(flow_zone / total_orders * 100, 2) if total_orders > 0 else 0},
        "main_zone": {"label": "主流区(¥15-30)", "count": main_zone, "ratio": round(main_zone / total_orders * 100, 2) if total_orders > 0 else 0},
        "profit_zone": {"label": "利润区(¥30-50)", "count": profit_zone, "ratio": round(profit_zone / total_orders * 100, 2) if total_orders > 0 else 0},
        "high_zone": {"label": "高价区(≥¥50)", "count": high_zone, "ratio": round(high_zone / total_orders * 100, 2) if total_orders > 0 else 0},
    }
    
    # 购物篮深度（平均SKU数）
    if '订单ID' in df.columns:
        basket_depth = df.groupby('订单ID').size().mean()
    else:
        basket_depth = 1.0
    
    return {
        "success": True,
        "data": {
            "price_ranges": range_data,
            "business_zones": business_zones,
            "avg_basket_depth": round(float(basket_depth), 2),
            "total_orders": total_orders,
            "avg_order_value": round(float(np.mean(prices)), 2) if len(prices) > 0 else 0
        }
    }


def get_price_range_color(price: float) -> str:
    """根据价格返回颜色"""
    if price < 15:
        return "#3498DB"  # 蓝色 - 流量区
    elif price < 30:
        return "#27AE60"  # 绿色 - 主流区
    elif price < 50:
        return "#F39C12"  # 橙色 - 利润区
    else:
        return "#9B59B6"  # 紫色 - 高价区


@router.get("/category-trend")
async def get_category_trend(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    channel: Optional[str] = Query(None, description="渠道筛选"),
    weeks: int = Query(4, ge=1, le=12, description="统计周数")
) -> Dict[str, Any]:
    """
    获取一级分类销售趋势（与老版本完全一致）
    
    返回各一级分类的周销售趋势数据
    """
    # 按门店加载数据（利用缓存）
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": {"categories": [], "weeks": [], "series": []}}
    
    # 渠道筛选
    if channel and '渠道' in df.columns:
        df = df[df['渠道'] == channel]
    
    if '日期' not in df.columns or '一级分类名' not in df.columns:
        return {"success": True, "data": {"categories": [], "weeks": [], "series": []}}
    
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    
    if df.empty:
        return {"success": True, "data": {"categories": [], "weeks": [], "series": []}}
    
    # 筛选最近N周
    max_date = df['日期'].max()
    if pd.isna(max_date):
        return {"success": True, "data": {"categories": [], "weeks": [], "series": []}}
    
    min_date = max_date - timedelta(weeks=weeks)
    df = df[df['日期'] >= min_date]
    
    if df.empty:
        return {"success": True, "data": {"categories": [], "weeks": [], "series": []}}
    
    # 添加周标识
    df['周'] = df['日期'].dt.to_period('W').apply(lambda x: x.start_time.strftime('%Y-%m-%d'))
    
    # 按一级分类和周聚合
    sales_field = '实收价格' if '实收价格' in df.columns else '商品实售价'
    if sales_field not in df.columns:
        return {"success": True, "data": {"categories": [], "weeks": [], "series": []}}
    
    category_weekly = df.groupby(['一级分类名', '周'])[sales_field].sum().reset_index()
    category_weekly.columns = ['category', 'week', 'sales']
    
    # 获取所有分类和周
    categories = sorted(category_weekly['category'].unique().tolist())
    weeks_list = sorted(category_weekly['week'].unique().tolist())
    
    # 构建系列数据
    series = []
    colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']
    
    for i, cat in enumerate(categories):
        cat_data = category_weekly[category_weekly['category'] == cat]
        values = []
        for week in weeks_list:
            week_val = cat_data[cat_data['week'] == week]['sales'].values
            values.append(round(float(week_val[0]), 2) if len(week_val) > 0 else 0)
        
        series.append({
            "name": cat,
            "data": values,
            "color": colors[i % len(colors)]
        })
    
    return {
        "success": True,
        "data": {
            "categories": categories,
            "weeks": weeks_list,
            "series": series
        }
    }


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


@router.get("/anomaly-detection")
async def get_anomaly_detection(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    获取异常诊断数据（与老版本完全一致）
    
    三类异常:
    1. 低利润率订单（利润率<10%）
    2. 高配送成本订单（配送成本占比>30%）
    3. 负利润订单（订单实际利润<0）
    """
    # 按门店加载数据（利用缓存）
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": {"low_profit": [], "high_delivery": [], "negative_profit": [], "summary": {}}}
    
    # 日期筛选
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        if start_date:
            df = df[df['日期'].dt.date >= start_date]
        if end_date:
            df = df[df['日期'].dt.date <= end_date]
    
    if df.empty:
        return {"success": True, "data": {"low_profit": [], "high_delivery": [], "negative_profit": [], "summary": {}}}
    
    order_agg = calculate_order_metrics(df)
    
    if order_agg.empty:
        return {"success": True, "data": {"low_profit": [], "high_delivery": [], "negative_profit": [], "summary": {}}}
    
    # 计算利润率
    order_agg['利润率'] = order_agg.apply(
        lambda r: r['订单实际利润'] / r['实收价格'] * 100 if r.get('实收价格', 0) > 0 else 0, axis=1
    )
    
    # 计算配送成本占比
    if '物流配送费' in order_agg.columns and '用户支付配送费' in order_agg.columns:
        order_agg['配送净成本'] = order_agg['物流配送费'] - order_agg.get('用户支付配送费', 0) + order_agg.get('配送费减免金额', 0)
        order_agg['配送成本占比'] = order_agg.apply(
            lambda r: r['配送净成本'] / r['实收价格'] * 100 if r.get('实收价格', 0) > 0 else 0, axis=1
        )
    else:
        order_agg['配送成本占比'] = 0
    
    total_orders = len(order_agg)
    
    # 1. 低利润率订单（利润率<10%）
    low_profit_df = order_agg[order_agg['利润率'] < 10].head(10)
    low_profit_list = []
    for _, row in low_profit_df.iterrows():
        low_profit_list.append({
            "order_id": row.get('订单ID', ''),
            "amount": round(float(row.get('实收价格', 0)), 2),
            "profit": round(float(row.get('订单实际利润', 0)), 2),
            "profit_rate": round(float(row.get('利润率', 0)), 2),
            "channel": row.get('渠道', ''),
        })
    
    # 2. 高配送成本订单（配送成本占比>30%）
    high_delivery_df = order_agg[order_agg['配送成本占比'] > 30].head(10)
    high_delivery_list = []
    for _, row in high_delivery_df.iterrows():
        high_delivery_list.append({
            "order_id": row.get('订单ID', ''),
            "amount": round(float(row.get('实收价格', 0)), 2),
            "delivery_cost": round(float(row.get('配送净成本', 0)), 2),
            "delivery_ratio": round(float(row.get('配送成本占比', 0)), 2),
            "channel": row.get('渠道', ''),
        })
    
    # 3. 负利润订单
    negative_profit_df = order_agg[order_agg['订单实际利润'] < 0].head(10)
    negative_profit_list = []
    for _, row in negative_profit_df.iterrows():
        negative_profit_list.append({
            "order_id": row.get('订单ID', ''),
            "amount": round(float(row.get('实收价格', 0)), 2),
            "profit": round(float(row.get('订单实际利润', 0)), 2),
            "loss": round(float(-row.get('订单实际利润', 0)), 2),
            "channel": row.get('渠道', ''),
        })
    
    # 汇总统计
    low_profit_count = len(order_agg[order_agg['利润率'] < 10])
    high_delivery_count = len(order_agg[order_agg['配送成本占比'] > 30])
    negative_profit_count = len(order_agg[order_agg['订单实际利润'] < 0])
    
    total_negative_loss = order_agg[order_agg['订单实际利润'] < 0]['订单实际利润'].sum()
    
    return {
        "success": True,
        "data": {
            "low_profit": low_profit_list,
            "high_delivery": high_delivery_list,
            "negative_profit": negative_profit_list,
            "summary": {
                "total_orders": total_orders,
                "low_profit_count": int(low_profit_count),
                "low_profit_ratio": round(low_profit_count / total_orders * 100, 2) if total_orders > 0 else 0,
                "high_delivery_count": int(high_delivery_count),
                "high_delivery_ratio": round(high_delivery_count / total_orders * 100, 2) if total_orders > 0 else 0,
                "negative_profit_count": int(negative_profit_count),
                "negative_profit_ratio": round(negative_profit_count / total_orders * 100, 2) if total_orders > 0 else 0,
                "total_loss": round(float(abs(total_negative_loss)), 2)
            }
        }
    }


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

@router.get("/category-hourly-trend")
async def get_category_hourly_trend(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    date: Optional[str] = Query(None, description="指定日期(YYYY-MM-DD或MM-DD格式)"),
    start_date: Optional[str] = Query(None, description="日期范围开始(YYYY-MM-DD格式)"),
    end_date: Optional[str] = Query(None, description="日期范围结束(YYYY-MM-DD格式)"),
    channel: Optional[str] = Query(None, description="渠道筛选")
) -> Dict[str, Any]:
    """
    获取分时段品类走势数据（销售趋势图表联动）
    
    - 如果指定单日期(date)：返回该日期的24小时分时段品类销售数据
    - 如果指定日期范围(start_date, end_date)：返回范围内每日品类销售数据
    - 如果不指定日期：返回近7天的每日品类销售数据
    
    与Dash版本一致的计算逻辑：
    - 🔴 剔除耗材数据（一级分类名='耗材'，如购物袋）
    - 按一级分类聚合
    - 使用实收价格作为销售额
    - 按销售额降序排序（销售额最高的分类排在前面）
    - 过滤掉空分类名
    """
    # 按门店加载数据
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": {"labels": [], "categories": [], "series": []}}
    
    # 🔴 关键业务规则：剔除耗材数据（购物袋等）
    # 与Dash版本保持一致：分类分析不展示耗材
    if '一级分类名' in df.columns:
        original_count = len(df)
        df = df[df['一级分类名'] != '耗材'].copy()
        filtered_count = original_count - len(df)
        if filtered_count > 0:
            print(f"[category-hourly-trend] 剔除耗材数据: {filtered_count} 条")
    
    # 渠道筛选
    if channel and channel != 'all' and '渠道' in df.columns:
        df = df[df['渠道'] == channel]
    
    if '日期' not in df.columns or '一级分类名' not in df.columns:
        return {"success": True, "data": {"labels": [], "categories": [], "series": []}}
    
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    
    # 🆕 处理空分类名：填充为"未分类"而不是过滤掉
    df['一级分类名'] = df['一级分类名'].fillna('未分类')
    df.loc[df['一级分类名'].astype(str).isin(['', 'nan', 'None']), '一级分类名'] = '未分类'
    
    if df.empty:
        return {"success": True, "data": {"labels": [], "categories": [], "series": []}}
    
    # 销售额字段
    sales_field = '实收价格' if '实收价格' in df.columns else '商品实售价'
    if sales_field not in df.columns:
        return {"success": True, "data": {"labels": [], "categories": [], "series": []}}
    
    # 🆕 解析日期参数：支持单日期或日期范围
    target_date = None
    range_start = None
    range_end = None
    
    # 优先处理日期范围
    if start_date and end_date:
        try:
            range_start = pd.to_datetime(start_date)
            range_end = pd.to_datetime(end_date)
        except:
            range_start = None
            range_end = None
    elif date:
        try:
            # 支持 MM-DD 格式（从数据中推断年份）
            if len(date) == 5 and '-' in date:
                max_date = df['日期'].max()
                year = max_date.year
                target_date = pd.to_datetime(f"{year}-{date}")
            else:
                target_date = pd.to_datetime(date)
        except:
            target_date = None
    
    # 🆕 日期范围模式：返回范围内每日品类销售数据
    # 🔴 特殊处理：当 start_date === end_date 时，视为单日期模式，返回小时数据
    if range_start and range_end:
        # 如果是同一天，转换为单日期模式
        if range_start.date() == range_end.date():
            target_date = range_start
            range_start = None
            range_end = None
            # 继续执行下面的单日期逻辑
        else:
            range_df = df[(df['日期'].dt.date >= range_start.date()) & (df['日期'].dt.date <= range_end.date())]
            if range_df.empty:
                return {"success": True, "data": {"labels": [], "categories": [], "series": [], "mode": "daily"}}
            
            # 按日期和分类聚合
            daily_category = range_df.groupby([range_df['日期'].dt.strftime('%m-%d'), '一级分类名'])[sales_field].sum().reset_index()
            daily_category.columns = ['date', 'category', 'revenue']
            
            # 按总销售额降序排序分类
            category_totals = daily_category.groupby('category')['revenue'].sum().sort_values(ascending=False)
            categories = category_totals.index.tolist()
            
            # 生成完整的日期序列
            all_dates = []
            current_date = range_start
            while current_date <= range_end:
                all_dates.append(current_date.strftime('%m-%d'))
                current_date += timedelta(days=1)
            
            # 构建系列数据
            series = []
            colors = ['#8b5cf6', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1']
            
            for i, cat in enumerate(categories):
                cat_data = daily_category[daily_category['category'] == cat]
                values = []
                for d in all_dates:
                    day_val = cat_data[cat_data['date'] == d]['revenue'].values
                    values.append(round(float(day_val[0]), 2) if len(day_val) > 0 else 0)
                
                series.append({
                    "name": cat,
                    "data": values,
                    "color": colors[i % len(colors)]
                })
            
            return {
                "success": True,
                "data": {
                    "labels": all_dates,
                    "categories": categories,
                    "series": series,
                    "mode": "daily",
                    "start_date": range_start.strftime('%Y-%m-%d'),
                    "end_date": range_end.strftime('%Y-%m-%d')
                }
            }
    
    if target_date:
        # 指定日期：返回24小时分时段数据
        day_df = df[df['日期'].dt.date == target_date.date()]
        if day_df.empty:
            return {"success": True, "data": {"labels": [], "categories": [], "series": [], "mode": "hourly"}}
        
        # 提取小时
        if '下单时间' in day_df.columns:
            day_df = day_df.copy()
            day_df['小时'] = pd.to_datetime(day_df['下单时间'], errors='coerce').dt.hour
        else:
            day_df = day_df.copy()
            day_df['小时'] = day_df['日期'].dt.hour
        
        # 按小时和分类聚合
        hourly_category = day_df.groupby(['小时', '一级分类名'])[sales_field].sum().reset_index()
        hourly_category.columns = ['hour', 'category', 'revenue']
        
        # 🆕 按总销售额降序排序分类（返回所有分类，前端做筛选）
        category_totals = hourly_category.groupby('category')['revenue'].sum().sort_values(ascending=False)
        categories = category_totals.index.tolist()  # 返回所有分类
        
        hours = list(range(0, 24, 2))  # 每2小时一个点
        labels = [f"{h}:00" for h in hours]
        
        # 构建系列数据（所有分类）
        series = []
        colors = ['#8b5cf6', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1']
        
        for i, cat in enumerate(categories):
            cat_data = hourly_category[hourly_category['category'] == cat]
            values = []
            for h in hours:
                # 聚合2小时内的数据
                hour_val = cat_data[(cat_data['hour'] >= h) & (cat_data['hour'] < h + 2)]['revenue'].sum()
                values.append(round(float(hour_val), 2))
            
            series.append({
                "name": cat,
                "data": values,
                "color": colors[i % len(colors)]
            })
        
        return {
            "success": True,
            "data": {
                "labels": labels,
                "categories": categories,
                "series": series,
                "mode": "hourly",
                "date": target_date.strftime('%Y-%m-%d')
            }
        }
    else:
        # 不指定日期：返回近7天每日数据
        max_date = df['日期'].max()
        # 🆕 确保使用日期部分，去掉时间部分，避免边界问题
        max_date_only = pd.Timestamp(max_date.date())
        min_date_only = max_date_only - timedelta(days=6)
        
        # 🆕 使用 .dt.date 进行日期比较，避免时间部分影响
        week_df = df[(df['日期'].dt.date >= min_date_only.date()) & (df['日期'].dt.date <= max_date_only.date())]
        
        if week_df.empty:
            return {"success": True, "data": {"labels": [], "categories": [], "series": [], "mode": "daily"}}
        
        # 按日期和分类聚合
        daily_category = week_df.groupby([week_df['日期'].dt.strftime('%m-%d'), '一级分类名'])[sales_field].sum().reset_index()
        daily_category.columns = ['date', 'category', 'revenue']
        
        # 🆕 按总销售额降序排序分类（返回所有分类，前端做筛选）
        category_totals = daily_category.groupby('category')['revenue'].sum().sort_values(ascending=False)
        categories = category_totals.index.tolist()  # 返回所有分类
        
        # 🆕 生成完整的日期序列（确保每天都有数据点）
        all_dates = []
        current_date = min_date_only
        while current_date <= max_date_only:
            all_dates.append(current_date.strftime('%m-%d'))
            current_date += timedelta(days=1)
        
        # 构建系列数据（所有分类）
        series = []
        colors = ['#8b5cf6', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1']
        
        for i, cat in enumerate(categories):
            cat_data = daily_category[daily_category['category'] == cat]
            values = []
            for d in all_dates:
                day_val = cat_data[cat_data['date'] == d]['revenue'].values
                values.append(round(float(day_val[0]), 2) if len(day_val) > 0 else 0)
            
            series.append({
                "name": cat,
                "data": values,
                "color": colors[i % len(colors)]
            })
        
        return {
            "success": True,
            "data": {
                "labels": all_dates,
                "categories": categories,
                "series": series,
                "mode": "daily"
            }
        }


@router.get("/top-products-by-date")
async def get_top_products_by_date(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    date: Optional[str] = Query(None, description="指定日期(YYYY-MM-DD或MM-DD格式)"),
    start_date: Optional[str] = Query(None, description="日期范围开始(YYYY-MM-DD格式)"),
    end_date: Optional[str] = Query(None, description="日期范围结束(YYYY-MM-DD格式)"),
    channel: Optional[str] = Query(None, description="渠道筛选"),
    sort_by: str = Query("quantity", description="排序维度: quantity/revenue/profit/loss"),
    limit: int = Query(15, ge=5, le=50, description="返回数量")
) -> Dict[str, Any]:
    """
    获取商品销量排行数据（销售趋势图表联动）
    
    支持多维度排序：
    - quantity: 销量榜（按销量降序）
    - revenue: 营收榜（按销售额降序）
    - profit: 毛利榜（按利润额降序，正向）
    - loss: 亏损榜（按利润额升序，负向）
    
    支持单日期或日期范围筛选
    
    与Dash版本一致的计算逻辑：
    - 🔴 剔除耗材数据（一级分类名='耗材'，如购物袋）
    - 利润额：使用Excel原始字段（商品级毛利）
    - 销售额：实收价格 × 销量（或商品实售价）
    - 毛利率：利润额 / 销售额 × 100
    """
    # 按门店加载数据
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": {"products": [], "sort_by": sort_by}}
    
    # 🔴 关键业务规则：剔除耗材数据（购物袋等）
    # 与Dash版本保持一致：商品排行榜不展示耗材
    if '一级分类名' in df.columns:
        original_count = len(df)
        df = df[df['一级分类名'] != '耗材'].copy()
        filtered_count = original_count - len(df)
        if filtered_count > 0:
            print(f"[top-products-by-date] 剔除耗材数据: {filtered_count} 条")
    
    # 渠道筛选
    if channel and channel != 'all' and '渠道' in df.columns:
        df = df[df['渠道'] == channel]
    
    if '日期' not in df.columns or '商品名称' not in df.columns:
        return {"success": True, "data": {"products": [], "sort_by": sort_by}}
    
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    
    if df.empty:
        return {"success": True, "data": {"products": [], "sort_by": sort_by}}
    
    # 🆕 解析日期参数：支持单日期或日期范围
    target_date = None
    range_start = None
    range_end = None
    
    # 优先处理日期范围
    if start_date and end_date:
        try:
            range_start = pd.to_datetime(start_date)
            range_end = pd.to_datetime(end_date)
        except:
            range_start = None
            range_end = None
    elif date:
        try:
            if len(date) == 5 and '-' in date:
                max_date = df['日期'].max()
                year = max_date.year
                target_date = pd.to_datetime(f"{year}-{date}")
            else:
                target_date = pd.to_datetime(date)
        except:
            target_date = None
    
    # 筛选日期
    # 🔴 特殊处理：当 start_date === end_date 时，视为单日期模式
    if range_start and range_end:
        if range_start.date() == range_end.date():
            # 同一天，转换为单日期模式
            target_date = range_start
            range_start = None
            range_end = None
        else:
            df = df[(df['日期'].dt.date >= range_start.date()) & (df['日期'].dt.date <= range_end.date())]
    
    if target_date:
        df = df[df['日期'].dt.date == target_date.date()]
    
    if df.empty:
        return {"success": True, "data": {"products": [], "sort_by": sort_by}}
    
    # 字段映射（与Dash版本一致）
    quantity_field = '月售' if '月售' in df.columns else '销量'
    
    # 🔴 销售额计算：实收价格 × 销量（与Dash版本一致）
    # 实收价格是单价，需要乘以销量得到销售额
    if '实收价格' in df.columns and quantity_field in df.columns:
        df['_销售额'] = df['实收价格'].fillna(0) * df[quantity_field].fillna(1)
        sales_field = '_销售额'
    elif '商品实售价' in df.columns:
        # 商品实售价已经是总价
        sales_field = '商品实售价'
    else:
        sales_field = None
    
    # 按商品聚合（使用店内码优先，避免同名不同规格商品混淆）
    group_key = '店内码' if '店内码' in df.columns else '商品名称'
    
    agg_dict = {}
    
    # 商品名称（如果按店内码聚合）
    if group_key == '店内码':
        agg_dict['name'] = ('商品名称', 'first')
    
    # 销量
    if quantity_field in df.columns:
        agg_dict['quantity'] = (quantity_field, 'sum')
    
    # 销售额
    if sales_field and sales_field in df.columns:
        agg_dict['revenue'] = (sales_field, 'sum')
    
    # 🔴 利润额：直接使用Excel原始字段（商品级毛利，已乘以销量）
    if '利润额' in df.columns:
        agg_dict['profit'] = ('利润额', 'sum')
    
    # 分类
    if '一级分类名' in df.columns:
        agg_dict['category'] = ('一级分类名', 'first')
    
    if not agg_dict:
        return {"success": True, "data": {"products": [], "sort_by": sort_by}}
    
    product_agg = df.groupby(group_key).agg(**agg_dict).reset_index()
    
    # 如果按店内码聚合，重命名列
    if group_key == '店内码':
        product_agg = product_agg.rename(columns={group_key: 'store_code'})
    else:
        product_agg = product_agg.rename(columns={group_key: 'name'})
    
    # 确保有name列
    if 'name' not in product_agg.columns and 'store_code' in product_agg.columns:
        product_agg['name'] = product_agg['store_code']
    
    # 计算毛利率
    if 'profit' in product_agg.columns and 'revenue' in product_agg.columns:
        product_agg['profit_rate'] = (product_agg['profit'] / product_agg['revenue'].replace(0, float('nan')) * 100).round(2)
        product_agg['profit_rate'] = product_agg['profit_rate'].fillna(0)
    else:
        product_agg['profit_rate'] = 0
    
    # 排序
    ascending = False
    actual_sort_by = sort_by
    if sort_by == 'loss':
        actual_sort_by = 'profit'
        ascending = True  # 亏损榜：利润从低到高
    
    sort_field = actual_sort_by if actual_sort_by in product_agg.columns else 'quantity'
    if sort_field not in product_agg.columns:
        sort_field = list(product_agg.columns)[1] if len(product_agg.columns) > 1 else product_agg.columns[0]
    
    product_agg = product_agg.sort_values(sort_field, ascending=ascending).head(limit)
    
    # 构建返回数据
    products = []
    for _, row in product_agg.iterrows():
        product = {
            "name": str(row.get('name', '未知商品')),
            "quantity": int(row.get('quantity', 0)),
            "revenue": round(float(row.get('revenue', 0)), 2),
            "profit": round(float(row.get('profit', 0)), 2),
            "profit_rate": round(float(row.get('profit_rate', 0)), 2),
            "category": str(row.get('category', '未分类')),
            "growth": 0  # 环比增长（暂不计算）
        }
        products.append(product)
    
    return {
        "success": True,
        "data": {
            "products": products,
            "sort_by": sort_by,
            "date": target_date.strftime('%Y-%m-%d') if target_date else None,
            "total_count": len(product_agg)
        }
    }


# ==================== 分时利润分析 API ====================

def identify_peak_periods(hourly_orders: pd.Series) -> List[Dict[str, Any]]:
    """
    智能识别高峰时段
    
    算法：订单量 > 平均值 + 0.5倍标准差
    
    Args:
        hourly_orders: 每小时订单数 Series，index为小时(0-23)
    
    Returns:
        高峰时段列表，每个元素包含 start, end, name
    """
    if hourly_orders.empty or hourly_orders.sum() == 0:
        return []
    
    mean_orders = hourly_orders.mean()
    std_orders = hourly_orders.std()
    
    # 高峰阈值：均值 + 0.5倍标准差
    threshold = mean_orders + 0.5 * std_orders
    
    # 找出高峰小时
    peak_hours = hourly_orders[hourly_orders > threshold].index.tolist()
    
    if not peak_hours:
        return []
    
    # 合并连续时段
    peak_periods = []
    peak_hours = sorted(peak_hours)
    
    start = peak_hours[0]
    end = peak_hours[0]
    
    for hour in peak_hours[1:]:
        if hour == end + 1:
            # 连续，扩展区间
            end = hour
        else:
            # 不连续，保存当前区间，开始新区间
            peak_periods.append((start, end))
            start = hour
            end = hour
    
    # 保存最后一个区间
    peak_periods.append((start, end))
    
    # 命名时段
    result = []
    for start_hour, end_hour in peak_periods:
        # 根据时间范围命名
        if 6 <= start_hour <= 9:
            name = "早高峰"
        elif 11 <= start_hour <= 14:
            name = "午高峰"
        elif 17 <= start_hour <= 20:
            name = "晚高峰"
        elif 20 <= start_hour or start_hour <= 2:
            name = "夜高峰"
        else:
            name = "高峰时段"
        
        result.append({
            "start": f"{start_hour:02d}:00",
            "end": f"{end_hour + 1:02d}:00",  # 结束时间是下一个小时
            "name": name,
            "start_hour": start_hour,
            "end_hour": end_hour
        })
    
    return result


@router.get("/hourly-profit")
async def get_hourly_profit(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    target_date: Optional[str] = Query(None, description="目标日期(YYYY-MM-DD或MM-DD格式)，默认为数据最后一天"),
    start_date: Optional[str] = Query(None, description="开始日期(YYYY-MM-DD格式)"),
    end_date: Optional[str] = Query(None, description="结束日期(YYYY-MM-DD格式)"),
    channel: Optional[str] = Query(None, description="渠道筛选")
) -> Dict[str, Any]:
    """
    获取分时利润数据（分时段诊断图表专用）
    
    核心功能：
    1. 按小时聚合订单数和净利润
    2. 智能识别高峰时段（订单量 > 均值+0.5σ）
    3. 计算单均利润
    
    利润计算公式（与权威手册一致）：
    订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    
    Returns:
        {
            "success": true,
            "data": {
                "date": "2025-01-07",
                "hours": ["00:00", "01:00", ..., "23:00"],
                "orders": [2, 0, 0, ...],
                "profits": [-15.5, 0, 0, ...],
                "revenues": [58.0, 0, 0, ...],
                "avg_profits": [-7.75, 0, 0, ...],  // 单均利润
                "peak_periods": [
                    {"start": "11:00", "end": "14:00", "name": "午高峰"},
                    {"start": "17:00", "end": "20:00", "name": "晚高峰"}
                ]
            }
        }
    """
    # 加载数据
    df = get_order_data(store_name)
    
    empty_result = {
        "success": True,
        "data": {
            "date": None,
            "hours": [f"{h:02d}:00" for h in range(24)],
            "orders": [0] * 24,
            "profits": [0] * 24,
            "revenues": [0] * 24,
            "avg_profits": [0] * 24,
            "peak_periods": []
        }
    }
    
    if df.empty:
        return empty_result
    
    # 确保日期列存在
    if '日期' not in df.columns:
        return {"success": False, "error": "缺少日期字段"}
    
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    
    if df.empty:
        return empty_result
    
    # 确定日期筛选方式
    date_label = None  # 用于返回的日期标签
    
    if target_date:
        # 单日期模式
        try:
            # 支持 MM-DD 格式（从数据中推断年份）
            if len(target_date) == 5 and '-' in target_date:
                max_date = df['日期'].max()
                year = max_date.year
                analysis_date = pd.to_datetime(f"{year}-{target_date}")
            else:
                analysis_date = pd.to_datetime(target_date)
            df = df[df['日期'].dt.date == analysis_date.date()]
            date_label = analysis_date.strftime('%Y-%m-%d')
        except:
            pass
    elif start_date and end_date:
        # 🆕 日期范围模式
        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df['日期'].dt.date >= start_dt.date()) & (df['日期'].dt.date <= end_dt.date())]
            date_label = f"{start_date} ~ {end_date}"
        except:
            pass
    elif start_date:
        try:
            start_dt = pd.to_datetime(start_date)
            df = df[df['日期'].dt.date >= start_dt.date()]
            date_label = f"{start_date} ~"
        except:
            pass
    elif end_date:
        try:
            end_dt = pd.to_datetime(end_date)
            df = df[df['日期'].dt.date <= end_dt.date()]
            date_label = f"~ {end_date}"
        except:
            pass
    else:
        # 默认使用数据最后一天
        analysis_date = df['日期'].max().normalize()
        df = df[df['日期'].dt.date == analysis_date.date()]
        date_label = analysis_date.strftime('%Y-%m-%d')
    
    if df.empty:
        return {
            "success": True,
            "data": {
                "date": date_label,
                "hours": [f"{h:02d}:00" for h in range(24)],
                "orders": [0] * 24,
                "profits": [0] * 24,
                "revenues": [0] * 24,
                "avg_profits": [0] * 24,
                "peak_periods": []
            }
        }
    
    # 渠道筛选
    if channel and channel != 'all' and '渠道' in df.columns:
        df = df[df['渠道'] == channel]
        if df.empty:
            return {
                "success": True,
                "data": {
                    "date": date_label,
                    "hours": [f"{h:02d}:00" for h in range(24)],
                    "orders": [0] * 24,
                    "profits": [0] * 24,
                    "revenues": [0] * 24,
                    "avg_profits": [0] * 24,
                    "peak_periods": []
                }
            }
    
    # 提取小时
    df['小时'] = df['日期'].dt.hour
    
    # 计算销售额（实收价格 × 销量）
    quantity_field = '月售' if '月售' in df.columns else '销量'
    if '实收价格' in df.columns and quantity_field in df.columns:
        df['_销售额'] = df['实收价格'].fillna(0) * df[quantity_field].fillna(1)
    else:
        df['_销售额'] = df.get('商品实售价', 0)
    
    # 按订单ID和小时聚合（先聚合到订单级）
    order_agg_dict = {
        '利润额': 'sum',
        '物流配送费': 'first',
        '_销售额': 'sum',
        '小时': 'first',
    }
    
    if '平台服务费' in df.columns:
        order_agg_dict['平台服务费'] = 'sum'
    if '企客后返' in df.columns:
        order_agg_dict['企客后返'] = 'sum'
    
    order_agg = df.groupby('订单ID').agg(order_agg_dict).reset_index()
    
    # 计算订单实际利润
    order_agg['订单实际利润'] = (
        order_agg['利润额'].fillna(0) -
        order_agg.get('平台服务费', pd.Series(0, index=order_agg.index)).fillna(0) -
        order_agg['物流配送费'].fillna(0) +
        order_agg.get('企客后返', pd.Series(0, index=order_agg.index)).fillna(0)
    )
    
    # 按小时聚合
    hourly_stats = order_agg.groupby('小时').agg({
        '订单ID': 'count',
        '订单实际利润': 'sum',
        '_销售额': 'sum'
    }).reset_index()
    
    hourly_stats.columns = ['hour', 'orders', 'profit', 'revenue']
    
    # 填充所有24小时
    all_hours = pd.DataFrame({'hour': range(24)})
    hourly_stats = all_hours.merge(hourly_stats, on='hour', how='left').fillna(0)
    
    # 计算单均利润
    hourly_stats['avg_profit'] = hourly_stats.apply(
        lambda r: round(r['profit'] / r['orders'], 2) if r['orders'] > 0 else 0, axis=1
    )
    
    # 智能识别高峰时段
    hourly_orders = hourly_stats.set_index('hour')['orders']
    peak_periods = identify_peak_periods(hourly_orders)
    
    return {
        "success": True,
        "data": {
            "date": date_label,  # 🆕 使用 date_label（支持日期范围）
            "hours": [f"{h:02d}:00" for h in range(24)],
            "orders": [int(x) for x in hourly_stats['orders'].tolist()],
            "profits": [round(float(x), 2) for x in hourly_stats['profit'].tolist()],
            "revenues": [round(float(x), 2) for x in hourly_stats['revenue'].tolist()],
            "avg_profits": [float(x) for x in hourly_stats['avg_profit'].tolist()],
            "peak_periods": peak_periods
        }
    }


# ==================== 成本结构分析API（资金流向全景桑基图专用） ====================

@router.get("/cost-structure")
async def get_cost_structure(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    获取成本结构分析数据（资金流向全景桑基图专用）
    
    与Dash版本Tab1成本结构分析完全一致：
    - 四大成本：商品成本、配送净成本、商家活动成本、平台服务费
    - 按渠道分组，支持桑基图展示资金流向
    
    计算公式（来自【权威】业务逻辑与数据字典完整手册）：
    - 商品成本：商品采购成本之和
    - 配送净成本：物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返
    - 商家活动成本：满减金额 + 商品减免金额 + 商家代金券 + 商家承担部分券 + 满赠金额 + 商家其他优惠
    - 平台服务费：平台服务费之和（商品级字段）
    """
    # 按门店加载数据
    df = get_order_data(store_name)
    
    empty_result = {
        "success": True,
        "data": {
            "channels": [],
            "total": {
                "revenue": 0,
                "profit": 0,
                "cogs": 0,
                "delivery": 0,
                "marketing": 0,
                "commission": 0
            }
        }
    }
    
    if df.empty:
        return empty_result
    
    # 日期筛选
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        if start_date:
            df = df[df['日期'].dt.date >= start_date]
        if end_date:
            df = df[df['日期'].dt.date <= end_date]
    
    if df.empty or '渠道' not in df.columns:
        return empty_result
    
    # 计算订单级指标（使用统一函数）
    order_agg = calculate_order_metrics(df)
    
    if order_agg.empty or '渠道' not in order_agg.columns:
        return empty_result
    
    # 排除咖啡渠道（与Dash版本一致）
    CHANNELS_TO_REMOVE = ['美团咖啡店', '饿了么咖啡店', '饿了么咖啡', '美团咖啡']
    order_agg = order_agg[~order_agg['渠道'].isin(CHANNELS_TO_REMOVE)]
    
    if order_agg.empty:
        return empty_result
    
    # ==================== 计算商品成本（从原始df，避免聚合损失） ====================
    # 与Dash版本Tab1成本结构分析逻辑一致
    valid_order_ids = order_agg['订单ID'].unique()
    df_valid = df[df['订单ID'].astype(str).isin([str(x) for x in valid_order_ids])]
    
    # 按渠道和订单ID计算商品成本
    cost_field = '商品采购成本' if '商品采购成本' in df_valid.columns else '成本'
    if cost_field in df_valid.columns:
        product_cost_by_channel = df_valid.groupby('渠道')[cost_field].sum().to_dict()
    else:
        product_cost_by_channel = {}
    
    # ==================== 按渠道聚合成本结构 ====================
    agg_dict = {
        '订单ID': 'count',
        '实收价格': 'sum',
        '订单实际利润': 'sum',
    }
    
    # 检查并添加可选字段
    if '配送净成本' in order_agg.columns:
        agg_dict['配送净成本'] = 'sum'
    if '商家活动成本' in order_agg.columns:
        agg_dict['商家活动成本'] = 'sum'
    if '平台服务费' in order_agg.columns:
        agg_dict['平台服务费'] = 'sum'
    elif '平台佣金' in order_agg.columns:
        agg_dict['平台佣金'] = 'sum'
    
    channel_stats = order_agg.groupby('渠道').agg(agg_dict).reset_index()
    
    # 构建返回数据
    channels_data = []
    total_revenue = 0
    total_profit = 0
    total_cogs = 0
    total_delivery = 0
    total_marketing = 0
    total_commission = 0
    
    for _, row in channel_stats.iterrows():
        channel_name = row['渠道']
        revenue = float(row['实收价格'])
        profit = float(row['订单实际利润'])
        order_count = int(row['订单ID'])
        
        # 商品成本（从原始df获取）
        cogs = float(product_cost_by_channel.get(channel_name, 0))
        
        # 配送净成本
        delivery = float(row['配送净成本']) if '配送净成本' in channel_stats.columns else 0
        
        # 商家活动成本
        marketing = float(row['商家活动成本']) if '商家活动成本' in channel_stats.columns else 0
        
        # 平台服务费
        if '平台服务费' in channel_stats.columns:
            commission = float(row['平台服务费'])
        elif '平台佣金' in channel_stats.columns:
            commission = float(row['平台佣金'])
        else:
            commission = 0
        
        # 累计总计
        total_revenue += revenue
        total_profit += profit
        total_cogs += cogs
        total_delivery += delivery
        total_marketing += marketing
        total_commission += commission
        
        channels_data.append({
            "id": str(len(channels_data) + 1),
            "name": channel_name,
            "revenue": round(revenue, 2),
            "profit": round(profit, 2),
            "order_count": order_count,
            "costs": {
                "cogs": round(cogs, 2),
                "delivery": round(delivery, 2),
                "marketing": round(marketing, 2),
                "commission": round(commission, 2)
            },
            "rates": {
                "profit_rate": round(profit / revenue * 100, 2) if revenue > 0 else 0,
                "cogs_rate": round(cogs / revenue * 100, 2) if revenue > 0 else 0,
                "delivery_rate": round(delivery / revenue * 100, 2) if revenue > 0 else 0,
                "marketing_rate": round(marketing / revenue * 100, 2) if revenue > 0 else 0,
                "commission_rate": round(commission / revenue * 100, 2) if revenue > 0 else 0
            }
        })
    
    # 按销售额排序
    channels_data.sort(key=lambda x: x['revenue'], reverse=True)
    
    # 重新分配ID
    for i, ch in enumerate(channels_data):
        ch['id'] = str(i + 1)
    
    return {
        "success": True,
        "data": {
            "channels": channels_data,
            "total": {
                "revenue": round(total_revenue, 2),
                "profit": round(total_profit, 2),
                "cogs": round(total_cogs, 2),
                "delivery": round(total_delivery, 2),
                "marketing": round(total_marketing, 2),
                "commission": round(total_commission, 2)
            }
        }
    }


# ==================== 分距离订单诊断 API ====================

# 7个距离区间常量定义
DISTANCE_BANDS = [
    {"label": "0-1km", "min": 0, "max": 1},
    {"label": "1-2km", "min": 1, "max": 2},
    {"label": "2-3km", "min": 2, "max": 3},
    {"label": "3-4km", "min": 3, "max": 4},
    {"label": "4-5km", "min": 4, "max": 5},
    {"label": "5-6km", "min": 5, "max": 6},
    {"label": "6km+", "min": 6, "max": float('inf')},
]


def get_distance_band(distance: float) -> dict:
    """
    根据距离值返回所属区间
    
    Args:
        distance: 配送距离（公里）
    
    Returns:
        对应的距离区间字典
    """
    if distance < 0:
        distance = 0
    
    for band in DISTANCE_BANDS:
        if band["min"] <= distance < band["max"]:
            return band
    
    # 默认返回最后一个区间（6km+）
    return DISTANCE_BANDS[-1]


def get_distance_band_index(distance: float) -> int:
    """
    根据距离值返回所属区间的索引
    
    Args:
        distance: 配送距离（公里）
    
    Returns:
        区间索引 (0-6)
    """
    if distance < 0:
        distance = 0
    
    for i, band in enumerate(DISTANCE_BANDS):
        if band["min"] <= distance < band["max"]:
            return i
    
    return len(DISTANCE_BANDS) - 1


@router.get("/distance-analysis")
async def get_distance_analysis(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    channel: Optional[str] = Query(None, description="渠道筛选"),
    target_date: Optional[str] = Query(None, description="目标日期(YYYY-MM-DD或MM-DD格式)"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    获取分距离订单诊断数据
    
    核心功能：
    1. 按7个距离区间聚合订单数据
    2. 计算每个区间的订单数、销售额、利润、利润率、配送成本等指标
    3. 识别最优配送距离区间（利润率最高）
    
    距离区间定义：
    - 0-1km, 1-2km, 2-3km, 3-4km, 4-5km, 5-6km, 6km+
    
    利润计算公式（与权威手册一致）：
    订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    
    Returns:
        {
            "success": true,
            "data": {
                "distance_bands": [
                    {
                        "band_label": "0-1km",
                        "min_distance": 0,
                        "max_distance": 1,
                        "order_count": 150,
                        "revenue": 12500.00,
                        "profit": 2800.00,
                        "profit_rate": 22.4,
                        "delivery_cost": 450.00,
                        "delivery_cost_rate": 3.6,
                        "avg_order_value": 83.33
                    },
                    ...
                ],
                "summary": {
                    "total_orders": 1200,
                    "avg_distance": 2.8,
                    "optimal_distance": "1-2km",
                    "total_revenue": 98000.00,
                    "total_profit": 18500.00
                }
            }
        }
    """
    # 🔍 调试日志：检查接收的参数
    print(f"📊 [distance-analysis] 接收参数: store_name={store_name!r}, channel={channel!r}, target_date={target_date!r}")
    
    # 加载数据
    df = get_order_data(store_name)
    
    # 🔍 调试日志：检查加载的数据量
    print(f"📊 [distance-analysis] 加载数据: {len(df)} 行")
    
    # 空数据返回结构
    empty_bands = []
    for band in DISTANCE_BANDS:
        empty_bands.append({
            "band_label": band["label"],
            "min_distance": band["min"],
            "max_distance": band["max"] if band["max"] != float('inf') else 999,
            "order_count": 0,
            "revenue": 0,
            "profit": 0,
            "profit_rate": 0,
            "delivery_cost": 0,
            "delivery_cost_rate": 0,
            "avg_order_value": 0
        })
    
    empty_result = {
        "success": True,
        "data": {
            "distance_bands": empty_bands,
            "summary": {
                "total_orders": 0,
                "avg_distance": 0,
                "optimal_distance": None,
                "total_revenue": 0,
                "total_profit": 0
            }
        }
    }
    
    if df.empty:
        return empty_result
    
    # 确保日期列存在
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        df = df.dropna(subset=['日期'])
    
    if df.empty:
        return empty_result
    
    # 日期筛选（与分时段诊断一致：默认使用最新一天）
    analysis_date = None
    if target_date:
        try:
            # 支持 MM-DD 格式（从数据中推断年份）
            if len(target_date) == 5 and '-' in target_date:
                max_date = df['日期'].max()
                year = max_date.year
                analysis_date = pd.to_datetime(f"{year}-{target_date}")
            else:
                analysis_date = pd.to_datetime(target_date)
        except:
            analysis_date = None
    elif start_date or end_date:
        # 有日期范围时使用范围筛选
        if start_date:
            df = df[df['日期'].dt.date >= start_date]
        if end_date:
            df = df[df['日期'].dt.date <= end_date]
    
    # 如果没有指定日期参数，默认使用数据最后一天（与分时段诊断一致）
    if analysis_date is None and start_date is None and end_date is None:
        analysis_date = df['日期'].max().normalize()
    
    # 如果有具体日期，筛选该日期数据
    if analysis_date is not None:
        df = df[df['日期'].dt.date == analysis_date.date()]
    
    if df.empty:
        return empty_result
    
    # 渠道筛选
    if channel and channel != 'all' and '渠道' in df.columns:
        df = df[df['渠道'] == channel]
        if df.empty:
            return empty_result
    
    # 计算订单级指标
    order_agg = calculate_order_metrics(df)
    
    if order_agg.empty:
        return empty_result
    
    # 获取配送距离数据
    # 从原始df获取配送距离（因为order_agg可能没有这个字段）
    if '订单ID' in df.columns:
        # 按订单ID获取配送距离（取第一个值，因为同一订单距离相同）
        distance_map = {}
        
        # 尝试从数据库直接获取配送距离
        try:
            session = SessionLocal()
            try:
                from sqlalchemy import distinct
                order_ids = order_agg['订单ID'].unique().tolist()
                
                # 批量查询配送距离
                orders_with_distance = session.query(
                    Order.order_id, 
                    Order.delivery_distance
                ).filter(
                    Order.order_id.in_(order_ids)
                ).all()
                
                for order_id, distance in orders_with_distance:
                    if distance is not None:
                        distance_map[str(order_id)] = float(distance)
                
                # ✅ 检测距离单位：如果平均值>100，说明是米，需要转换为公里
                if distance_map:
                    avg_dist = sum(distance_map.values()) / len(distance_map)
                    if avg_dist > 100:
                        print(f"⚠️ 检测到配送距离单位为【米】(平均值={avg_dist:.1f})，自动转换为公里")
                        distance_map = {k: v / 1000 for k, v in distance_map.items()}
                
                print(f"✅ 从数据库获取配送距离: {len(distance_map)} 条")
            finally:
                session.close()
        except Exception as e:
            print(f"⚠️ 从数据库获取配送距离失败: {e}")
            # 备用方案：从df获取
            for col in ['配送距离', '送达距离', 'distance', 'delivery_distance']:
                if col in df.columns:
                    temp_map = df.groupby('订单ID')[col].first().to_dict()
                    for k, v in temp_map.items():
                        if pd.notna(v):
                            distance_map[str(k)] = float(v)
                    # ✅ 检测距离单位：如果平均值>100，说明是米，需要转换为公里
                    if distance_map:
                        avg_dist = sum(distance_map.values()) / len(distance_map)
                        if avg_dist > 100:
                            print(f"⚠️ 检测到配送距离单位为【米】(平均值={avg_dist:.1f})，自动转换为公里")
                            distance_map = {k: v / 1000 for k, v in distance_map.items()}
                    break
        
        # 将配送距离添加到order_agg
        order_agg['配送距离'] = order_agg['订单ID'].astype(str).map(distance_map).fillna(0)
    else:
        order_agg['配送距离'] = 0
    
    # 为每个订单分配距离区间
    order_agg['距离区间'] = order_agg['配送距离'].apply(get_distance_band_index)
    
    # 按距离区间聚合
    band_stats = []
    total_orders = 0
    total_revenue = 0
    total_profit = 0
    total_distance = 0
    optimal_band = None
    max_profit = float('-inf')  # 改为利润总额最高
    
    for i, band in enumerate(DISTANCE_BANDS):
        band_df = order_agg[order_agg['距离区间'] == i]
        
        order_count = len(band_df)
        revenue = float(band_df['实收价格'].sum()) if '实收价格' in band_df.columns and order_count > 0 else 0
        profit = float(band_df['订单实际利润'].sum()) if '订单实际利润' in band_df.columns and order_count > 0 else 0
        
        # 配送成本（物流配送费 - 用户支付配送费 + 配送费减免金额）
        delivery_cost = 0
        if order_count > 0:
            if '物流配送费' in band_df.columns:
                delivery_cost = float(band_df['物流配送费'].sum())
            if '用户支付配送费' in band_df.columns:
                delivery_cost -= float(band_df['用户支付配送费'].sum())
            if '配送费减免金额' in band_df.columns:
                delivery_cost += float(band_df['配送费减免金额'].sum())
        
        # 计算派生指标
        profit_rate = round(profit / revenue * 100, 2) if revenue > 0 else 0
        delivery_cost_rate = round(delivery_cost / revenue * 100, 2) if revenue > 0 else 0
        avg_order_value = round(revenue / order_count, 2) if order_count > 0 else 0
        
        # 累计总计
        total_orders += order_count
        total_revenue += revenue
        total_profit += profit
        if order_count > 0:
            total_distance += float(band_df['配送距离'].sum())
        
        # 识别最优距离区间（利润总额最高且有订单）
        if order_count > 0 and profit > max_profit:
            max_profit = profit
            optimal_band = band["label"]
        
        band_stats.append({
            "band_label": band["label"],
            "min_distance": band["min"],
            "max_distance": band["max"] if band["max"] != float('inf') else 999,
            "order_count": order_count,
            "revenue": round(revenue, 2),
            "profit": round(profit, 2),
            "profit_rate": profit_rate,
            "delivery_cost": round(delivery_cost, 2),
            "delivery_cost_rate": delivery_cost_rate,
            "avg_order_value": avg_order_value
        })
    
    # 计算平均配送距离
    avg_distance = round(total_distance / total_orders, 2) if total_orders > 0 else 0
    
    # 获取分析日期（用于前端显示）- 支持日期范围
    analysis_date_str = None
    if analysis_date is not None:
        analysis_date_str = analysis_date.strftime('%Y-%m-%d')
    elif start_date and end_date:
        # 🆕 日期范围格式
        analysis_date_str = f"{start_date} ~ {end_date}"
    elif start_date:
        analysis_date_str = f"{start_date} ~"
    elif end_date:
        analysis_date_str = f"~ {end_date}"
    elif not df.empty and '日期' in df.columns:
        analysis_date_str = df['日期'].max().strftime('%Y-%m-%d')
    
    return {
        "success": True,
        "data": {
            "date": analysis_date_str,  # 🆕 添加分析日期
            "distance_bands": band_stats,
            "summary": {
                "total_orders": total_orders,
                "avg_distance": avg_distance,
                "optimal_distance": optimal_band,
                "total_revenue": round(total_revenue, 2),
                "total_profit": round(total_profit, 2)
            }
        }
    }


# ==================== 配送溢价雷达数据 API ====================

@router.get("/delivery-radar")
async def get_delivery_radar_data(
    store_name: Optional[str] = Query(None, description="门店名称"),
    channel: Optional[str] = Query(None, description="渠道筛选"),
    target_date: Optional[str] = Query(None, description="目标日期(YYYY-MM-DD格式)，默认为数据最后一天"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    min_distance: Optional[float] = Query(None, description="最小距离(km)"),
    max_distance: Optional[float] = Query(None, description="最大距离(km)")
):
    """
    获取配送溢价雷达图数据
    
    返回每个订单的：
    - 配送距离（公里）
    - 下单时段（小时）
    - 配送成本（配送净成本）
    - 客单价
    - 订单利润
    - 是否溢价（配送净成本 > 6元，与Dash版本一致）
    
    用于雷达图展示配送溢价订单的时空分布
    """
    if not store_name:
        return {"success": False, "message": "请选择门店", "data": [], "summary": None}
    
    try:
        from sqlalchemy import func  # 🆕 导入 func
        session = SessionLocal()
        try:
            # 构建查询
            query = session.query(Order).filter(Order.store_name == store_name)
            
            # 渠道筛选
            if channel:
                query = query.filter(Order.channel == channel)
            
            # 日期筛选（支持单日期和日期范围）
            analysis_date = None
            date_label = None  # 🆕 用于返回的日期标签
            
            if target_date:
                # 指定目标日期
                analysis_date = datetime.strptime(target_date, '%Y-%m-%d')
                query = query.filter(
                    Order.date >= analysis_date,
                    Order.date < analysis_date + timedelta(days=1)
                )
                date_label = target_date
            elif start_date or end_date:
                # 🆕 日期范围筛选
                if start_date:
                    query = query.filter(Order.date >= datetime.strptime(start_date, '%Y-%m-%d'))
                if end_date:
                    query = query.filter(Order.date <= datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
                # 构建日期标签
                if start_date and end_date:
                    date_label = f"{start_date} ~ {end_date}"
                elif start_date:
                    date_label = f"{start_date} ~"
                else:
                    date_label = f"~ {end_date}"
            else:
                # 默认使用最新一天
                max_date_query = session.query(func.max(Order.date)).filter(Order.store_name == store_name)
                if channel:
                    max_date_query = max_date_query.filter(Order.channel == channel)
                max_date = max_date_query.scalar()
                if max_date:
                    analysis_date = max_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    query = query.filter(
                        Order.date >= analysis_date,
                        Order.date < analysis_date + timedelta(days=1)
                    )
                    date_label = analysis_date.strftime('%Y-%m-%d')
            
            # 获取数据
            orders = query.all()
            
            if not orders:
                return {"success": True, "data": [], "date": date_label, "summary": {"total": 0, "premium_count": 0, "premium_rate": 0}}
            
            # 转换为DataFrame进行聚合
            data = []
            for order in orders:
                data.append({
                    '订单ID': order.order_id,
                    '下单时间': order.date,
                    '配送距离': order.delivery_distance or 0,
                    '物流配送费': order.delivery_fee or 0,
                    '用户支付配送费': order.user_paid_delivery_fee or 0,
                    '配送费减免金额': order.delivery_discount or 0,
                    '企客后返': order.corporate_rebate or 0,
                    '商品实售价': order.price or 0,
                    '利润额': order.profit or 0,
                    '平台服务费': order.platform_service_fee or 0,
                    '渠道': order.channel or ''
                })
            
            df = pd.DataFrame(data)
            
            # 按订单ID聚合（一个订单可能有多个商品）
            order_agg = df.groupby('订单ID').agg({
                '下单时间': 'first',
                '配送距离': 'first',  # 订单级字段
                '物流配送费': 'first',
                '用户支付配送费': 'first',
                '配送费减免金额': 'first',
                '企客后返': 'first',
                '商品实售价': 'sum',  # 商品级字段求和
                '利润额': 'sum',
                '平台服务费': 'sum',
                '渠道': 'first'
            }).reset_index()
            
            # 配送距离单位转换（如果是米，转换为公里）
            if len(order_agg) > 0:
                avg_dist = order_agg['配送距离'].mean()
                if avg_dist > 100:  # 平均值>100，说明单位是米
                    order_agg['配送距离'] = order_agg['配送距离'] / 1000
            
            # 距离筛选
            if min_distance is not None:
                order_agg = order_agg[order_agg['配送距离'] >= min_distance]
            if max_distance is not None:
                order_agg = order_agg[order_agg['配送距离'] < max_distance]
            
            # 计算配送净成本
            # 配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免) - 企客后返
            order_agg['配送净成本'] = (
                order_agg['物流配送费'] 
                - (order_agg['用户支付配送费'] - order_agg['配送费减免金额'])
                - order_agg['企客后返']
            )
            
            # 计算订单实际利润
            # 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
            order_agg['订单实际利润'] = (
                order_agg['利润额'] 
                - order_agg['平台服务费'] 
                - order_agg['物流配送费'] 
                + order_agg['企客后返']
            )
            
            # 提取小时
            order_agg['小时'] = pd.to_datetime(order_agg['下单时间']).dt.hour
            
            # 判断是否溢价（高配送费预警）
            # 定义：配送净成本 > 6元（与Dash版本保持一致）
            PREMIUM_THRESHOLD = 6
            order_agg['是否溢价'] = order_agg['配送净成本'] > PREMIUM_THRESHOLD
            
            # 🔧 性能优化：使用向量化操作替代循环
            total_orders = len(order_agg)
            premium_mask = order_agg['是否溢价']
            premium_count = int(premium_mask.sum())
            healthy_count = total_orders - premium_count
            
            premium_profit_sum = float(order_agg.loc[premium_mask, '订单实际利润'].sum())
            healthy_profit_sum = float(order_agg.loc[~premium_mask, '订单实际利润'].sum())
            
            premium_rate = round(premium_count / total_orders * 100, 1) if total_orders > 0 else 0
            
            # 构建返回数据（向量化）
            radar_points = order_agg.apply(lambda row: {
                "distance": round(row['配送距离'], 2),
                "hour": int(row['小时']),
                "delivery_cost": round(row['配送净成本'], 2),
                "order_value": round(row['商品实售价'], 2),
                "profit": round(row['订单实际利润'], 2),
                "is_premium": bool(row['是否溢价']),
                "channel": row['渠道']
            }, axis=1).tolist()
            
            return {
                "success": True,
                "date": date_label,  # 🆕 使用 date_label（支持日期范围）
                "data": radar_points,
                "summary": {
                    "total": total_orders,
                    "premium_count": premium_count,
                    "premium_rate": premium_rate,
                    "healthy_avg_profit": round(healthy_profit_sum / healthy_count, 2) if healthy_count > 0 else 0,
                    "premium_avg_profit": round(premium_profit_sum / premium_count, 2) if premium_count > 0 else 0
                }
            }
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ 获取配送溢价雷达数据失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e), "data": []}


# ==================== 营销成本结构分析API（营销成本桑基图专用） ====================

@router.get("/marketing-structure")
async def get_marketing_structure(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    获取营销成本结构分析数据（营销成本桑基图专用）
    
    展示各渠道在7个营销字段上的费用分布（不含配送费减免金额）：
    - 满减金额 (full_reduction)
    - 商品减免金额 (product_discount)
    - 商家代金券 (merchant_voucher)
    - 商家承担部分券 (merchant_share)
    - 满赠金额 (gift_amount)
    - 商家其他优惠 (other_discount)
    - 新客减免金额 (new_customer_discount)
    
    注意：配送费减免金额属于配送成本，不属于营销成本，已剔除
    
    所有7个字段都是订单级字段，聚合时使用 .first() 避免重复计算
    
    汇总指标：
    - 总营销成本 = 7个营销字段之和
    - 单均营销费用 = 总营销成本 / 订单数
    - 营销成本率 = 总营销成本 / 销售额 × 100%
    """
    # 按门店加载数据
    df = get_order_data(store_name)
    
    empty_result = {
        "success": True,
        "data": {
            "channels": [],
            "summary": {
                "total_marketing_cost": 0,
                "avg_marketing_per_order": 0,
                "marketing_cost_ratio": 0,
                "total_orders": 0,
                "total_revenue": 0
            }
        }
    }
    
    if df.empty:
        return empty_result
    
    # 日期筛选
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        if start_date:
            df = df[df['日期'].dt.date >= start_date]
        if end_date:
            df = df[df['日期'].dt.date <= end_date]
    
    if df.empty or '渠道' not in df.columns:
        return empty_result
    
    # 计算订单级指标（使用统一函数）
    order_agg = calculate_order_metrics(df)
    
    if order_agg.empty or '渠道' not in order_agg.columns:
        return empty_result
    
    # 排除咖啡渠道（与Dash版本一致）
    CHANNELS_TO_REMOVE = ['美团咖啡店', '饿了么咖啡店', '饿了么咖啡', '美团咖啡']
    order_agg = order_agg[~order_agg['渠道'].isin(CHANNELS_TO_REMOVE)]
    
    if order_agg.empty:
        return empty_result
    
    # 7个营销字段映射（中文字段名 -> API返回字段名）
    # 注意：配送费减免金额属于配送成本，不属于营销成本，已剔除
    MARKETING_FIELDS = {
        '满减金额': 'full_reduction',
        '商品减免金额': 'product_discount',
        '商家代金券': 'merchant_voucher',
        '商家承担部分券': 'merchant_share',
        '满赠金额': 'gift_amount',
        '商家其他优惠': 'other_discount',
        '新客减免金额': 'new_customer_discount'
    }
    
    # 按渠道聚合营销字段
    agg_dict = {
        '订单ID': 'count',
        '实收价格': 'sum',
    }
    
    # 添加7个营销字段的聚合（订单级字段已在calculate_order_metrics中用first聚合）
    for cn_field in MARKETING_FIELDS.keys():
        if cn_field in order_agg.columns:
            agg_dict[cn_field] = 'sum'
    
    channel_stats = order_agg.groupby('渠道').agg(agg_dict).reset_index()
    
    # 构建返回数据
    channels_data = []
    total_marketing_cost = 0
    total_orders = 0
    total_revenue = 0
    
    for _, row in channel_stats.iterrows():
        channel_name = row['渠道']
        order_count = int(row['订单ID'])
        revenue = float(row['实收价格'])
        
        # 构建营销成本字典
        marketing_costs = {}
        channel_marketing_total = 0
        
        for cn_field, en_field in MARKETING_FIELDS.items():
            if cn_field in channel_stats.columns:
                value = float(row[cn_field])
            else:
                value = 0.0
            marketing_costs[en_field] = round(value, 2)
            channel_marketing_total += value
        
        # 累计总计
        total_marketing_cost += channel_marketing_total
        total_orders += order_count
        total_revenue += revenue
        
        channels_data.append({
            "channel": channel_name,
            "order_count": order_count,
            "revenue": round(revenue, 2),
            "marketing_costs": marketing_costs,
            "total_marketing_cost": round(channel_marketing_total, 2)
        })
    
    # 按总营销成本排序
    channels_data.sort(key=lambda x: x['total_marketing_cost'], reverse=True)
    
    # 计算汇总指标
    avg_marketing_per_order = total_marketing_cost / total_orders if total_orders > 0 else 0
    marketing_cost_ratio = (total_marketing_cost / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        "success": True,
        "data": {
            "channels": channels_data,
            "summary": {
                "total_marketing_cost": round(total_marketing_cost, 2),
                "avg_marketing_per_order": round(avg_marketing_per_order, 2),
                "marketing_cost_ratio": round(marketing_cost_ratio, 2),
                "total_orders": total_orders,
                "total_revenue": round(total_revenue, 2)
            }
        }
    }


# ==================== 营销成本趋势分析API（营销成本趋势图专用） ====================

@router.get("/marketing-trend")
async def get_marketing_trend(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    channel: Optional[str] = Query(None, description="渠道筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    获取营销成本趋势分析数据（营销成本趋势图专用）
    
    按日期聚合7个营销字段的成本数据，用于展示各营销类型占比随时间的变化趋势。
    
    7个营销字段（不含配送费减免金额）：
    - 满减金额 (full_reduction)
    - 商品减免金额 (product_discount)
    - 商家代金券 (merchant_voucher)
    - 商家承担部分券 (merchant_share)
    - 满赠金额 (gift_amount)
    - 商家其他优惠 (other_discount)
    - 新客减免金额 (new_customer_discount)
    
    注意：配送费减免金额属于配送成本，不属于营销成本，已剔除
    
    所有7个字段都是订单级字段，聚合时使用 .first() 避免重复计算
    
    返回数据结构：
    - dates: 日期数组
    - series: 各营销类型的每日金额数组
    - totals: 每日总营销成本数组
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    # 按门店加载数据
    df = get_order_data(store_name)
    
    # 7个营销字段映射（中文字段名 -> API返回字段名）
    # 注意：配送费减免金额属于配送成本，不属于营销成本，已剔除
    MARKETING_FIELDS = {
        '满减金额': 'full_reduction',
        '商品减免金额': 'product_discount',
        '商家代金券': 'merchant_voucher',
        '商家承担部分券': 'merchant_share',
        '满赠金额': 'gift_amount',
        '商家其他优惠': 'other_discount',
        '新客减免金额': 'new_customer_discount'
    }
    
    empty_result = {
        "success": True,
        "data": {
            "dates": [],
            "series": {
                "full_reduction": [],
                "product_discount": [],
                "merchant_voucher": [],
                "merchant_share": [],
                "gift_amount": [],
                "other_discount": [],
                "new_customer_discount": []
            },
            "totals": []
        }
    }
    
    if df.empty:
        return empty_result
    
    # 渠道筛选
    if channel and channel != 'all' and '渠道' in df.columns:
        df = df[df['渠道'] == channel]
    
    if df.empty:
        return empty_result
    
    # 日期筛选
    if '日期' not in df.columns:
        return empty_result
    
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    
    if df.empty:
        return empty_result
    
    # Requirements 1.4: 支持按日期范围过滤
    if start_date:
        df = df[df['日期'].dt.date >= start_date]
    if end_date:
        df = df[df['日期'].dt.date <= end_date]
    
    if df.empty:
        return empty_result
    
    # Requirements 1.2: 计算订单级指标（使用统一函数，订单级字段用first聚合）
    order_agg = calculate_order_metrics(df)
    
    if order_agg.empty or '日期' not in order_agg.columns:
        return empty_result
    
    # 确保日期列是datetime类型
    order_agg['日期'] = pd.to_datetime(order_agg['日期'], errors='coerce')
    order_agg = order_agg.dropna(subset=['日期'])
    
    if order_agg.empty:
        return empty_result
    
    # 提取日期部分用于分组
    order_agg['日期_str'] = order_agg['日期'].dt.strftime('%Y-%m-%d')
    
    # 按日期聚合营销字段
    agg_dict = {}
    for cn_field in MARKETING_FIELDS.keys():
        if cn_field in order_agg.columns:
            agg_dict[cn_field] = 'sum'
    
    if not agg_dict:
        return empty_result
    
    daily_stats = order_agg.groupby('日期_str').agg(agg_dict).reset_index()
    
    # 按日期排序
    daily_stats = daily_stats.sort_values('日期_str')
    
    # 构建返回数据
    dates = daily_stats['日期_str'].tolist()
    
    # Requirements 1.3: 构建series数据结构
    series = {}
    for cn_field, en_field in MARKETING_FIELDS.items():
        if cn_field in daily_stats.columns:
            series[en_field] = [round(float(v), 2) for v in daily_stats[cn_field].tolist()]
        else:
            # Requirements 1.5: 某日期某营销类型金额为0时返回0（不省略）
            series[en_field] = [0.0] * len(dates)
    
    # 计算每日总营销成本
    totals = []
    for i in range(len(dates)):
        daily_total = sum(series[en_field][i] for en_field in MARKETING_FIELDS.values())
        totals.append(round(daily_total, 2))
    
    return {
        "success": True,
        "data": {
            "dates": dates,
            "series": series,
            "totals": totals
        }
    }
