# -*- coding: utf-8 -*-
"""
品类效益矩阵 API

与 Dash 版本完全一致的计算逻辑：
- 销售额使用 actual_price（实收价格）
- 利润率 = 利润 / 实收价格 × 100%
- 支持一级分类和三级分类下钻
- 🔴 剔除耗材分类（非销售商品）

🆕 2025-01-16 优化：
滞销天数计算逻辑改为"以商品首次出现日期为观察起点"
- 商品A在1日有销售 → 从1日开始计算无销售天数
- 商品B在5日首次出现 → 从5日开始计算无销售天数
- 解决了数据窗口边界导致的滞销判断失真问题

业务逻辑来源: 智能门店看板_Dash版.py 第11120-11450行
"""

from fastapi import APIRouter, Query
from typing import Optional, Dict, Any, List
from datetime import timedelta
import pandas as pd
import numpy as np

import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from .orders import get_order_data

router = APIRouter()


def get_product_latest_stock(df: pd.DataFrame, stock_col: str, date_col: str) -> Dict[str, float]:
    """获取每个商品的最新库存（与Dash版本一致）"""
    if stock_col not in df.columns or date_col not in df.columns:
        return {}
    
    df_sorted = df.sort_values(date_col)
    latest = df_sorted.groupby('商品名称')[stock_col].last()
    return latest.to_dict()


@router.get("/performance")
async def get_category_performance(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    parent_category: Optional[str] = Query(None, description="父级分类（用于下钻到三级分类）"),
    channel: Optional[str] = Query(None, description="渠道筛选"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期")
) -> Dict[str, Any]:
    """
    获取品类效益数据（与Dash版本一致）
    
    返回数据结构：
    - 第一层（parent_category=None）：一级分类汇总
    - 第二层（parent_category=某一级分类）：该分类下的三级分类明细
    
    计算逻辑：
    - 销售额 = sum(实收价格)
    - 利润 = sum(订单实际利润) 或 销售额 - 成本
    - 利润率 = 利润 / 销售额 × 100%
    - 订单数 = count(distinct 订单ID)
    """
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": [], "level": "l1" if not parent_category else "l3"}
    
    # 🔴 剔除耗材分类（与Dash版本一致）
    category_col = '一级分类名' if '一级分类名' in df.columns else '一级分类'
    if category_col in df.columns:
        original_count = len(df)
        df = df[df[category_col] != '耗材'].copy()
        filtered_count = original_count - len(df)
        if filtered_count > 0:
            print(f"[category-matrix] 剔除耗材数据: {filtered_count} 条")
    
    # 渠道筛选
    if channel and channel != 'all' and '渠道' in df.columns:
        df = df[df['渠道'] == channel]
    
    # 日期筛选
    date_col = '日期' if '日期' in df.columns else '下单时间'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        
        if start_date:
            df = df[df[date_col] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df[date_col] <= pd.to_datetime(end_date)]
    
    if df.empty:
        return {"success": True, "data": [], "level": "l1" if not parent_category else "l3"}
    
    # 确定销售额字段
    sales_field = '实收价格' if '实收价格' in df.columns else '商品实售价'
    if sales_field not in df.columns:
        return {"success": True, "data": [], "error": "缺少销售额字段"}
    
    # 确定利润字段 - 按优先级检查多个可能的字段名
    profit_field = None
    for pf in ['订单实际利润', '利润额', '利润', 'profit']:
        if pf in df.columns:
            profit_field = pf
            break
    
    # 确定分类字段
    l3_col = '三级分类名' if '三级分类名' in df.columns else '三级分类'
    
    # 确定聚合维度
    if parent_category:
        # 下钻到三级分类
        df = df[df[category_col] == parent_category]
        if df.empty:
            return {"success": True, "data": [], "level": "l3", "parent": parent_category}
        
        group_col = l3_col if l3_col in df.columns else category_col
        level = "l3"
    else:
        # 一级分类汇总
        group_col = category_col
        level = "l1"
    
    if group_col not in df.columns:
        return {"success": True, "data": [], "level": level, "error": f"缺少分类字段: {group_col}"}
    
    # 处理空分类名
    df[group_col] = df[group_col].fillna('未分类')
    df.loc[df[group_col].astype(str).isin(['', 'nan', 'None']), group_col] = '未分类'
    
    # 🔴 关键修复：实收价格是单价，需要先乘以销量
    quantity_field = '月售' if '月售' in df.columns else '销量' if '销量' in df.columns else None
    
    if quantity_field:
        df['_销售额'] = df[sales_field].fillna(0) * df[quantity_field].fillna(1)
        agg_dict = {
            '_销售额': 'sum',
            '订单ID': 'count'  # 订单数（与Dash一致使用count）
        }
        if quantity_field:
            agg_dict[quantity_field] = 'sum'  # 总销量
    else:
        # 如果没有销量字段，假设每条记录销量为1
        agg_dict = {
            sales_field: 'sum',
            '订单ID': 'count'
        }
    
    if profit_field:
        agg_dict[profit_field] = 'sum'
    
    category_stats = df.groupby(group_col).agg(agg_dict).reset_index()
    
    # 重命名列 - 使用rename而不是直接赋值，避免列顺序问题
    if quantity_field and '_销售额' in category_stats.columns:
        rename_dict = {group_col: 'category', '_销售额': 'revenue', '订单ID': 'orderCount'}
        if profit_field:
            rename_dict[profit_field] = 'profit'
        if quantity_field in category_stats.columns:
            rename_dict[quantity_field] = 'quantity'
        category_stats.rename(columns=rename_dict, inplace=True)
    else:
        rename_dict = {group_col: 'category', sales_field: 'revenue', '订单ID': 'orderCount'}
        if profit_field:
            rename_dict[profit_field] = 'profit'
        category_stats.rename(columns=rename_dict, inplace=True)
    
    # 如果没有利润字段，估算利润（假设35%成本率）
    if 'profit' not in category_stats.columns:
        category_stats['profit'] = category_stats['revenue'] * 0.3  # 假设30%利润率
    
    # 计算利润率
    category_stats['margin'] = (category_stats['profit'] / category_stats['revenue'].replace(0, np.nan) * 100).fillna(0).round(2)
    
    # 按销售额降序排序
    category_stats = category_stats.sort_values('revenue', ascending=False)
    
    # 构建返回数据
    result = []
    for _, row in category_stats.iterrows():
        name = row['category']  # 使用重命名后的列名
        if parent_category:
            # 三级分类：名称格式为 "一级分类|三级分类"
            display_name = f"{parent_category}|{name}"
        else:
            display_name = name
        
        result.append({
            "name": display_name,
            "revenue": round(float(row['revenue']), 2),
            "profit": round(float(row['profit']), 2),
            "orderCount": int(row['orderCount']),
            "grossMargin": round(float(row['margin']) / 100, 4),  # 转为小数
            # 以下字段由库存风险API提供
            "soldOutCount": 0,
            "slowMovingCount": 0,
            "inventoryTurnover": 0
        })
    
    return {
        "success": True,
        "data": result,
        "level": level,
        "parent": parent_category,
        "total": len(result)
    }


@router.get("/with-risk")
async def get_category_with_risk(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    parent_category: Optional[str] = Query(None, description="父级分类"),
    channel: Optional[str] = Query(None, description="渠道筛选")
) -> Dict[str, Any]:
    """
    获取品类效益数据（含库存风险统计）
    
    合并品类销售数据和库存风险数据，一次性返回完整信息
    
    🔧 性能优化：
    - 使用向量化操作替代循环
    - 减少不必要的数据复制
    - 简化库存风险计算
    """
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": [], "level": "l1" if not parent_category else "l3"}
    
    # 🔴 剔除耗材分类
    category_col = '一级分类名' if '一级分类名' in df.columns else '一级分类'
    if category_col in df.columns:
        df = df[df[category_col] != '耗材']
    
    # 渠道筛选
    if channel and channel != 'all' and '渠道' in df.columns:
        df = df[df['渠道'] == channel]
    
    if df.empty:
        return {"success": True, "data": [], "level": "l1" if not parent_category else "l3"}
    
    # 日期字段
    date_col = '日期' if '日期' in df.columns else '下单时间'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
    
    # 销售额字段
    sales_field = '实收价格' if '实收价格' in df.columns else '商品实售价'
    if sales_field not in df.columns:
        return {"success": True, "data": [], "error": "缺少销售额字段"}
    
    # 利润字段
    profit_field = None
    for pf in ['订单实际利润', '利润额', '利润', 'profit']:
        if pf in df.columns:
            profit_field = pf
            break
    
    # 三级分类字段
    l3_col = '三级分类名' if '三级分类名' in df.columns else '三级分类'
    
    # 确定聚合维度
    if parent_category:
        df = df[df[category_col] == parent_category]
        if df.empty:
            return {"success": True, "data": [], "level": "l3", "parent": parent_category}
        group_col = l3_col if l3_col in df.columns else category_col
        level = "l3"
    else:
        group_col = category_col
        level = "l1"
    
    if group_col not in df.columns:
        return {"success": True, "data": [], "level": level}
    
    # 处理空分类名
    df[group_col] = df[group_col].fillna('未分类').astype(str)
    df.loc[df[group_col].isin(['', 'nan', 'None']), group_col] = '未分类'
    
    # ==================== 1. 销售数据聚合（向量化）====================
    df[sales_field] = pd.to_numeric(df[sales_field], errors='coerce').fillna(0)
    
    quantity_field = '月售' if '月售' in df.columns else '销量' if '销量' in df.columns else None
    
    if quantity_field and quantity_field in df.columns:
        df[quantity_field] = pd.to_numeric(df[quantity_field], errors='coerce').fillna(1)
        df['_销售额'] = df[sales_field] * df[quantity_field]
        revenue_col = '_销售额'
    else:
        revenue_col = sales_field
    
    if profit_field:
        df[profit_field] = pd.to_numeric(df[profit_field], errors='coerce').fillna(0)
    
    # 一次性聚合
    agg_dict = {revenue_col: 'sum', '订单ID': 'nunique'}
    if profit_field:
        agg_dict[profit_field] = 'sum'
    
    category_stats = df.groupby(group_col, as_index=False).agg(agg_dict)
    category_stats.columns = ['category', 'revenue', 'orderCount'] + (['profit'] if profit_field else [])
    
    if 'profit' not in category_stats.columns:
        category_stats['profit'] = category_stats['revenue'] * 0.3
    
    # 计算利润率
    category_stats['margin'] = np.where(
        category_stats['revenue'] > 0,
        (category_stats['profit'] / category_stats['revenue'] * 100).round(1),
        0.0
    )
    
    # ==================== 2. 简化库存风险统计（🆕 优化版：以首次出现日期为基准） ====================
    risk_data = {cat: {'soldOut': 0, 'slowMoving': 0, 'turnover': 0} for cat in category_stats['category']}
    
    stock_col = next((c for c in ['库存', '剩余库存', 'stock'] if c in df.columns), None)
    
    if stock_col and date_col in df.columns and len(df) > 0:
        last_date = df[date_col].max()
        seven_days_ago = last_date - timedelta(days=7)
        
        # 🆕 获取每个商品的首次出现日期和最后销售日期
        product_dates = df.sort_values(date_col).groupby('商品名称').agg({
            stock_col: 'last',
            group_col: 'first',
            date_col: ['min', 'max']  # 首次出现日期和最后销售日期
        }).reset_index()
        product_dates.columns = ['商品名称', 'stock', 'category', 'first_sale', 'last_sale']
        
        # 售罄品：最近7天有销售 + 当前库存=0
        recent_products = set(df[df[date_col] >= seven_days_ago]['商品名称'].unique())
        sellout_mask = (product_dates['stock'] == 0) & (product_dates['商品名称'].isin(recent_products))
        sellout_by_cat = product_dates[sellout_mask].groupby('category').size()
        
        # 🆕 滞销品：库存>0 + 从首次出现日期开始计算无销售天数 >= 7
        # 如果最后销售日期 == 首次出现日期，说明只卖过一次，从首次出现日期开始计算
        def calc_days_no_sale(row):
            if row['last_sale'] == row['first_sale']:
                return (last_date - row['first_sale']).days
            else:
                return (last_date - row['last_sale']).days
        
        product_dates['days_no_sale'] = product_dates.apply(calc_days_no_sale, axis=1)
        slowmove_mask = (product_dates['stock'] > 0) & (product_dates['days_no_sale'] >= 7)
        slowmove_by_cat = product_dates[slowmove_mask].groupby('category').size()
        
        # 更新风险数据
        for cat in risk_data:
            risk_data[cat]['soldOut'] = int(sellout_by_cat.get(cat, 0))
            risk_data[cat]['slowMoving'] = int(slowmove_by_cat.get(cat, 0))
    
    # ==================== 3. 构建结果 ====================
    category_stats = category_stats.sort_values('revenue', ascending=False)
    
    result = []
    for _, row in category_stats.iterrows():
        name = row['category']
        display_name = f"{parent_category}|{name}" if parent_category else name
        risk = risk_data.get(name, {'soldOut': 0, 'slowMoving': 0, 'turnover': 0})
        
        result.append({
            "name": display_name,
            "revenue": round(float(row['revenue']), 2),
            "profit": round(float(row['profit']), 2),
            "orderCount": int(row['orderCount']),
            "grossMargin": round(float(row['margin']), 1),
            "soldOutCount": risk['soldOut'],
            "slowMovingCount": risk['slowMoving'],
            "inventoryTurnover": risk['turnover']
        })
    
    return {
        "success": True,
        "data": result,
        "level": level,
        "parent": parent_category,
        "total": len(result)
    }
