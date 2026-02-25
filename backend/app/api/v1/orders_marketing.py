# -*- coding: utf-8 -*-
"""
营销成本分析 API

从 orders.py 拆分出的营销相关接口：
- 营销成本结构分析（桑基图专用）
- 营销成本趋势分析（趋势图专用）
"""

from fastapi import APIRouter, Query
from typing import Optional, Dict, Any
from datetime import date
import pandas as pd

# 从主模块导入公共函数
from .orders import get_order_data, calculate_order_metrics

router = APIRouter()


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
