# -*- coding: utf-8 -*-
"""
全量门店对比分析 API

功能：
- 全量门店关键指标对比
- 门店排行榜
- 环比数据（本周 vs 上周）+ 同比数据（去年同期）
- 门店效率分析
- 异常门店检测

计算逻辑与经营总览（orders.py）完全一致

优化点：
- SQL层面渠道筛选（避免N+1查询）
- 缓存key包含渠道参数
- 平均利润率使用加权平均
- 添加同比数据
- 添加异常检测
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np
import time
import json

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
from .orders import calculate_order_metrics, calculate_gmv
from sqlalchemy import and_, or_, func, text

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

# 检查预聚合表是否可用
AGGREGATION_TABLE_AVAILABLE = False
try:
    session = SessionLocal()
    result = session.execute(text("SELECT COUNT(*) FROM store_daily_summary"))
    count = result.scalar()
    if count and count > 0:
        AGGREGATION_TABLE_AVAILABLE = True
        print(f"✅ 预聚合表可用: {count} 条汇总记录")
    session.close()
except Exception as e:
    print(f"⚠️ 预聚合表不可用: {e}")

router = APIRouter()

# ==================== 缓存配置 ====================
# ✅ 优化：延长TTL到24小时（数据每天更新一次）
CACHE_TTL = 86400  # 缓存有效期24小时
STORE_COMPARISON_CACHE_KEY = "store_comparison_all"
STORE_COMPARISON_TIMESTAMP_KEY = "store_comparison_timestamp"

# 渠道与订单编号前缀的映射（全局常量）
CHANNEL_PREFIX_MAP = {
    '美团': 'SG',
    '饿了么': 'ELE',
    '京东': 'JD'
}

# 内存缓存（备用）- 支持渠道维度
_store_comparison_cache = {}


def get_store_metrics_from_aggregation(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    channel: Optional[str] = None
) -> pd.DataFrame:
    """
    从预聚合表快速获取门店指标（性能优化版）
    
    使用预聚合表 store_daily_summary 进行查询，
    查询时间从 ~500ms 降低到 ~2ms
    
    注意：需要先运行 更新预聚合表添加GMV字段.py 脚本添加GMV字段
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        channel: 渠道名称（美团/饿了么/京东），None表示全部
    
    Returns:
        DataFrame with store metrics
    """
    if not AGGREGATION_TABLE_AVAILABLE:
        return pd.DataFrame()
    
    session = SessionLocal()
    try:
        # 检查是否有GMV字段
        check_sql = """
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'store_daily_summary' AND column_name = 'gmv'
        """
        result = session.execute(text(check_sql))
        has_gmv = result.fetchone() is not None
        
        if not has_gmv:
            print("⚠️ [预聚合表] 缺少GMV字段，请运行 更新预聚合表添加GMV字段.py")
            return pd.DataFrame()
        
        # 构建查询（包含GMV字段）
        sql = """
            SELECT 
                store_name,
                SUM(order_count) as order_count,
                SUM(total_revenue) as total_revenue,
                SUM(total_profit) as total_profit,
                SUM(delivery_net_cost) as total_delivery_cost,
                SUM(total_marketing_cost) as total_marketing_cost,
                SUM(COALESCE(gmv, 0)) as total_gmv
            FROM store_daily_summary
            WHERE 1=1
        """
        params = {}
        
        if start_date:
            sql += " AND summary_date >= :start_date"
            params['start_date'] = start_date
        if end_date:
            sql += " AND summary_date <= :end_date"
            params['end_date'] = end_date
        if channel and channel in ['美团', '饿了么', '京东']:
            sql += " AND channel = :channel"
            params['channel'] = channel
        
        sql += " GROUP BY store_name"
        
        result = session.execute(text(sql), params)
        rows = result.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        # 转换为DataFrame
        data = []
        for row in rows:
            store_name = row[0]
            order_count = int(row[1]) if row[1] else 0
            total_revenue = float(row[2]) if row[2] else 0
            total_profit = float(row[3]) if row[3] else 0
            total_delivery_cost = float(row[4]) if row[4] else 0
            total_marketing_cost = float(row[5]) if row[5] else 0
            total_gmv = float(row[6]) if row[6] else 0
            
            # 计算派生指标
            profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            aov = total_revenue / order_count if order_count > 0 else 0
            avg_delivery_fee = total_delivery_cost / order_count if order_count > 0 else 0
            avg_marketing_cost = total_marketing_cost / order_count if order_count > 0 else 0
            delivery_cost_rate = (total_delivery_cost / total_revenue * 100) if total_revenue > 0 else 0
            # ✅ 营销成本率 = 营销成本 / GMV × 100%
            marketing_cost_rate = (total_marketing_cost / total_gmv * 100) if total_gmv > 0 else 0
            
            data.append({
                'store_name': store_name,
                'order_count': order_count,
                'total_revenue': total_revenue,
                'total_profit': total_profit,
                'total_delivery_cost': total_delivery_cost,
                'total_marketing_cost': total_marketing_cost,
                'gmv': total_gmv,
                'profit_margin': profit_margin,
                'aov': aov,
                'avg_delivery_fee': avg_delivery_fee,
                'avg_marketing_cost': avg_marketing_cost,
                'delivery_cost_rate': delivery_cost_rate,
                'marketing_cost_rate': marketing_cost_rate
            })
        
        df = pd.DataFrame(data)
        
        # 计算排名
        df['revenue_rank'] = df['total_revenue'].rank(ascending=False, method='min').astype(int)
        df['profit_rank'] = df['total_profit'].rank(ascending=False, method='min').astype(int)
        df['profit_margin_rank'] = df['profit_margin'].rank(ascending=False, method='min').astype(int)
        
        print(f"✅ [预聚合表+GMV] 快速查询完成: {len(df)} 门店, 渠道={channel or '全部'}")
        return df
    except Exception as e:
        print(f"⚠️ 预聚合表查询失败: {e}")
        return pd.DataFrame()
    finally:
        session.close()


def get_all_stores_data(
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None,
    channel: Optional[str] = None
) -> pd.DataFrame:
    """
    从数据库加载所有门店的订单数据（带缓存）
    
    优化点：
    1. SQL层面直接筛选渠道（避免N+1查询）
    2. 缓存key包含渠道参数
    3. 优先使用Redis缓存，备用内存缓存
    4. 缓存有效期5分钟
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        channel: 渠道名称（美团/饿了么/京东），None表示全部
    """
    global _store_comparison_cache
    current_time = time.time()
    
    # 生成缓存key（包含日期范围和渠道）
    channel_key = channel if channel else "all"
    date_key = f"{start_date}:{end_date}:{channel_key}"
    redis_cache_key = f"{STORE_COMPARISON_CACHE_KEY}:{date_key}"
    redis_timestamp_key = f"{STORE_COMPARISON_TIMESTAMP_KEY}:{date_key}"
    
    # 1. 尝试从Redis获取缓存
    if REDIS_AVAILABLE and redis_client:
        try:
            cached_timestamp = redis_client.get(redis_timestamp_key)
            if cached_timestamp:
                if current_time - float(cached_timestamp) < CACHE_TTL:
                    cached_data = redis_client.get(redis_cache_key)
                    if cached_data:
                        data = json.loads(cached_data)
                        print(f"📦 使用Redis缓存数据 (全量门店对比, 渠道={channel_key}, {len(data)} 条)")
                        return pd.DataFrame(data)
        except Exception as e:
            print(f"⚠️ Redis读取失败: {e}")
    
    # 2. 尝试使用内存缓存
    cache_entry = _store_comparison_cache.get(date_key)
    if cache_entry and current_time - cache_entry.get("timestamp", 0) < CACHE_TTL:
        print(f"📦 使用内存缓存数据 (全量门店对比, 渠道={channel_key})")
        return cache_entry["data"].copy()
    
    # 3. 从数据库加载（SQL层面直接筛选）
    print(f"🔄 从数据库加载全量门店数据 (日期: {start_date}~{end_date}, 渠道: {channel_key})...")
    session = SessionLocal()
    try:
        query = session.query(Order)
        
        # 日期筛选
        if start_date:
            query = query.filter(Order.date >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(Order.date <= datetime.combine(end_date, datetime.max.time()))
        
        # ✅ SQL层面渠道筛选（避免N+1查询）
        if channel and channel in CHANNEL_PREFIX_MAP:
            prefix = CHANNEL_PREFIX_MAP[channel]
            query = query.filter(Order.order_number.like(f'{prefix}%'))
            print(f"   SQL渠道筛选: order_number LIKE '{prefix}%'")
        
        orders = query.all()
        if not orders:
            return pd.DataFrame()
        
        # 转换为DataFrame
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '门店ID': order.store_id,
                '日期': order.date,
                '渠道': order.channel,
                '商品名称': order.product_name,
                '一级分类名': order.category_level1,
                '三级分类名': order.category_level3,
                '月售': order.quantity if order.quantity is not None else 1,
                '实收价格': float(order.actual_price or 0),
                '商品实售价': float(order.price or 0),
                '商品原价': float(order.original_price or 0),  # ✅ 新增：GMV计算需要
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
                '商家代金券': float(order.merchant_voucher or 0),
                '商家承担部分券': float(order.merchant_share or 0),
                '满赠金额': float(order.gift_amount or 0),
                '商家其他优惠': float(order.other_merchant_discount or 0),
                '打包袋金额': float(order.packaging_fee or 0),  # ✅ 新增：GMV计算需要
            })
        
        df = pd.DataFrame(data)
        print(f"✅ 全量门店数据加载完成: {len(df)} 条记录, {df['门店名称'].nunique()} 个门店")
        
        # 4. 更新缓存
        # 更新内存缓存
        _store_comparison_cache[date_key] = {
            "data": df.copy(),
            "timestamp": current_time
        }
        
        # 更新Redis缓存
        if REDIS_AVAILABLE and redis_client:
            try:
                # 将日期转换为字符串以便JSON序列化
                cache_data = data.copy()
                for item in cache_data:
                    if item.get('日期'):
                        item['日期'] = str(item['日期'])
                
                redis_client.set(redis_cache_key, json.dumps(cache_data, ensure_ascii=False))
                redis_client.set(redis_timestamp_key, str(current_time))
                # 设置过期时间
                redis_client.expire(redis_cache_key, CACHE_TTL)
                redis_client.expire(redis_timestamp_key, CACHE_TTL)
                print(f"✅ 数据已缓存到Redis (全量门店对比, 渠道={channel_key})")
            except Exception as e:
                print(f"⚠️ Redis缓存写入失败: {e}")
        
        return df
    finally:
        session.close()


def invalidate_store_comparison_cache():
    """清除全量门店对比缓存（数据更新时调用）"""
    global _store_comparison_cache
    _store_comparison_cache = {}
    
    if REDIS_AVAILABLE and redis_client:
        try:
            # 清除所有门店对比相关的缓存
            keys = redis_client.keys(f"{STORE_COMPARISON_CACHE_KEY}:*")
            if keys:
                redis_client.delete(*keys)
            keys = redis_client.keys(f"{STORE_COMPARISON_TIMESTAMP_KEY}:*")
            if keys:
                redis_client.delete(*keys)
            print("✅ 全量门店对比Redis缓存已清除")
        except Exception as e:
            print(f"⚠️ Redis缓存清除失败: {e}")
    
    print("✅ 全量门店对比内存缓存已清除")


def calculate_store_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算每个门店的关键指标
    
    使用与 orders.py 完全一致的计算逻辑
    
    公式说明：
    - 营销成本率 = 营销成本 / GMV × 100%（GMV = 商品原价×销量 + 打包袋 + 用户支付配送费）
    - 配送成本率 = 配送净成本 / 实收金额 × 100%
    """
    if df.empty or '门店名称' not in df.columns:
        return pd.DataFrame()
    
    # 先计算订单级指标（复用 orders.py 的函数）
    order_agg = calculate_order_metrics(df)
    
    if order_agg.empty or '门店名称' not in order_agg.columns:
        return pd.DataFrame()
    
    # 确保配送净成本字段存在（与 Dash 版本一致）
    if '配送净成本' not in order_agg.columns:
        # 计算配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返
        order_agg['配送净成本'] = (
            order_agg['物流配送费'].fillna(0) -
            (order_agg.get('用户支付配送费', 0) - order_agg.get('配送费减免金额', 0)) -
            order_agg.get('企客后返', 0)
        )
        print(f"✅ [calculate_store_metrics] 计算配送净成本: 总计 ¥{order_agg['配送净成本'].sum():,.2f}")
    
    # ✅ 按门店计算GMV（使用正确的公式：剔除商品原价<=0的整行）
    store_gmv_data = {}
    for store_name in df['门店名称'].unique():
        store_df = df[df['门店名称'] == store_name]
        gmv_result = calculate_gmv(store_df)
        store_gmv_data[store_name] = {
            'gmv': gmv_result['gmv'],
            'marketing_cost': gmv_result['marketing_cost'],
            'marketing_cost_rate': gmv_result['marketing_cost_rate']
        }
    
    # 按门店聚合
    store_stats = order_agg.groupby('门店名称').agg({
        '订单ID': 'count',
        '实收价格': 'sum',
        '订单实际利润': 'sum',
        '配送净成本': 'sum',
        '商家活动成本': 'sum',
    }).reset_index()
    
    store_stats.columns = ['store_name', 'order_count', 'total_revenue', 'total_profit', 'total_delivery_cost', 'total_marketing_cost']
    
    # ✅ 添加GMV数据
    store_stats['gmv'] = store_stats['store_name'].map(lambda x: store_gmv_data.get(x, {}).get('gmv', 0))
    store_stats['gmv_marketing_cost'] = store_stats['store_name'].map(lambda x: store_gmv_data.get(x, {}).get('marketing_cost', 0))
    
    # 计算派生指标
    store_stats['profit_margin'] = store_stats.apply(
        lambda r: r['total_profit'] / r['total_revenue'] * 100 if r['total_revenue'] > 0 else 0, axis=1
    )
    store_stats['aov'] = store_stats.apply(
        lambda r: r['total_revenue'] / r['order_count'] if r['order_count'] > 0 else 0, axis=1
    )
    # 单均配送费 = 配送净成本 / 订单数
    store_stats['avg_delivery_fee'] = store_stats.apply(
        lambda r: r['total_delivery_cost'] / r['order_count'] if r['order_count'] > 0 else 0, axis=1
    )
    store_stats['avg_marketing_cost'] = store_stats.apply(
        lambda r: r['total_marketing_cost'] / r['order_count'] if r['order_count'] > 0 else 0, axis=1
    )
    # 配送成本率 = 配送净成本 / 实收金额 × 100%
    store_stats['delivery_cost_rate'] = store_stats.apply(
        lambda r: r['total_delivery_cost'] / r['total_revenue'] * 100 if r['total_revenue'] > 0 else 0, axis=1
    )
    # ✅ 营销成本率 = 营销成本(7字段) / GMV × 100%（使用正确的GMV计算）
    store_stats['marketing_cost_rate'] = store_stats.apply(
        lambda r: r['gmv_marketing_cost'] / r['gmv'] * 100 if r['gmv'] > 0 else 0, axis=1
    )
    
    # 计算排名
    store_stats['revenue_rank'] = store_stats['total_revenue'].rank(ascending=False, method='min').astype(int)
    store_stats['profit_rank'] = store_stats['total_profit'].rank(ascending=False, method='min').astype(int)
    store_stats['profit_margin_rank'] = store_stats['profit_margin'].rank(ascending=False, method='min').astype(int)
    
    return store_stats


@router.post("/comparison/clear-cache")
async def clear_store_comparison_cache():
    """清除全量门店对比缓存"""
    invalidate_store_comparison_cache()
    return {"success": True, "message": "全量门店对比缓存已清除"}


@router.get("/comparison")
async def get_stores_comparison(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    sort_by: str = Query("revenue", description="排序字段: revenue, profit, profit_margin, order_count"),
    sort_order: str = Query("desc", description="排序方向: asc, desc"),
    channel: Optional[str] = Query(None, description="渠道筛选（可选，如：美团、饿了么、京东）"),
    use_aggregation: bool = Query(True, description="是否使用预聚合表（性能优化）")
) -> Dict[str, Any]:
    """
    全量门店对比分析
    
    返回所有门店的关键指标：
    - 订单量、销售额、利润、利润率
    - 单均配送费、单均营销费、客单价
    - 配送成本率、营销成本率
    - 异常标识（利润率异常、订单量异常等）
    
    渠道筛选规则（基于订单编号前缀）：
    - 美团 → SG 开头
    - 饿了么 → ELE 开头
    - 京东 → JD 开头
    
    优化点：
    - ✅ 优先使用预聚合表（查询时间从~500ms降到~2ms）
    - 平均利润率使用加权平均（总利润/总销售额）
    - SQL层面渠道筛选
    - 添加异常检测
    """
    import time
    query_start = time.time()
    
    # ✅ 优先使用预聚合表（性能优化）
    store_stats = None
    if use_aggregation and AGGREGATION_TABLE_AVAILABLE:
        store_stats = get_store_metrics_from_aggregation(start_date, end_date, channel)
        if not store_stats.empty:
            print(f"✅ [预聚合表] 查询耗时: {(time.time() - query_start)*1000:.1f}ms")
    
    # 如果预聚合表不可用或为空，回退到原始查询
    if store_stats is None or store_stats.empty:
        print(f"⚠️ 预聚合表不可用，使用原始查询...")
        df = get_all_stores_data(start_date, end_date, channel)
        
        if df.empty:
            return {
                "success": True,
                "data": {
                    "stores": [],
                    "summary": {
                        "total_stores": 0,
                        "total_orders": 0,
                        "total_revenue": 0,
                        "total_profit": 0,
                        "avg_profit_margin": 0,
                        "weighted_profit_margin": 0
                    }
                }
            }
        
        # 计算门店指标
        store_stats = calculate_store_metrics(df)
        print(f"⚠️ [原始查询] 查询耗时: {(time.time() - query_start)*1000:.1f}ms")
    
    if store_stats.empty:
        return {
            "success": True,
            "data": {
                "stores": [],
                "summary": {
                    "total_stores": 0,
                    "total_orders": 0,
                    "total_revenue": 0,
                    "total_profit": 0,
                    "avg_profit_margin": 0,
                    "weighted_profit_margin": 0
                }
            }
        }
    
    # 排序
    sort_col_map = {
        'revenue': 'total_revenue',
        'profit': 'total_profit',
        'profit_margin': 'profit_margin',
        'order_count': 'order_count'
    }
    sort_col = sort_col_map.get(sort_by, 'total_revenue')
    store_stats = store_stats.sort_values(sort_col, ascending=(sort_order == 'asc'))
    
    # ✅ 计算汇总数据（修复：使用加权平均利润率）
    total_revenue = float(store_stats['total_revenue'].sum())
    total_profit = float(store_stats['total_profit'].sum())
    weighted_profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    summary = {
        "total_stores": len(store_stats),
        "total_orders": int(store_stats['order_count'].sum()),
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "avg_profit_margin": round(weighted_profit_margin, 2),  # ✅ 修复：使用加权平均
        "weighted_profit_margin": round(weighted_profit_margin, 2)  # 显式字段
    }
    
    # ✅ 异常检测阈值
    avg_profit_margin = store_stats['profit_margin'].mean()
    std_profit_margin = store_stats['profit_margin'].std()
    avg_order_count = store_stats['order_count'].mean()
    std_order_count = store_stats['order_count'].std()
    
    # 转换为列表
    stores_list = []
    for _, row in store_stats.iterrows():
        # ✅ 异常检测
        anomalies = []
        
        # 利润率异常（低于平均值2个标准差）
        if std_profit_margin > 0 and row['profit_margin'] < avg_profit_margin - 2 * std_profit_margin:
            anomalies.append({
                "type": "low_profit_margin",
                "message": f"利润率({row['profit_margin']:.1f}%)显著低于平均水平({avg_profit_margin:.1f}%)",
                "severity": "high"
            })
        
        # 订单量异常（低于平均值2个标准差）
        if std_order_count > 0 and row['order_count'] < avg_order_count - 2 * std_order_count:
            anomalies.append({
                "type": "low_order_count",
                "message": f"订单量({row['order_count']})显著低于平均水平({avg_order_count:.0f})",
                "severity": "medium"
            })
        
        # 营销成本率过高（超过15%）
        if row['marketing_cost_rate'] > 15:
            anomalies.append({
                "type": "high_marketing_cost",
                "message": f"营销成本率({row['marketing_cost_rate']:.1f}%)过高，建议优化活动策略",
                "severity": "medium"
            })
        
        # 配送成本率过高（超过20%）
        if row['delivery_cost_rate'] > 20:
            anomalies.append({
                "type": "high_delivery_cost",
                "message": f"配送成本率({row['delivery_cost_rate']:.1f}%)过高，建议优化配送范围",
                "severity": "medium"
            })
        
        stores_list.append({
            "store_name": row['store_name'],
            "order_count": int(row['order_count']),
            "total_revenue": round(float(row['total_revenue']), 2),
            "total_profit": round(float(row['total_profit']), 2),
            "profit_margin": round(float(row['profit_margin']), 2),
            "aov": round(float(row['aov']), 2),
            "avg_delivery_fee": round(float(row['avg_delivery_fee']), 2),
            "avg_marketing_cost": round(float(row['avg_marketing_cost']), 2),
            "delivery_cost_rate": round(float(row['delivery_cost_rate']), 2),
            "marketing_cost_rate": round(float(row['marketing_cost_rate']), 2),
            "ranks": {
                "revenue_rank": int(row['revenue_rank']),
                "profit_rank": int(row['profit_rank']),
                "profit_margin_rank": int(row['profit_margin_rank'])
            },
            "anomalies": anomalies  # ✅ 异常检测
        })
    
    return {
        "success": True,
        "data": {
            "stores": stores_list,
            "summary": summary
        }
    }


@router.get("/comparison/week-over-week")
async def get_stores_week_over_week(
    end_date: Optional[date] = Query(None, description="本期结束日期（默认为数据最大日期）"),
    previous_start: Optional[date] = Query(None, description="上期开始日期（可选，用于自定义对比周期）"),
    previous_end: Optional[date] = Query(None, description="上期结束日期（可选，用于自定义对比周期）"),
    channel: Optional[str] = Query(None, description="渠道筛选（可选，如：美团、饿了么、京东）")
) -> Dict[str, Any]:
    """
    全量门店环比数据（支持自定义对比周期和渠道筛选）
    
    计算逻辑：
    - 如果提供 previous_start 和 previous_end，使用自定义上期
    - 否则，自动计算：本期=最近7天，上期=前7天
    - 如果提供 channel，根据订单编号前缀筛选该渠道的数据
    
    优化点：
    - SQL层面渠道筛选
    """
    # 如果没有指定结束日期，使用数据库中的最大日期
    if not end_date:
        session = SessionLocal()
        try:
            max_date_result = session.query(Order.date).order_by(Order.date.desc()).first()
            if max_date_result and max_date_result[0]:
                end_date = max_date_result[0].date()
            else:
                end_date = date.today()
        finally:
            session.close()
    
    # 计算本期日期范围
    this_week_end = end_date
    
    # 如果提供了自定义上期，使用自定义逻辑
    if previous_start and previous_end:
        # 使用自定义上期
        last_week_start = previous_start
        last_week_end = previous_end
        
        # 计算本期开始日期（根据上期天数）
        days = (previous_end - previous_start).days + 1
        this_week_start = this_week_end - timedelta(days=days - 1)
        
        print(f"📊 自定义环比: 本期 {this_week_start} ~ {this_week_end}, 上期 {last_week_start} ~ {last_week_end}")
    else:
        # 默认逻辑：最近7天 vs 前7天
        this_week_start = this_week_end - timedelta(days=6)
        last_week_end = this_week_start - timedelta(days=1)
        last_week_start = last_week_end - timedelta(days=6)
        
        print(f"📊 默认环比: 本期 {this_week_start} ~ {this_week_end}, 上期 {last_week_start} ~ {last_week_end}")
    
    # SQL层面渠道筛选
    this_week_df = get_all_stores_data(this_week_start, this_week_end, channel)
    last_week_df = get_all_stores_data(last_week_start, last_week_end, channel)
    
    # 计算本周指标
    this_week_stats = calculate_store_metrics(this_week_df) if not this_week_df.empty else pd.DataFrame()
    last_week_stats = calculate_store_metrics(last_week_df) if not last_week_df.empty else pd.DataFrame()
    
    if this_week_stats.empty:
        return {
            "success": True,
            "data": {
                "stores": [],
                "period": {
                    "current": {"start": str(this_week_start), "end": str(this_week_end)},
                    "previous": {"start": str(last_week_start), "end": str(last_week_end)}
                }
            }
        }
    
    # 合并数据计算环比
    result = []
    for _, current_row in this_week_stats.iterrows():
        store_name = current_row['store_name']
        
        # 查找上周数据
        prev_row = last_week_stats[last_week_stats['store_name'] == store_name]
        
        # 计算环比变化
        if not prev_row.empty:
            prev_row = prev_row.iloc[0]
            order_count_change = ((current_row['order_count'] - prev_row['order_count']) / prev_row['order_count'] * 100) if prev_row['order_count'] > 0 else 0
            revenue_change = ((current_row['total_revenue'] - prev_row['total_revenue']) / prev_row['total_revenue'] * 100) if prev_row['total_revenue'] > 0 else 0
            profit_change = ((current_row['total_profit'] - prev_row['total_profit']) / prev_row['total_profit'] * 100) if prev_row['total_profit'] != 0 else 0
            profit_margin_change = current_row['profit_margin'] - prev_row['profit_margin']
            aov_change = ((current_row['aov'] - prev_row['aov']) / prev_row['aov'] * 100) if prev_row['aov'] > 0 else 0
            avg_delivery_fee_change = ((current_row['avg_delivery_fee'] - prev_row['avg_delivery_fee']) / prev_row['avg_delivery_fee'] * 100) if prev_row['avg_delivery_fee'] > 0 else 0
            avg_marketing_cost_change = ((current_row['avg_marketing_cost'] - prev_row['avg_marketing_cost']) / prev_row['avg_marketing_cost'] * 100) if prev_row['avg_marketing_cost'] > 0 else 0
            delivery_cost_rate_change = current_row['delivery_cost_rate'] - prev_row['delivery_cost_rate']
            marketing_cost_rate_change = current_row['marketing_cost_rate'] - prev_row['marketing_cost_rate']
        else:
            order_count_change = revenue_change = profit_change = profit_margin_change = 0
            aov_change = avg_delivery_fee_change = avg_marketing_cost_change = 0
            delivery_cost_rate_change = marketing_cost_rate_change = 0
        
        store_data = {
            "store_name": store_name,
            "current": {
                "order_count": int(current_row['order_count']),
                "total_revenue": round(float(current_row['total_revenue']), 2),
                "total_profit": round(float(current_row['total_profit']), 2),
                "profit_margin": round(float(current_row['profit_margin']), 2),
                "aov": round(float(current_row['aov']), 2),
                "avg_delivery_fee": round(float(current_row['avg_delivery_fee']), 2),
                "avg_marketing_cost": round(float(current_row['avg_marketing_cost']), 2),
                "delivery_cost_rate": round(float(current_row['delivery_cost_rate']), 2),
                "marketing_cost_rate": round(float(current_row['marketing_cost_rate']), 2)
            },
            "changes": {
                "order_count": round(float(order_count_change), 2),
                "revenue": round(float(revenue_change), 2),
                "profit": round(float(profit_change), 2),
                "profit_margin": round(float(profit_margin_change), 2),
                "aov": round(float(aov_change), 2),
                "avg_delivery_fee": round(float(avg_delivery_fee_change), 2),
                "avg_marketing_cost": round(float(avg_marketing_cost_change), 2),
                "delivery_cost_rate": round(float(delivery_cost_rate_change), 2),
                "marketing_cost_rate": round(float(marketing_cost_rate_change), 2)
            }
        }
        
        result.append(store_data)
    
    return {
        "success": True,
        "data": {
            "stores": result,
            "period": {
                "current": {"start": str(this_week_start), "end": str(this_week_end)},
                "previous": {"start": str(last_week_start), "end": str(last_week_end)}
            }
        }
    }


@router.get("/comparison/ranking")
async def get_stores_ranking(
    metric: str = Query("revenue", description="排名指标: revenue, profit, profit_margin, order_count"),
    limit: int = Query(10, ge=1, le=50, description="返回Top N"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    门店排行榜（Top N）
    """
    # 加载数据
    df = get_all_stores_data(start_date, end_date)
    
    if df.empty:
        return {"success": True, "data": []}
    
    # 计算门店指标
    store_stats = calculate_store_metrics(df)
    
    if store_stats.empty:
        return {"success": True, "data": []}
    
    # 排序
    sort_col_map = {
        'revenue': 'total_revenue',
        'profit': 'total_profit',
        'profit_margin': 'profit_margin',
        'order_count': 'order_count'
    }
    sort_col = sort_col_map.get(metric, 'total_revenue')
    store_stats = store_stats.sort_values(sort_col, ascending=False).head(limit)
    
    # 转换为列表
    result = []
    for idx, row in enumerate(store_stats.iterrows(), 1):
        _, row = row
        result.append({
            "rank": idx,
            "store_name": row['store_name'],
            "value": round(float(row[sort_col]), 2),
            "order_count": int(row['order_count']),
            "total_revenue": round(float(row['total_revenue']), 2),
            "total_profit": round(float(row['total_profit']), 2),
            "profit_margin": round(float(row['profit_margin']), 2)
        })
    
    return {"success": True, "data": result}


@router.get("/comparison/available-channels")
async def get_available_channels(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    获取当前日期范围内有数据的渠道列表
    
    只返回在指定日期范围内有订单数据的渠道
    渠道识别规则（基于订单编号前缀）：
    - SG 开头 → 美团
    - ELE 开头 → 饿了么
    - JD 开头 → 京东
    """
    # 定义支持的渠道及其订单编号前缀
    CHANNEL_PREFIXES = {
        '美团': 'SG',
        '饿了么': 'ELE',
        '京东': 'JD'
    }
    
    # 从数据库查询有数据的渠道
    session = SessionLocal()
    try:
        query = session.query(Order.order_number)
        
        if start_date:
            query = query.filter(Order.date >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(Order.date <= datetime.combine(end_date, datetime.max.time()))
        
        # 获取所有订单编号
        order_numbers = [r[0] for r in query.distinct().all() if r[0]]
        
        if not order_numbers:
            return {"success": True, "data": []}
        
        # 根据订单编号前缀识别有数据的渠道
        available_channels = []
        for channel_name, prefix in CHANNEL_PREFIXES.items():
            # 检查是否有该前缀的订单
            has_orders = any(str(on).startswith(prefix) for on in order_numbers)
            if has_orders:
                available_channels.append(channel_name)
        
        print(f"✅ 可用渠道列表: {available_channels} (日期: {start_date} ~ {end_date})")
        
        return {"success": True, "data": sorted(available_channels)}
    finally:
        session.close()


@router.get("/comparison/export")
async def export_stores_comparison(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    channel: Optional[str] = Query(None, description="渠道筛选"),
    format: str = Query("json", description="导出格式: json, csv")
) -> Dict[str, Any]:
    """
    导出门店对比数据
    
    支持 JSON 和 CSV 格式导出
    """
    from fastapi.responses import Response
    import io
    import csv
    
    # 获取数据
    df = get_all_stores_data(start_date, end_date, channel)
    
    if df.empty:
        return {"success": False, "error": "无数据可导出"}
    
    store_stats = calculate_store_metrics(df)
    
    if store_stats.empty:
        return {"success": False, "error": "无数据可导出"}
    
    # 准备导出数据
    export_data = []
    for _, row in store_stats.iterrows():
        export_data.append({
            "门店名称": row['store_name'],
            "订单量": int(row['order_count']),
            "销售额": round(float(row['total_revenue']), 2),
            "利润": round(float(row['total_profit']), 2),
            "利润率(%)": round(float(row['profit_margin']), 2),
            "客单价": round(float(row['aov']), 2),
            "单均配送费": round(float(row['avg_delivery_fee']), 2),
            "单均营销费": round(float(row['avg_marketing_cost']), 2),
            "配送成本率(%)": round(float(row['delivery_cost_rate']), 2),
            "营销成本率(%)": round(float(row['marketing_cost_rate']), 2),
            "销售额排名": int(row['revenue_rank']),
            "利润排名": int(row['profit_rank']),
            "利润率排名": int(row['profit_margin_rank'])
        })
    
    if format == "csv":
        # 生成CSV
        output = io.StringIO()
        if export_data:
            writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
            writer.writeheader()
            writer.writerows(export_data)
        
        return {
            "success": True,
            "data": {
                "format": "csv",
                "content": output.getvalue(),
                "filename": f"门店对比数据_{start_date or 'all'}_{end_date or 'all'}.csv"
            }
        }
    else:
        # JSON格式
        return {
            "success": True,
            "data": {
                "format": "json",
                "content": export_data,
                "filename": f"门店对比数据_{start_date or 'all'}_{end_date or 'all'}.json",
                "summary": {
                    "total_stores": len(export_data),
                    "date_range": f"{start_date or '全部'} ~ {end_date or '全部'}",
                    "channel": channel or "全部渠道"
                }
            }
        }


@router.get("/comparison/stores-by-channel")
async def get_stores_by_channel(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    channel: Optional[str] = Query(None, description="渠道筛选")
) -> Dict[str, Any]:
    """
    获取指定渠道下的门店列表
    
    用于渠道筛选后更新门店筛选器
    """
    df = get_all_stores_data(start_date, end_date, channel)
    
    if df.empty or '门店名称' not in df.columns:
        return {"success": True, "data": []}
    
    store_names = sorted(df['门店名称'].dropna().unique().tolist())
    
    return {
        "success": True,
        "data": store_names,
        "count": len(store_names)
    }


# ==================== 全局门店洞察分析引擎 ====================

class InsightsEngine:
    """
    全局门店洞察分析引擎
    
    提供基于规则的统计分析，生成结构化的洞察报告
    """
    
    def __init__(self, stores_data: pd.DataFrame, week_over_week_data: List[Dict] = None):
        """
        初始化洞察引擎
        
        Args:
            stores_data: 门店指标DataFrame
            week_over_week_data: 环比数据列表
        """
        self.stores = stores_data
        self.wow_data = week_over_week_data or []
        
    def calculate_statistics(self) -> Dict:
        """计算描述性统计"""
        if self.stores.empty:
            return self._empty_statistics()
        
        def calc_stats(series):
            return {
                'mean': round(float(series.mean()), 2),
                'median': round(float(series.median()), 2),
                'std': round(float(series.std()), 2),
                'p25': round(float(np.percentile(series, 25)), 2),
                'p50': round(float(np.percentile(series, 50)), 2),
                'p75': round(float(np.percentile(series, 75)), 2),
                'p90': round(float(np.percentile(series, 90)), 2)
            }
        
        return {
            'profit_margin': calc_stats(self.stores['profit_margin']),
            'aov': calc_stats(self.stores['aov']),
            'order_count': calc_stats(self.stores['order_count'])
        }
    
    def _empty_statistics(self) -> Dict:
        empty = {'mean': 0, 'median': 0, 'std': 0, 'p25': 0, 'p50': 0, 'p75': 0, 'p90': 0}
        return {'profit_margin': empty, 'aov': empty, 'order_count': empty}

    def cluster_stores(self) -> Dict:
        """门店分群分析（基于利润率分位数）"""
        if self.stores.empty:
            return self._empty_clustering()
        
        profit_margins = self.stores['profit_margin'].values
        p25 = np.percentile(profit_margins, 25)
        p75 = np.percentile(profit_margins, 75)
        
        high = self.stores[self.stores['profit_margin'] >= p75]
        medium = self.stores[(self.stores['profit_margin'] >= p25) & (self.stores['profit_margin'] < p75)]
        low = self.stores[self.stores['profit_margin'] < p25]
        
        def group_stats(group_df):
            if group_df.empty:
                return {
                    'count': 0, 'percentage': 0,
                    'avg_metrics': {'revenue': 0, 'profit': 0, 'profit_margin': 0, 'aov': 0},
                    'top_stores': [], 'characteristics': ''
                }
            return {
                'count': len(group_df),
                'percentage': round(len(group_df) / len(self.stores) * 100, 1),
                'avg_metrics': {
                    'revenue': round(float(group_df['total_revenue'].mean()), 2),
                    'profit': round(float(group_df['total_profit'].mean()), 2),
                    'profit_margin': round(float(group_df['profit_margin'].mean()), 2),
                    'aov': round(float(group_df['aov'].mean()), 2)
                },
                'top_stores': group_df.nlargest(3, 'total_profit')['store_name'].tolist(),
                'characteristics': ''
            }
        
        result = {
            'high_performance': group_stats(high),
            'medium_performance': group_stats(medium),
            'low_performance': group_stats(low)
        }
        
        # 生成特征描述
        result['high_performance']['characteristics'] = self._gen_cluster_char('high', result['high_performance'])
        result['medium_performance']['characteristics'] = self._gen_cluster_char('medium', result['medium_performance'])
        result['low_performance']['characteristics'] = self._gen_cluster_char('low', result['low_performance'])
        result['summary_text'] = self._gen_clustering_summary(result)
        
        return result

    def _gen_cluster_char(self, level: str, group: Dict) -> str:
        if group['count'] == 0:
            return "无门店"
        metrics = group['avg_metrics']
        if level == 'high':
            return f"平均利润率{metrics['profit_margin']:.1f}%，客单价¥{metrics['aov']:.1f}，盈利能力强"
        elif level == 'medium':
            return f"平均利润率{metrics['profit_margin']:.1f}%，客单价¥{metrics['aov']:.1f}，有提升空间"
        else:
            return f"平均利润率{metrics['profit_margin']:.1f}%，客单价¥{metrics['aov']:.1f}，需重点关注"
    
    def _gen_clustering_summary(self, result: Dict) -> str:
        high = result['high_performance']
        low = result['low_performance']
        return f"""🎯 门店分群分析

根据利润率将门店分为三个层级：

【高绩效门店】{high['count']}家（占比{high['percentage']:.1f}%）
{high['characteristics']}
代表门店：{', '.join(high['top_stores'][:3]) if high['top_stores'] else '无'}

【中等门店】{result['medium_performance']['count']}家（占比{result['medium_performance']['percentage']:.1f}%）
{result['medium_performance']['characteristics']}

【低绩效门店】{low['count']}家（占比{low['percentage']:.1f}%）
{low['characteristics']}
代表门店：{', '.join(low['top_stores'][:3]) if low['top_stores'] else '无'}

💡 建议：重点关注低绩效门店，分析其成本结构和运营问题。"""
    
    def _empty_clustering(self) -> Dict:
        empty_group = {'count': 0, 'percentage': 0, 'avg_metrics': {'revenue': 0, 'profit': 0, 'profit_margin': 0, 'aov': 0}, 'top_stores': [], 'characteristics': ''}
        return {'high_performance': empty_group, 'medium_performance': empty_group, 'low_performance': empty_group, 'summary_text': '暂无数据'}

    def detect_anomalies(self) -> Dict:
        """异常门店检测"""
        if self.stores.empty:
            return self._empty_anomalies()
        
        anomalies = {'low_profit_margin': [], 'low_order_count': [], 'high_marketing_cost': [], 'high_delivery_cost': []}
        
        # Z-score检测利润率异常
        pm_mean = self.stores['profit_margin'].mean()
        pm_std = self.stores['profit_margin'].std()
        if pm_std > 0:
            for _, row in self.stores.iterrows():
                z = (row['profit_margin'] - pm_mean) / pm_std
                if z < -2:
                    anomalies['low_profit_margin'].append({
                        'store_name': row['store_name'],
                        'value': round(row['profit_margin'], 2),
                        'threshold': round(pm_mean - 2 * pm_std, 2),
                        'severity': 'high' if z < -3 else 'medium',
                        'message': f"利润率{row['profit_margin']:.1f}%显著低于平均值{pm_mean:.1f}%"
                    })
        
        # IQR检测订单量异常
        oc_q1 = np.percentile(self.stores['order_count'], 25)
        oc_q3 = np.percentile(self.stores['order_count'], 75)
        oc_iqr = oc_q3 - oc_q1
        oc_lower = oc_q1 - 1.5 * oc_iqr
        for _, row in self.stores.iterrows():
            if row['order_count'] < oc_lower:
                anomalies['low_order_count'].append({
                    'store_name': row['store_name'],
                    'value': int(row['order_count']),
                    'threshold': int(oc_lower),
                    'severity': 'medium',
                    'message': f"订单量{int(row['order_count'])}显著低于正常范围"
                })
        
        # 阈值检测营销成本率（>15%）
        for _, row in self.stores.iterrows():
            if row['marketing_cost_rate'] > 15:
                anomalies['high_marketing_cost'].append({
                    'store_name': row['store_name'],
                    'value': round(row['marketing_cost_rate'], 2),
                    'threshold': 15,
                    'severity': 'high' if row['marketing_cost_rate'] > 20 else 'medium',
                    'message': f"营销成本率{row['marketing_cost_rate']:.1f}%过高"
                })
        
        # 阈值检测配送成本率（>20%）
        for _, row in self.stores.iterrows():
            if row['delivery_cost_rate'] > 20:
                anomalies['high_delivery_cost'].append({
                    'store_name': row['store_name'],
                    'value': round(row['delivery_cost_rate'], 2),
                    'threshold': 20,
                    'severity': 'high' if row['delivery_cost_rate'] > 25 else 'medium',
                    'message': f"配送成本率{row['delivery_cost_rate']:.1f}%过高"
                })
        
        total = len(set(a['store_name'] for t in anomalies.values() for a in t))
        return {
            'total_anomaly_stores': total,
            'by_type': anomalies,
            'summary_text': self._gen_anomaly_summary(anomalies, total)
        }

    def _gen_anomaly_summary(self, anomalies: Dict, total: int) -> str:
        if total == 0:
            return "✅ 异常检测\n\n所有门店运营指标正常，未发现显著异常。"
        
        lines = [f"⚠️ 异常检测\n\n共发现 {total} 家门店存在异常情况：\n"]
        
        if anomalies['low_profit_margin']:
            lines.append(f"🔴 利润率异常：{len(anomalies['low_profit_margin'])}家")
            for a in anomalies['low_profit_margin'][:3]:
                lines.append(f"   - {a['store_name']}: {a['message']}")
        
        if anomalies['low_order_count']:
            lines.append(f"🟠 订单量异常：{len(anomalies['low_order_count'])}家")
            for a in anomalies['low_order_count'][:3]:
                lines.append(f"   - {a['store_name']}: {a['message']}")
        
        if anomalies['high_marketing_cost']:
            lines.append(f"🟡 营销成本过高：{len(anomalies['high_marketing_cost'])}家")
            for a in anomalies['high_marketing_cost'][:3]:
                lines.append(f"   - {a['store_name']}: {a['message']}")
        
        if anomalies['high_delivery_cost']:
            lines.append(f"🟡 配送成本过高：{len(anomalies['high_delivery_cost'])}家")
            for a in anomalies['high_delivery_cost'][:3]:
                lines.append(f"   - {a['store_name']}: {a['message']}")
        
        lines.append("\n💡 建议：优先处理高严重度异常，逐一排查问题根因。")
        return '\n'.join(lines)
    
    def _empty_anomalies(self) -> Dict:
        return {'total_anomaly_stores': 0, 'by_type': {'low_profit_margin': [], 'low_order_count': [], 'high_marketing_cost': [], 'high_delivery_cost': []}, 'summary_text': '暂无数据'}

    def compare_head_tail(self, n: int = 3) -> Dict:
        """头尾门店对比分析"""
        if self.stores.empty or len(self.stores) < 2:
            return self._empty_head_tail()
        
        sorted_stores = self.stores.sort_values('profit_margin', ascending=False)
        top = sorted_stores.head(n)
        bottom = sorted_stores.tail(n)
        
        def store_metrics(row):
            return {
                'store_name': row['store_name'],
                'order_count': int(row['order_count']),
                'total_revenue': round(float(row['total_revenue']), 2),
                'total_profit': round(float(row['total_profit']), 2),
                'profit_margin': round(float(row['profit_margin']), 2),
                'aov': round(float(row['aov']), 2),
                'marketing_cost_rate': round(float(row['marketing_cost_rate']), 2),
                'delivery_cost_rate': round(float(row['delivery_cost_rate']), 2)
            }
        
        top_list = [store_metrics(row) for _, row in top.iterrows()]
        bottom_list = [store_metrics(row) for _, row in bottom.iterrows()]
        
        # 计算差异
        top_avg = lambda f: top[f].mean()
        bottom_avg = lambda f: bottom[f].mean()
        
        differences = {
            'profit_margin_gap': round(top_avg('profit_margin') - bottom_avg('profit_margin'), 2),
            'aov_gap': round(top_avg('aov') - bottom_avg('aov'), 2),
            'marketing_cost_rate_gap': round(top_avg('marketing_cost_rate') - bottom_avg('marketing_cost_rate'), 2),
            'delivery_cost_rate_gap': round(top_avg('delivery_cost_rate') - bottom_avg('delivery_cost_rate'), 2)
        }
        
        # 分析特征
        top_char = self._analyze_top_characteristics(top)
        bottom_issues = self._analyze_bottom_issues(bottom)
        
        return {
            'top_stores': top_list,
            'bottom_stores': bottom_list,
            'differences': differences,
            'top_characteristics': top_char,
            'bottom_issues': bottom_issues,
            'summary_text': self._gen_head_tail_summary(top_list, bottom_list, differences, top_char, bottom_issues)
        }

    def _analyze_top_characteristics(self, top_df: pd.DataFrame) -> str:
        if top_df.empty:
            return "无数据"
        avg_pm = top_df['profit_margin'].mean()
        avg_aov = top_df['aov'].mean()
        avg_mc = top_df['marketing_cost_rate'].mean()
        avg_dc = top_df['delivery_cost_rate'].mean()
        chars = []
        if avg_pm > 25:
            chars.append("利润率优秀")
        if avg_aov > self.stores['aov'].median():
            chars.append("客单价较高")
        if avg_mc < 10:
            chars.append("营销成本控制良好")
        if avg_dc < 15:
            chars.append("配送成本控制良好")
        return '、'.join(chars) if chars else "综合表现均衡"
    
    def _analyze_bottom_issues(self, bottom_df: pd.DataFrame) -> str:
        if bottom_df.empty:
            return "无数据"
        avg_pm = bottom_df['profit_margin'].mean()
        avg_mc = bottom_df['marketing_cost_rate'].mean()
        avg_dc = bottom_df['delivery_cost_rate'].mean()
        issues = []
        if avg_pm < 15:
            issues.append("利润率偏低")
        if avg_mc > 15:
            issues.append("营销成本过高")
        if avg_dc > 20:
            issues.append("配送成本过高")
        return '、'.join(issues) if issues else "需进一步分析"
    
    def _gen_head_tail_summary(self, top, bottom, diff, top_char, bottom_issues) -> str:
        return f"""🔄 头尾门店对比

【头部门店 Top3】
{chr(10).join([f"  {i+1}. {s['store_name']}: 利润率{s['profit_margin']:.1f}%, 客单价¥{s['aov']:.1f}" for i, s in enumerate(top)])}
共同特征：{top_char}

【尾部门店 Bottom3】
{chr(10).join([f"  {i+1}. {s['store_name']}: 利润率{s['profit_margin']:.1f}%, 客单价¥{s['aov']:.1f}" for i, s in enumerate(bottom)])}
主要问题：{bottom_issues}

【差距分析】
- 利润率差距：{diff['profit_margin_gap']:.1f}个百分点
- 客单价差距：¥{diff['aov_gap']:.1f}
- 营销成本率差距：{diff['marketing_cost_rate_gap']:.1f}个百分点
- 配送成本率差距：{diff['delivery_cost_rate_gap']:.1f}个百分点

💡 建议：学习头部门店的成功经验，针对尾部门店的问题制定改进方案。"""
    
    def _empty_head_tail(self) -> Dict:
        return {'top_stores': [], 'bottom_stores': [], 'differences': {'profit_margin_gap': 0, 'aov_gap': 0, 'marketing_cost_rate_gap': 0, 'delivery_cost_rate_gap': 0}, 'top_characteristics': '', 'bottom_issues': '', 'summary_text': '暂无数据'}

    def analyze_attribution(self) -> Dict:
        """利润率归因分析（相关性分析）"""
        if self.stores.empty or len(self.stores) < 3:
            return self._empty_attribution()
        
        pm = self.stores['profit_margin'].values
        aov = self.stores['aov'].values
        mc = self.stores['marketing_cost_rate'].values
        dc = self.stores['delivery_cost_rate'].values
        
        # 计算相关系数
        def safe_corr(a, b):
            if len(a) < 2 or np.std(a) == 0 or np.std(b) == 0:
                return 0
            return round(float(np.corrcoef(a, b)[0, 1]), 3)
        
        correlations = {
            'aov_correlation': safe_corr(pm, aov),
            'marketing_cost_correlation': safe_corr(pm, mc),
            'delivery_cost_correlation': safe_corr(pm, dc)
        }
        
        # 识别主要影响因素
        factors = [
            ('客单价', correlations['aov_correlation'], '正相关' if correlations['aov_correlation'] > 0 else '负相关'),
            ('营销成本率', correlations['marketing_cost_correlation'], '正相关' if correlations['marketing_cost_correlation'] > 0 else '负相关'),
            ('配送成本率', correlations['delivery_cost_correlation'], '正相关' if correlations['delivery_cost_correlation'] > 0 else '负相关')
        ]
        factors.sort(key=lambda x: abs(x[1]), reverse=True)
        primary = factors[0]
        
        return {
            'correlations': correlations,
            'primary_factor': primary[0],
            'summary_text': self._gen_attribution_summary(correlations, primary)
        }
    
    def _gen_attribution_summary(self, corr, primary) -> str:
        return f"""📈 利润率归因分析

通过相关性分析，识别影响门店利润率的关键因素：

【相关系数】
- 客单价 vs 利润率：{corr['aov_correlation']:.3f} {'（正相关）' if corr['aov_correlation'] > 0 else '（负相关）'}
- 营销成本率 vs 利润率：{corr['marketing_cost_correlation']:.3f} {'（正相关）' if corr['marketing_cost_correlation'] > 0 else '（负相关）'}
- 配送成本率 vs 利润率：{corr['delivery_cost_correlation']:.3f} {'（正相关）' if corr['delivery_cost_correlation'] > 0 else '（负相关）'}

【主要影响因素】
{primary[0]}是影响利润率的最主要因素（相关系数{primary[1]:.3f}）

💡 建议：
- 若客单价正相关强，可通过提升客单价来改善利润
- 若成本率负相关强，应重点控制相应成本"""
    
    def _empty_attribution(self) -> Dict:
        return {'correlations': {'aov_correlation': 0, 'marketing_cost_correlation': 0, 'delivery_cost_correlation': 0}, 'primary_factor': '', 'summary_text': '数据不足，无法进行归因分析'}

    def analyze_trends(self) -> Dict:
        """趋势变化分析（基于环比数据）"""
        if not self.wow_data:
            return self._empty_trends()
        
        growing = []
        declining = []
        
        for store in self.wow_data:
            change = store.get('changes', {}).get('profit', 0)
            if change > 0:
                growing.append({
                    'store_name': store['store_name'],
                    'change_rate': round(change, 2),
                    'current_value': store.get('current', {}).get('total_profit', 0),
                    'previous_value': store.get('current', {}).get('total_profit', 0) / (1 + change/100) if change != -100 else 0
                })
            elif change < 0:
                declining.append({
                    'store_name': store['store_name'],
                    'change_rate': round(change, 2),
                    'current_value': store.get('current', {}).get('total_profit', 0),
                    'previous_value': store.get('current', {}).get('total_profit', 0) / (1 + change/100) if change != -100 else 0
                })
        
        growing.sort(key=lambda x: x['change_rate'], reverse=True)
        declining.sort(key=lambda x: x['change_rate'])
        
        total = len(self.wow_data)
        return {
            'growing_stores': {
                'count': len(growing),
                'percentage': round(len(growing) / total * 100, 1) if total > 0 else 0,
                'top3': growing[:3]
            },
            'declining_stores': {
                'count': len(declining),
                'percentage': round(len(declining) / total * 100, 1) if total > 0 else 0,
                'top3': declining[:3]
            },
            'summary_text': self._gen_trends_summary(growing, declining, total)
        }
    
    def _gen_trends_summary(self, growing, declining, total) -> str:
        if total == 0:
            return "📉 趋势分析\n\n暂无环比数据"
        
        lines = [f"📉 趋势变化分析\n\n共{total}家门店参与环比分析：\n"]
        
        lines.append(f"【增长门店】{len(growing)}家（占比{len(growing)/total*100:.1f}%）")
        if growing:
            for s in growing[:3]:
                lines.append(f"  ↑ {s['store_name']}: +{s['change_rate']:.1f}%")
        
        lines.append(f"\n【下滑门店】{len(declining)}家（占比{len(declining)/total*100:.1f}%）")
        if declining:
            for s in declining[:3]:
                lines.append(f"  ↓ {s['store_name']}: {s['change_rate']:.1f}%")
        
        lines.append("\n💡 建议：关注下滑门店，分析下滑原因并及时干预。")
        return '\n'.join(lines)
    
    def _empty_trends(self) -> Dict:
        return {'growing_stores': {'count': 0, 'percentage': 0, 'top3': []}, 'declining_stores': {'count': 0, 'percentage': 0, 'top3': []}, 'summary_text': '暂无环比数据'}

    def generate_recommendations(self, anomalies: Dict, clustering: Dict, attribution: Dict, trends: Dict) -> Dict:
        """生成策略建议"""
        urgent = []
        important = []
        general = []
        
        # 基于异常检测生成紧急建议
        if anomalies['by_type']['low_profit_margin']:
            stores = [a['store_name'] for a in anomalies['by_type']['low_profit_margin']]
            urgent.append({
                'priority': 'urgent',
                'category': '利润异常',
                'title': '利润率异常门店需紧急关注',
                'description': f"发现{len(stores)}家门店利润率显著低于平均水平，需立即排查原因",
                'action_items': ['检查商品定价是否合理', '分析成本结构', '核实是否存在异常订单'],
                'affected_stores': stores[:5]
            })
        
        if anomalies['by_type']['high_marketing_cost']:
            stores = [a['store_name'] for a in anomalies['by_type']['high_marketing_cost']]
            important.append({
                'priority': 'important',
                'category': '成本控制',
                'title': '营销成本过高需优化',
                'description': f"{len(stores)}家门店营销成本率超过15%，建议优化活动策略",
                'action_items': ['评估活动ROI', '减少低效促销', '优化优惠券发放策略'],
                'affected_stores': stores[:5]
            })
        
        if anomalies['by_type']['high_delivery_cost']:
            stores = [a['store_name'] for a in anomalies['by_type']['high_delivery_cost']]
            important.append({
                'priority': 'important',
                'category': '成本控制',
                'title': '配送成本过高需优化',
                'description': f"{len(stores)}家门店配送成本率超过20%，建议优化配送范围",
                'action_items': ['调整配送范围', '优化起送金额', '考虑自配送方案'],
                'affected_stores': stores[:5]
            })
        
        # 基于分群生成建议
        if clustering['low_performance']['count'] > 0:
            stores = clustering['low_performance']['top_stores']
            general.append({
                'priority': 'general',
                'category': '门店提升',
                'title': '低绩效门店提升计划',
                'description': f"{clustering['low_performance']['count']}家门店处于低绩效区间，建议制定提升计划",
                'action_items': ['对标高绩效门店', '分析差距原因', '制定改进措施'],
                'affected_stores': stores[:5]
            })
        
        # 基于归因分析生成建议
        if attribution['primary_factor'] == '客单价' and attribution['correlations']['aov_correlation'] > 0.3:
            general.append({
                'priority': 'general',
                'category': '收入提升',
                'title': '提升客单价策略',
                'description': '客单价与利润率强正相关，建议通过提升客单价来改善利润',
                'action_items': ['优化商品组合', '设置满减门槛', '推广高毛利商品'],
                'affected_stores': []
            })
        
        return {
            'urgent': urgent,
            'important': important,
            'general': general,
            'summary_text': self._gen_recommendations_summary(urgent, important, general)
        }

    def _gen_recommendations_summary(self, urgent, important, general) -> str:
        total = len(urgent) + len(important) + len(general)
        if total == 0:
            return "💡 策略建议\n\n当前运营状况良好，暂无特别建议。"
        
        lines = [f"💡 策略建议\n\n共生成{total}条建议：\n"]
        
        if urgent:
            lines.append(f"🔴 紧急（{len(urgent)}条）")
            for r in urgent:
                lines.append(f"  • {r['title']}")
        
        if important:
            lines.append(f"\n🟠 重要（{len(important)}条）")
            for r in important:
                lines.append(f"  • {r['title']}")
        
        if general:
            lines.append(f"\n🟢 一般（{len(general)}条）")
            for r in general:
                lines.append(f"  • {r['title']}")
        
        return '\n'.join(lines)
    
    def generate_overview(self) -> Dict:
        """生成整体概况"""
        if self.stores.empty:
            return self._empty_overview()
        
        total_revenue = float(self.stores['total_revenue'].sum())
        total_profit = float(self.stores['total_profit'].sum())
        weighted_pm = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        stats = self.calculate_statistics()
        
        overview = {
            'total_stores': len(self.stores),
            'total_orders': int(self.stores['order_count'].sum()),
            'total_revenue': round(total_revenue, 2),
            'total_profit': round(total_profit, 2),
            'weighted_profit_margin': round(weighted_pm, 2),
            'statistics': stats,
            'summary_text': self._gen_overview_summary(len(self.stores), int(self.stores['order_count'].sum()), total_revenue, total_profit, weighted_pm, stats)
        }
        return overview
    
    def _gen_overview_summary(self, stores, orders, revenue, profit, pm, stats) -> str:
        health = "✅ 整体经营状况良好" if pm >= 25 else ("⚠️ 整体经营状况一般" if pm >= 15 else "🔴 整体利润率偏低")
        return f"""📊 整体经营概况

当前共有 {stores} 家门店参与分析，累计完成 {orders:,} 笔订单，
实现销售额 ¥{revenue:,.0f}，总利润 ¥{profit:,.0f}。

加权平均利润率为 {pm:.1f}%，利润率中位数为 {stats['profit_margin']['median']:.1f}%。

【利润率分布】
- P25（低于75%门店）: {stats['profit_margin']['p25']:.1f}%
- P50（中位数）: {stats['profit_margin']['p50']:.1f}%
- P75（高于75%门店）: {stats['profit_margin']['p75']:.1f}%
- P90（头部10%门店）: {stats['profit_margin']['p90']:.1f}%

{health}"""
    
    def _empty_overview(self) -> Dict:
        return {'total_stores': 0, 'total_orders': 0, 'total_revenue': 0, 'total_profit': 0, 'weighted_profit_margin': 0, 'statistics': self._empty_statistics(), 'summary_text': '暂无数据'}

    def calculate_health_scores(self) -> Dict:
        """
        门店健康度评分（0-100分）
        
        评分维度及权重：
        - 利润率得分（40%）：基于利润率分位数
        - 订单量得分（20%）：基于订单量分位数
        - 营销成本率得分（20%）：成本率越低得分越高
        - 配送成本率得分（20%）：成本率越低得分越高
        """
        if self.stores.empty:
            return self._empty_health_scores()
        
        scores = []
        for _, row in self.stores.iterrows():
            # 利润率得分（0-100，基于分位数）
            pm_percentile = (self.stores['profit_margin'] <= row['profit_margin']).mean() * 100
            pm_score = pm_percentile * 0.4
            
            # 订单量得分（0-100，基于分位数）
            oc_percentile = (self.stores['order_count'] <= row['order_count']).mean() * 100
            oc_score = oc_percentile * 0.2
            
            # 营销成本率得分（越低越好，15%以下满分，30%以上0分）
            mc_rate = row['marketing_cost_rate']
            mc_score = max(0, min(100, (30 - mc_rate) / 15 * 100)) * 0.2
            
            # 配送成本率得分（越低越好，10%以下满分，30%以上0分）
            dc_rate = row['delivery_cost_rate']
            dc_score = max(0, min(100, (30 - dc_rate) / 20 * 100)) * 0.2
            
            total_score = pm_score + oc_score + mc_score + dc_score
            scores.append({
                'store_name': row['store_name'],
                'health_score': round(total_score, 1),
                'pm_score': round(pm_score / 0.4, 1),
                'oc_score': round(oc_score / 0.2, 1),
                'mc_score': round(mc_score / 0.2, 1),
                'dc_score': round(dc_score / 0.2, 1)
            })
        
        scores.sort(key=lambda x: x['health_score'], reverse=True)
        
        # 分布统计
        excellent = len([s for s in scores if s['health_score'] >= 80])
        good = len([s for s in scores if 60 <= s['health_score'] < 80])
        average = len([s for s in scores if 40 <= s['health_score'] < 60])
        poor = len([s for s in scores if s['health_score'] < 40])
        
        return {
            'scores': scores,
            'distribution': {
                'excellent': {'count': excellent, 'percentage': round(excellent / len(scores) * 100, 1)},
                'good': {'count': good, 'percentage': round(good / len(scores) * 100, 1)},
                'average': {'count': average, 'percentage': round(average / len(scores) * 100, 1)},
                'poor': {'count': poor, 'percentage': round(poor / len(scores) * 100, 1)}
            },
            'top_stores': scores[:3],
            'bottom_stores': scores[-3:] if len(scores) >= 3 else scores,
            'avg_score': round(sum(s['health_score'] for s in scores) / len(scores), 1),
            'summary_text': self._gen_health_summary(scores, excellent, good, average, poor)
        }
    
    def _gen_health_summary(self, scores, excellent, good, average, poor) -> str:
        total = len(scores)
        avg = sum(s['health_score'] for s in scores) / total
        return f"""🏥 门店健康度评分

基于利润率(40%)、订单量(20%)、营销成本率(20%)、配送成本率(20%)综合评分：

【健康度分布】
- 🟢 优秀（≥80分）：{excellent}家（{excellent/total*100:.1f}%）
- 🔵 良好（60-80分）：{good}家（{good/total*100:.1f}%）
- 🟡 一般（40-60分）：{average}家（{average/total*100:.1f}%）
- 🔴 较差（<40分）：{poor}家（{poor/total*100:.1f}%）

平均健康度：{avg:.1f}分

【最健康门店】
{chr(10).join([f"  {i+1}. {s['store_name']}: {s['health_score']:.1f}分" for i, s in enumerate(scores[:3])])}

【需关注门店】
{chr(10).join([f"  {i+1}. {s['store_name']}: {s['health_score']:.1f}分" for i, s in enumerate(scores[-3:])])}

💡 建议：重点关注健康度低于40分的门店，分析其薄弱环节。"""
    
    def _empty_health_scores(self) -> Dict:
        return {'scores': [], 'distribution': {'excellent': {'count': 0, 'percentage': 0}, 'good': {'count': 0, 'percentage': 0}, 'average': {'count': 0, 'percentage': 0}, 'poor': {'count': 0, 'percentage': 0}}, 'top_stores': [], 'bottom_stores': [], 'avg_score': 0, 'summary_text': '暂无数据'}

    def analyze_cost_structure(self) -> Dict:
        """成本结构分析"""
        if self.stores.empty:
            return self._empty_cost_structure()
        
        # 计算总成本
        total_marketing = float(self.stores['total_marketing_cost'].sum()) if 'total_marketing_cost' in self.stores.columns else 0
        total_delivery = float(self.stores['total_delivery_cost'].sum()) if 'total_delivery_cost' in self.stores.columns else 0
        total_revenue = float(self.stores['total_revenue'].sum())
        
        # 计算成本率统计
        mc_rates = self.stores['marketing_cost_rate'].values
        dc_rates = self.stores['delivery_cost_rate'].values
        
        def rate_stats(rates):
            return {
                'mean': round(float(np.mean(rates)), 2),
                'median': round(float(np.median(rates)), 2),
                'std': round(float(np.std(rates)), 2),
                'min': round(float(np.min(rates)), 2),
                'max': round(float(np.max(rates)), 2)
            }
        
        # 识别成本异常门店
        mc_high = self.stores[self.stores['marketing_cost_rate'] > 15]['store_name'].tolist()
        dc_high = self.stores[self.stores['delivery_cost_rate'] > 20]['store_name'].tolist()
        
        # 高绩效 vs 低绩效门店成本对比
        pm_median = self.stores['profit_margin'].median()
        high_perf = self.stores[self.stores['profit_margin'] >= pm_median]
        low_perf = self.stores[self.stores['profit_margin'] < pm_median]
        
        comparison = {
            'high_performance': {
                'avg_marketing_rate': round(float(high_perf['marketing_cost_rate'].mean()), 2) if not high_perf.empty else 0,
                'avg_delivery_rate': round(float(high_perf['delivery_cost_rate'].mean()), 2) if not high_perf.empty else 0
            },
            'low_performance': {
                'avg_marketing_rate': round(float(low_perf['marketing_cost_rate'].mean()), 2) if not low_perf.empty else 0,
                'avg_delivery_rate': round(float(low_perf['delivery_cost_rate'].mean()), 2) if not low_perf.empty else 0
            }
        }
        
        return {
            'totals': {
                'marketing_cost': round(total_marketing, 2),
                'delivery_cost': round(total_delivery, 2),
                'marketing_ratio': round(total_marketing / total_revenue * 100, 2) if total_revenue > 0 else 0,
                'delivery_ratio': round(total_delivery / total_revenue * 100, 2) if total_revenue > 0 else 0
            },
            'marketing_rate_stats': rate_stats(mc_rates),
            'delivery_rate_stats': rate_stats(dc_rates),
            'anomaly_stores': {
                'high_marketing': mc_high[:5],
                'high_delivery': dc_high[:5]
            },
            'performance_comparison': comparison,
            'summary_text': self._gen_cost_structure_summary(total_marketing, total_delivery, total_revenue, mc_high, dc_high, comparison)
        }
    
    def _gen_cost_structure_summary(self, mc, dc, revenue, mc_high, dc_high, comparison) -> str:
        mc_ratio = mc / revenue * 100 if revenue > 0 else 0
        dc_ratio = dc / revenue * 100 if revenue > 0 else 0
        
        return f"""💰 成本结构分析

【成本总览】
- 营销成本：¥{mc:,.0f}（占销售额{mc_ratio:.1f}%）
- 配送成本：¥{dc:,.0f}（占销售额{dc_ratio:.1f}%）

【成本异常门店】
- 营销成本率>15%：{len(mc_high)}家 {('(' + ', '.join(mc_high[:3]) + '...)') if mc_high else ''}
- 配送成本率>20%：{len(dc_high)}家 {('(' + ', '.join(dc_high[:3]) + '...)') if dc_high else ''}

【高绩效 vs 低绩效门店对比】
- 高绩效门店：营销成本率{comparison['high_performance']['avg_marketing_rate']:.1f}%，配送成本率{comparison['high_performance']['avg_delivery_rate']:.1f}%
- 低绩效门店：营销成本率{comparison['low_performance']['avg_marketing_rate']:.1f}%，配送成本率{comparison['low_performance']['avg_delivery_rate']:.1f}%

💡 优化建议：
- {'营销成本偏高，建议优化活动策略' if mc_ratio > 12 else '营销成本控制良好'}
- {'配送成本偏高，建议优化配送范围' if dc_ratio > 15 else '配送成本控制良好'}"""
    
    def _empty_cost_structure(self) -> Dict:
        return {'totals': {'marketing_cost': 0, 'delivery_cost': 0, 'marketing_ratio': 0, 'delivery_ratio': 0}, 'marketing_rate_stats': {'mean': 0, 'median': 0, 'std': 0, 'min': 0, 'max': 0}, 'delivery_rate_stats': {'mean': 0, 'median': 0, 'std': 0, 'min': 0, 'max': 0}, 'anomaly_stores': {'high_marketing': [], 'high_delivery': []}, 'performance_comparison': {'high_performance': {'avg_marketing_rate': 0, 'avg_delivery_rate': 0}, 'low_performance': {'avg_marketing_rate': 0, 'avg_delivery_rate': 0}}, 'summary_text': '暂无数据'}


@router.get("/comparison/global-insights")
async def get_global_insights(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    channel: Optional[str] = Query(None, description="渠道筛选"),
    include_trends: bool = Query(True, description="是否包含趋势分析")
) -> Dict[str, Any]:
    """
    全局门店洞察分析
    
    返回完整的洞察报告，包含：
    - 整体概况分析
    - 门店分群分析
    - 异常门店检测
    - 头尾对比分析
    - 利润率归因分析
    - 趋势变化分析
    - 策略建议
    """
    import time
    from datetime import datetime as dt
    
    query_start = time.time()
    
    # 获取门店数据
    store_stats = None
    if AGGREGATION_TABLE_AVAILABLE:
        store_stats = get_store_metrics_from_aggregation(start_date, end_date, channel)
    
    if store_stats is None or store_stats.empty:
        df = get_all_stores_data(start_date, end_date, channel)
        if not df.empty:
            store_stats = calculate_store_metrics(df)
    
    if store_stats is None or store_stats.empty:
        return {"success": True, "data": None, "message": "暂无门店数据"}
    
    # 获取环比数据（如果需要）
    wow_data = []
    if include_trends and end_date:
        try:
            wow_response = await get_stores_week_over_week(end_date, None, None, channel)
            if wow_response.get('success') and wow_response.get('data'):
                wow_data = wow_response['data'].get('stores', [])
        except Exception as e:
            print(f"⚠️ 获取环比数据失败: {e}")
    
    # 初始化洞察引擎
    engine = InsightsEngine(store_stats, wow_data)
    
    # 生成各模块分析
    overview = engine.generate_overview()
    clustering = engine.cluster_stores()
    anomalies = engine.detect_anomalies()
    head_tail = engine.compare_head_tail()
    attribution = engine.analyze_attribution()
    trends = engine.analyze_trends()
    health_scores = engine.calculate_health_scores()
    cost_structure = engine.analyze_cost_structure()
    recommendations = engine.generate_recommendations(anomalies, clustering, attribution, trends)
    
    query_time = (time.time() - query_start) * 1000
    print(f"✅ [全局洞察] 分析完成，耗时: {query_time:.1f}ms")
    
    return {
        "success": True,
        "data": {
            "overview": overview,
            "clustering": clustering,
            "anomalies": anomalies,
            "head_tail_comparison": head_tail,
            "attribution": attribution,
            "trends": trends,
            "health_scores": health_scores,
            "cost_structure": cost_structure,
            "recommendations": recommendations,
            "generated_at": dt.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
