# -*- coding: utf-8 -*-
"""
配送分析 + 成本结构 API

从 orders.py 拆分出的配送相关接口：
- 分时利润分析（含高峰识别）
- 成本结构分析（桑基图）
- 分距离订单诊断
- 配送溢价雷达
"""

from fastapi import APIRouter, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np
from database.connection import SessionLocal

# 从主模块导入公共函数
from .orders import get_order_data, calculate_order_metrics

router = APIRouter()

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
            "peak_periods": peak_periods,
            "comparison": None  # 环比数据占位，下面计算
        }
    }
    
    result = {
        "success": True,
        "data": {
            "date": date_label,
            "hours": [f"{h:02d}:00" for h in range(24)],
            "orders": [int(x) for x in hourly_stats['orders'].tolist()],
            "profits": [round(float(x), 2) for x in hourly_stats['profit'].tolist()],
            "revenues": [round(float(x), 2) for x in hourly_stats['revenue'].tolist()],
            "avg_profits": [float(x) for x in hourly_stats['avg_profit'].tolist()],
            "peak_periods": peak_periods,
            "comparison": None
        }
    }
    
    # 🆕 计算环比数据（仅当选择单日期或日期范围时）
    try:
        # 重新加载完整数据用于环比计算
        full_df = get_order_data(store_name)
        if not full_df.empty and '日期' in full_df.columns:
            full_df['日期'] = pd.to_datetime(full_df['日期'], errors='coerce')
            full_df = full_df.dropna(subset=['日期'])
            
            # 渠道筛选
            if channel and channel != 'all' and '渠道' in full_df.columns:
                full_df = full_df[full_df['渠道'] == channel]
            
            # 确定当前周期和上一周期
            if target_date:
                # 单日期：环比为前一天
                try:
                    if len(target_date) == 5 and '-' in target_date:
                        max_date = full_df['日期'].max()
                        year = max_date.year
                        current_date = pd.to_datetime(f"{year}-{target_date}")
                    else:
                        current_date = pd.to_datetime(target_date)
                    prev_date = current_date - timedelta(days=1)
                    
                    # 获取上一周期数据
                    prev_df = full_df[full_df['日期'].dt.date == prev_date.date()]
                    if not prev_df.empty:
                        # 计算上一周期的分时数据
                        prev_df = prev_df.copy()
                        prev_df['小时'] = prev_df['日期'].dt.hour
                        quantity_field = '月售' if '月售' in prev_df.columns else '销量'
                        if '实收价格' in prev_df.columns and quantity_field in prev_df.columns:
                            prev_df['_销售额'] = prev_df['实收价格'].fillna(0) * prev_df[quantity_field].fillna(1)
                        else:
                            prev_df['_销售额'] = prev_df.get('商品实售价', 0)
                        
                        prev_order_agg_dict = {'利润额': 'sum', '物流配送费': 'first', '_销售额': 'sum', '小时': 'first'}
                        if '平台服务费' in prev_df.columns:
                            prev_order_agg_dict['平台服务费'] = 'sum'
                        if '企客后返' in prev_df.columns:
                            prev_order_agg_dict['企客后返'] = 'sum'
                        
                        prev_order_agg = prev_df.groupby('订单ID').agg(prev_order_agg_dict).reset_index()
                        prev_order_agg['订单实际利润'] = (
                            prev_order_agg['利润额'].fillna(0) -
                            prev_order_agg.get('平台服务费', pd.Series(0, index=prev_order_agg.index)).fillna(0) -
                            prev_order_agg['物流配送费'].fillna(0) +
                            prev_order_agg.get('企客后返', pd.Series(0, index=prev_order_agg.index)).fillna(0)
                        )
                        
                        prev_hourly = prev_order_agg.groupby('小时').agg({
                            '订单ID': 'count', '订单实际利润': 'sum', '_销售额': 'sum'
                        }).reset_index()
                        prev_hourly.columns = ['hour', 'orders', 'profit', 'revenue']
                        
                        # 计算汇总环比
                        curr_total_orders = sum(hourly_stats['orders'])
                        curr_total_profit = sum(hourly_stats['profit'])
                        prev_total_orders = int(prev_hourly['orders'].sum())
                        prev_total_profit = float(prev_hourly['profit'].sum())
                        
                        order_change = round((curr_total_orders - prev_total_orders) / prev_total_orders * 100, 1) if prev_total_orders > 0 else None
                        profit_change = round((curr_total_profit - prev_total_profit) / abs(prev_total_profit) * 100, 1) if prev_total_profit != 0 else None
                        
                        result["data"]["comparison"] = {
                            "period": f"{prev_date.strftime('%m-%d')} vs {current_date.strftime('%m-%d')}",
                            "prev_total_orders": prev_total_orders,
                            "prev_total_profit": round(prev_total_profit, 2),
                            "order_change": order_change,
                            "profit_change": profit_change
                        }
                except Exception as e:
                    print(f"⚠️ 分时段诊断环比计算失败: {e}")
            
            elif start_date and end_date:
                # 日期范围：环比为相同长度的前一周期
                try:
                    start_dt = pd.to_datetime(start_date)
                    end_dt = pd.to_datetime(end_date)
                    period_days = (end_dt - start_dt).days + 1
                    prev_end = start_dt - timedelta(days=1)
                    prev_start = prev_end - timedelta(days=period_days - 1)
                    
                    prev_df = full_df[(full_df['日期'].dt.date >= prev_start.date()) & (full_df['日期'].dt.date <= prev_end.date())]
                    if not prev_df.empty:
                        # 简化计算：只计算订单数和利润的环比
                        prev_df = prev_df.copy()
                        prev_df['小时'] = prev_df['日期'].dt.hour
                        prev_order_count = prev_df['订单ID'].nunique()
                        
                        # 计算利润
                        prev_profit = 0
                        if '利润额' in prev_df.columns:
                            prev_order_agg = prev_df.groupby('订单ID').agg({
                                '利润额': 'sum',
                                '物流配送费': 'first',
                                '平台服务费': 'sum' if '平台服务费' in prev_df.columns else 'first',
                                '企客后返': 'sum' if '企客后返' in prev_df.columns else 'first'
                            }).reset_index()
                            prev_order_agg['订单实际利润'] = (
                                prev_order_agg['利润额'].fillna(0) -
                                prev_order_agg.get('平台服务费', pd.Series(0)).fillna(0) -
                                prev_order_agg['物流配送费'].fillna(0) +
                                prev_order_agg.get('企客后返', pd.Series(0)).fillna(0)
                            )
                            prev_profit = float(prev_order_agg['订单实际利润'].sum())
                        
                        curr_total_orders = sum(hourly_stats['orders'])
                        curr_total_profit = sum(hourly_stats['profit'])
                        
                        order_change = round((curr_total_orders - prev_order_count) / prev_order_count * 100, 1) if prev_order_count > 0 else None
                        profit_change = round((curr_total_profit - prev_profit) / abs(prev_profit) * 100, 1) if prev_profit != 0 else None
                        
                        result["data"]["comparison"] = {
                            "period": f"{prev_start.strftime('%m-%d')}~{prev_end.strftime('%m-%d')} vs {start_date[5:]}~{end_date[5:]}",
                            "prev_total_orders": prev_order_count,
                            "prev_total_profit": round(prev_profit, 2),
                            "order_change": order_change,
                            "profit_change": profit_change
                        }
                except Exception as e:
                    print(f"⚠️ 分时段诊断日期范围环比计算失败: {e}")
    except Exception as e:
        print(f"⚠️ 分时段诊断环比计算异常: {e}")
    
    return result


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
        # 🆕 同时计算物流配送费总额用于单均配送费
        delivery_cost = 0
        total_delivery_fee = 0  # 物流配送费总额
        if order_count > 0:
            if '物流配送费' in band_df.columns:
                total_delivery_fee = float(band_df['物流配送费'].sum())
                delivery_cost = total_delivery_fee
            if '用户支付配送费' in band_df.columns:
                delivery_cost -= float(band_df['用户支付配送费'].sum())
            if '配送费减免金额' in band_df.columns:
                delivery_cost += float(band_df['配送费减免金额'].sum())
        
        # 计算派生指标
        profit_rate = round(profit / revenue * 100, 2) if revenue > 0 else 0
        delivery_cost_rate = round(delivery_cost / revenue * 100, 2) if revenue > 0 else 0
        avg_order_value = round(revenue / order_count, 2) if order_count > 0 else 0
        avg_delivery_fee = round(total_delivery_fee / order_count, 2) if order_count > 0 else 0  # 🆕 单均配送费
        
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
            "avg_order_value": avg_order_value,
            "avg_delivery_fee": avg_delivery_fee  # 🆕 单均配送费
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
    
    # 🆕 构建结果（环比数据稍后计算）
    result = {
        "success": True,
        "data": {
            "date": analysis_date_str,
            "distance_bands": band_stats,
            "summary": {
                "total_orders": total_orders,
                "avg_distance": avg_distance,
                "optimal_distance": optimal_band,
                "total_revenue": round(total_revenue, 2),
                "total_profit": round(total_profit, 2)
            },
            "comparison": None
        }
    }
    
    # 🆕 计算环比数据（包括每个距离区间的订单量环比）
    try:
        # 重新加载完整数据用于环比计算
        full_df = get_order_data(store_name)
        if not full_df.empty and '日期' in full_df.columns:
            full_df['日期'] = pd.to_datetime(full_df['日期'], errors='coerce')
            full_df = full_df.dropna(subset=['日期'])
            
            # 渠道筛选
            if channel and channel != 'all' and '渠道' in full_df.columns:
                full_df = full_df[full_df['渠道'] == channel]
            
            # 确定当前周期和上一周期
            prev_df = None
            period_label = None
            
            if analysis_date is not None:
                # 单日期：环比为前一天
                prev_date = analysis_date - timedelta(days=1)
                prev_df = full_df[full_df['日期'].dt.date == prev_date.date()]
                period_label = f"{prev_date.strftime('%m-%d')} vs {analysis_date.strftime('%m-%d')}"
            
            elif start_date and end_date:
                # 日期范围：环比为相同长度的前一周期
                period_days = (end_date - start_date).days + 1
                prev_end = start_date - timedelta(days=1)
                prev_start = prev_end - timedelta(days=period_days - 1)
                prev_df = full_df[(full_df['日期'].dt.date >= prev_start) & (full_df['日期'].dt.date <= prev_end)]
                period_label = f"{prev_start.strftime('%m-%d')}~{prev_end.strftime('%m-%d')} vs {start_date.strftime('%m-%d')}~{end_date.strftime('%m-%d')}"
            
            if prev_df is not None and not prev_df.empty:
                # 计算上一周期的订单级指标
                prev_order_agg = calculate_order_metrics(prev_df)
                
                if not prev_order_agg.empty:
                    # 获取上一周期的配送距离
                    prev_distance_map = {}
                    try:
                        session = SessionLocal()
                        try:
                            prev_order_ids = prev_order_agg['订单ID'].unique().tolist()
                            prev_orders_with_distance = session.query(
                                Order.order_id, 
                                Order.delivery_distance
                            ).filter(
                                Order.order_id.in_(prev_order_ids)
                            ).all()
                            
                            for order_id, distance in prev_orders_with_distance:
                                if distance is not None:
                                    prev_distance_map[str(order_id)] = float(distance)
                            
                            # 检测距离单位
                            if prev_distance_map:
                                avg_dist = sum(prev_distance_map.values()) / len(prev_distance_map)
                                if avg_dist > 100:
                                    prev_distance_map = {k: v / 1000 for k, v in prev_distance_map.items()}
                        finally:
                            session.close()
                    except Exception as e:
                        print(f"⚠️ 获取上一周期配送距离失败: {e}")
                    
                    # 为上一周期订单分配距离区间
                    prev_order_agg['配送距离'] = prev_order_agg['订单ID'].astype(str).map(prev_distance_map).fillna(0)
                    prev_order_agg['距离区间'] = prev_order_agg['配送距离'].apply(get_distance_band_index)
                    
                    # 🆕 计算每个距离区间的上一周期订单数和利润
                    prev_band_orders = {}
                    prev_band_profits = {}
                    for i, band in enumerate(DISTANCE_BANDS):
                        prev_band_df = prev_order_agg[prev_order_agg['距离区间'] == i]
                        prev_band_orders[i] = len(prev_band_df)
                        prev_band_profits[i] = float(prev_band_df['订单实际利润'].sum()) if '订单实际利润' in prev_band_df.columns and len(prev_band_df) > 0 else 0
                    
                    # 🆕 为每个距离区间计算订单量环比和利润环比
                    for i, band_stat in enumerate(band_stats):
                        current_count = band_stat["order_count"]
                        prev_count = prev_band_orders.get(i, 0)
                        current_profit = band_stat["profit"]
                        prev_profit = prev_band_profits.get(i, 0)
                        
                        # 订单量环比
                        if prev_count > 0:
                            order_count_change = round((current_count - prev_count) / prev_count * 100, 1)
                        else:
                            order_count_change = None  # 上一周期无数据
                        
                        # 利润环比
                        if prev_profit != 0:
                            profit_change = round((current_profit - prev_profit) / abs(prev_profit) * 100, 1)
                        else:
                            profit_change = None  # 上一周期无数据
                        
                        band_stat["order_count_change"] = order_count_change
                        band_stat["profit_change"] = profit_change
                    
                    # 计算总量环比
                    prev_total_orders = len(prev_order_agg)
                    prev_total_profit = float(prev_order_agg['订单实际利润'].sum()) if '订单实际利润' in prev_order_agg.columns else 0
                    prev_total_revenue = float(prev_order_agg['实收价格'].sum()) if '实收价格' in prev_order_agg.columns else 0
                    
                    order_change = round((total_orders - prev_total_orders) / prev_total_orders * 100, 1) if prev_total_orders > 0 else None
                    profit_change = round((total_profit - prev_total_profit) / abs(prev_total_profit) * 100, 1) if prev_total_profit != 0 else None
                    revenue_change = round((total_revenue - prev_total_revenue) / prev_total_revenue * 100, 1) if prev_total_revenue > 0 else None
                    
                    result["data"]["comparison"] = {
                        "period": period_label,
                        "prev_total_orders": prev_total_orders,
                        "prev_total_profit": round(prev_total_profit, 2),
                        "prev_total_revenue": round(prev_total_revenue, 2),
                        "order_change": order_change,
                        "profit_change": profit_change,
                        "revenue_change": revenue_change
                    }
    except Exception as e:
        print(f"⚠️ 分距离诊断环比计算失败: {e}")
    
    return result


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
        return {"success": False, "message": str(e), "data": []}


