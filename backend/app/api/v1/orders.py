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
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

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
CACHE_TTL = 300  # 缓存有效期5分钟
ORDER_DATA_CACHE_KEY = "order_data_cache"
ORDER_DATA_TIMESTAMP_KEY = "order_data_timestamp"

# 内存缓存（备用）
_memory_cache = {
    "order_data": None,
    "timestamp": 0
}

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


def get_order_data() -> pd.DataFrame:
    """
    从数据库加载订单数据（带缓存）
    
    缓存策略:
    1. 优先使用Redis缓存
    2. 备用内存缓存
    3. 缓存有效期5分钟
    """
    global _memory_cache
    current_time = time.time()
    
    # 1. 尝试从Redis获取缓存
    if REDIS_AVAILABLE and redis_client:
        try:
            cached_timestamp = redis_client.get(ORDER_DATA_TIMESTAMP_KEY)
            if cached_timestamp:
                if current_time - float(cached_timestamp) < CACHE_TTL:
                    cached_data = redis_client.get(ORDER_DATA_CACHE_KEY)
                    if cached_data:
                        data = json.loads(cached_data)
                        print(f"📦 使用Redis缓存数据 ({len(data)} 条)")
                        return pd.DataFrame(data)
        except Exception as e:
            print(f"⚠️ Redis读取失败: {e}")
    
    # 2. 尝试使用内存缓存
    if _memory_cache["order_data"] is not None:
        if current_time - _memory_cache["timestamp"] < CACHE_TTL:
            print(f"📦 使用内存缓存数据")
            return _memory_cache["order_data"].copy()
    
    # 3. 从数据库加载
    print("🔄 从数据库加载订单数据...")
    session = SessionLocal()
    try:
        orders = session.query(Order).all()
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
                '月售': order.quantity,
                '实收价格': float(order.actual_price or 0),
                '商品实售价': float(order.price or 0),  # 数据库字段是price
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
                '库存': order.stock,
            })
        
        df = pd.DataFrame(data)
        print(f"✅ 数据库加载完成: {len(df)} 条记录")
        
        # 4. 更新缓存
        # 更新内存缓存
        _memory_cache["order_data"] = df.copy()
        _memory_cache["timestamp"] = current_time
        
        # 更新Redis缓存
        if REDIS_AVAILABLE and redis_client:
            try:
                # 将日期转换为字符串以便JSON序列化
                cache_data = data.copy()
                for item in cache_data:
                    if item.get('日期'):
                        item['日期'] = str(item['日期'])
                
                redis_client.set(ORDER_DATA_CACHE_KEY, json.dumps(cache_data, ensure_ascii=False))
                redis_client.set(ORDER_DATA_TIMESTAMP_KEY, str(current_time))
                print("✅ 数据已缓存到Redis")
            except Exception as e:
                print(f"⚠️ Redis缓存写入失败: {e}")
        
        return df
    finally:
        session.close()


def invalidate_cache():
    """清除缓存（数据更新时调用）"""
    global _memory_cache
    _memory_cache = {"order_data": None, "timestamp": 0}
    
    if REDIS_AVAILABLE and redis_client:
        try:
            redis_client.delete(ORDER_DATA_CACHE_KEY)
            redis_client.delete(ORDER_DATA_TIMESTAMP_KEY)
            print("✅ 缓存已清除")
        except Exception as e:
            print(f"⚠️ Redis缓存清除失败: {e}")


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
    for field in ['满减金额', '商品减免金额', '新客减免金额', '渠道', '门店名称', '日期']:
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
    
    # 按渠道类型过滤异常订单
    if '渠道' in order_agg.columns:
        is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
        is_zero_fee = order_agg['平台服务费'] <= 0
        invalid_orders = is_fee_channel & is_zero_fee
        order_agg = order_agg[~invalid_orders].copy()
    
    return order_agg


@router.get("/overview")
async def get_order_overview(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
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
    """
    df = get_order_data()
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
    
    # 门店筛选
    if store_name and '门店名称' in df.columns:
        df = df[df['门店名称'] == store_name]
    
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
    
    return {
        "success": True,
        "data": {
            "total_orders": int(total_orders),
            "total_actual_sales": round(float(total_actual_sales), 2),
            "total_profit": round(float(total_profit), 2),
            "avg_order_value": round(float(avg_order_value), 2),
            "profit_rate": round(float(profit_rate), 2),
            "active_products": int(active_products),
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
    """
    df = get_order_data()
    if df.empty:
        return {"success": True, "data": []}
    
    # 门店筛选
    if store_name and '门店名称' in df.columns:
        df = df[df['门店名称'] == store_name]
    
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
    granularity: str = Query("day", description="粒度: day/week/month")
) -> Dict[str, Any]:
    """
    获取订单趋势数据
    
    返回每日/每周/每月的订单数、销售额、利润、客单价
    """
    df = get_order_data()
    if df.empty:
        return {"success": True, "data": {"dates": [], "order_counts": [], "amounts": [], "profits": [], "avg_values": []}}
    
    # 门店筛选
    if store_name and '门店名称' in df.columns:
        df = df[df['门店名称'] == store_name]
    
    if '日期' not in df.columns:
        return {"success": False, "error": "缺少日期字段"}
    
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    
    if df.empty:
        return {"success": True, "data": {"dates": [], "order_counts": [], "amounts": [], "profits": [], "avg_values": []}}
    
    # 筛选最近N天
    max_date = df['日期'].max()
    if pd.isna(max_date):
        return {"success": True, "data": {"dates": [], "order_counts": [], "amounts": [], "profits": [], "avg_values": []}}
    
    min_date = max_date - timedelta(days=days)
    df = df[df['日期'] >= min_date]
    
    if df.empty:
        return {"success": True, "data": {"dates": [], "order_counts": [], "amounts": [], "profits": [], "avg_values": []}}
    
    # 根据粒度分组
    if granularity == 'week':
        df['period'] = df['日期'].dt.to_period('W').apply(lambda x: x.start_time)
    elif granularity == 'month':
        df['period'] = df['日期'].dt.to_period('M').apply(lambda x: x.start_time)
    else:
        df['period'] = df['日期'].dt.date
    
    # 先聚合到订单级
    order_agg = calculate_order_metrics(df)
    
    if '日期' in order_agg.columns:
        order_agg['日期'] = pd.to_datetime(order_agg['日期'])
        if granularity == 'week':
            order_agg['period'] = order_agg['日期'].dt.to_period('W').apply(lambda x: x.start_time)
        elif granularity == 'month':
            order_agg['period'] = order_agg['日期'].dt.to_period('M').apply(lambda x: x.start_time)
        else:
            order_agg['period'] = order_agg['日期'].dt.date
        
        # 按周期聚合
        daily = order_agg.groupby('period').agg({
            '订单ID': 'count',
            '实收价格': 'sum',
            '订单实际利润': 'sum',
        }).reset_index()
        
        daily.columns = ['date', 'order_count', 'amount', 'profit']
    else:
        # 备用方案：按原始数据日期聚合
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
    
    return {
        "success": True,
        "data": {
            "dates": [str(d) for d in daily['date'].tolist()],
            "order_counts": [int(x) for x in daily['order_count'].tolist()],
            "amounts": [round(float(x), 2) for x in daily['amount'].tolist()],
            "profits": [round(float(x), 2) for x in daily['profit'].tolist()],
            "avg_values": [round(float(x), 2) for x in daily['avg_value'].tolist()],
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
    df = get_order_data()
    if df.empty:
        return {"success": True, "data": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
    
    # 门店筛选
    if store_name and '门店名称' in df.columns:
        df = df[df['门店名称'] == store_name]
    
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
    """获取门店列表"""
    df = get_order_data()
    if df.empty or '门店名称' not in df.columns:
        return {"success": True, "data": []}
    
    stores = sorted(df['门店名称'].dropna().unique().tolist())
    return {"success": True, "data": stores}


@router.get("/channel-list")
async def get_channel_list() -> Dict[str, Any]:
    """获取渠道列表"""
    df = get_order_data()
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
    df = get_order_data()
    if df.empty:
        return {"success": True, "data": {"labels": [], "counts": [], "colors": []}}
    
    # 门店筛选
    if store_name and '门店名称' in df.columns:
        df = df[df['门店名称'] == store_name]
    
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
    df = get_order_data()
    if df.empty:
        return {"success": True, "data": {"price_ranges": [], "business_zones": {}, "avg_basket_depth": 0}}
    
    # 门店筛选
    if store_name and '门店名称' in df.columns:
        df = df[df['门店名称'] == store_name]
    
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
    df = get_order_data()
    if df.empty:
        return {"success": True, "data": {"categories": [], "weeks": [], "series": []}}
    
    # 门店筛选
    if store_name and '门店名称' in df.columns:
        df = df[df['门店名称'] == store_name]
    
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
    """
    df = get_order_data()
    if df.empty:
        return {"success": True, "data": {"current": {}, "previous": {}, "changes": {}}}
    
    # 门店筛选
    if store_name and '门店名称' in df.columns:
        df = df[df['门店名称'] == store_name]
    
    if '日期' not in df.columns:
        return {"success": True, "data": {"current": {}, "previous": {}, "changes": {}}}
    
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])  # 移除无效日期
    
    if df.empty:
        return {"success": True, "data": {"current": {}, "previous": {}, "changes": {}}}
    
    # 确定日期范围
    max_date = df['日期'].max()
    if pd.isna(max_date):
        return {"success": True, "data": {"current": {}, "previous": {}, "changes": {}}}
    
    if start_date is None:
        end_date = max_date.date()
        start_date = end_date - timedelta(days=6)  # 默认最近7天
    elif end_date is None:
        end_date = start_date + timedelta(days=6)
    
    # 计算周期长度
    period_days = (end_date - start_date).days + 1
    if period_days <= 0:
        period_days = 7  # 默认7天
    
    # 计算上一周期日期范围
    prev_end_date = start_date - timedelta(days=1)
    prev_start_date = prev_end_date - timedelta(days=period_days - 1)
    
    # 当前周期数据
    current_df = df[(df['日期'].dt.date >= start_date) & (df['日期'].dt.date <= end_date)]
    # 上一周期数据
    prev_df = df[(df['日期'].dt.date >= prev_start_date) & (df['日期'].dt.date <= prev_end_date)]
    
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
    """
    df = get_order_data()
    if df.empty:
        return {"success": True, "data": []}
    
    # 门店筛选
    if store_name and '门店名称' in df.columns:
        df = df[df['门店名称'] == store_name]
    
    if '日期' not in df.columns or '渠道' not in df.columns:
        return {"success": True, "data": []}
    
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    
    if df.empty:
        return {"success": True, "data": []}
    
    # 确定日期范围
    max_date = df['日期'].max()
    if pd.isna(max_date):
        return {"success": True, "data": []}
    
    if start_date is None:
        end_date = max_date.date()
        start_date = end_date - timedelta(days=6)
    elif end_date is None:
        end_date = start_date + timedelta(days=6)
    
    period_days = (end_date - start_date).days + 1
    if period_days <= 0:
        period_days = 7
    
    prev_end_date = start_date - timedelta(days=1)
    prev_start_date = prev_end_date - timedelta(days=period_days - 1)
    
    # 当前周期和上一周期数据
    current_df = df[(df['日期'].dt.date >= start_date) & (df['日期'].dt.date <= end_date)]
    prev_df = df[(df['日期'].dt.date >= prev_start_date) & (df['日期'].dt.date <= prev_end_date)]
    
    # 获取所有渠道
    channels = df['渠道'].dropna().unique().tolist()
    
    result = []
    for channel in channels:
        # 当前周期渠道数据
        curr_ch = current_df[current_df['渠道'] == channel]
        curr_metrics = calculate_channel_metrics(curr_ch)
        
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
        
        # 评级
        rating = get_channel_rating(curr_metrics, changes)
        
        result.append({
            "channel": channel,
            "current": curr_metrics,
            "previous": prev_metrics,
            "changes": changes,
            "rating": rating
        })
    
    # 按订单数排序
    result.sort(key=lambda x: x['current'].get('order_count', 0), reverse=True)
    
    return {"success": True, "data": result}


def calculate_channel_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """计算单个渠道的指标"""
    if df.empty:
        return {
            "order_count": 0,
            "amount": 0,
            "profit": 0,
            "avg_value": 0,
            "profit_rate": 0
        }
    
    order_agg = calculate_order_metrics(df)
    
    order_count = len(order_agg)
    amount = order_agg['实收价格'].sum() if '实收价格' in order_agg.columns else 0
    profit = order_agg['订单实际利润'].sum() if '订单实际利润' in order_agg.columns else 0
    avg_value = amount / order_count if order_count > 0 else 0
    profit_rate = (profit / amount * 100) if amount > 0 else 0
    
    return {
        "order_count": int(order_count),
        "amount": round(float(amount), 2),
        "profit": round(float(profit), 2),
        "avg_value": round(float(avg_value), 2),
        "profit_rate": round(float(profit_rate), 2)
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
    df = get_order_data()
    if df.empty:
        return {"success": True, "data": {"low_profit": [], "high_delivery": [], "negative_profit": [], "summary": {}}}
    
    # 门店筛选
    if store_name and '门店名称' in df.columns:
        df = df[df['门店名称'] == store_name]
    
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
    df = get_order_data()
    
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
    
    # 门店筛选
    if store_name and '门店名称' in df.columns:
        df = df[df['门店名称'] == store_name]
    
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
