# -*- coding: utf-8 -*-
"""
品类分析 + 异常检测 + 图表联动 API

从 orders.py 拆分出的分析相关接口：
- 利润区间分布
- 客单价区间分布
- 一级分类销售趋势
- 异常诊断
- 分时品类走势
- 商品销量排行
"""

from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import pandas as pd
import numpy as np

# 从主模块导入公共函数
from .orders import get_order_data, calculate_order_metrics

router = APIRouter()


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


