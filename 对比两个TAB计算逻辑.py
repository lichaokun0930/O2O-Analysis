# -*- coding: utf-8 -*-
"""
对比经营总览TAB和全量门店对比TAB的计算逻辑

直接调用两个API的核心计算函数，找出差异
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "backend" / "app"))

from database.connection import SessionLocal
from database.models import Order
from datetime import datetime, date
import pandas as pd

# 导入两个API的计算函数
from backend.app.api.v1.orders import get_order_data, calculate_order_metrics as orders_calculate
from backend.app.api.v1.store_comparison import get_all_stores_data, calculate_store_metrics

STORE_NAME = "惠宜选-泰州兴化店"
START_DATE = date(2026, 1, 16)
END_DATE = date(2026, 1, 22)

def test_orders_api_logic():
    """模拟经营总览API的计算逻辑"""
    print("\n" + "=" * 60)
    print("【经营总览TAB】计算逻辑")
    print("=" * 60)
    
    # 1. 加载数据（与orders.py一致）
    df = get_order_data(STORE_NAME)
    print(f"原始数据: {len(df)} 条")
    
    # 2. 日期筛选（与orders.py一致）
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        df = df[df['日期'].dt.date >= START_DATE]
        df = df[df['日期'].dt.date <= END_DATE]
    
    print(f"日期筛选后: {len(df)} 条")
    print(f"唯一订单数: {df['订单ID'].nunique()}")
    
    # 3. 计算订单级指标
    order_agg = orders_calculate(df)
    print(f"订单级聚合后: {len(order_agg)} 条")
    
    # 4. 汇总
    total_orders = len(order_agg)
    total_actual_sales = order_agg['实收价格'].sum() if '实收价格' in order_agg.columns else 0
    total_profit = order_agg['订单实际利润'].sum() if '订单实际利润' in order_agg.columns else 0
    
    print(f"\n结果:")
    print(f"  订单数: {total_orders}")
    print(f"  销售额: ¥{total_actual_sales:,.2f}")
    print(f"  总利润: ¥{total_profit:,.2f}")
    
    return {
        'orders': total_orders,
        'sales': total_actual_sales,
        'profit': total_profit
    }


def test_comparison_api_logic():
    """模拟全量门店对比API的计算逻辑"""
    print("\n" + "=" * 60)
    print("【全量门店对比TAB】计算逻辑")
    print("=" * 60)
    
    # 1. 加载数据（与store_comparison.py一致）
    df = get_all_stores_data(START_DATE, END_DATE, None)
    print(f"原始数据: {len(df)} 条")
    
    # 筛选目标门店
    store_df = df[df['门店名称'] == STORE_NAME].copy()
    print(f"门店筛选后: {len(store_df)} 条")
    print(f"唯一订单数: {store_df['订单ID'].nunique()}")
    
    # 2. 计算门店指标
    store_stats = calculate_store_metrics(store_df)
    
    if store_stats.empty:
        print("❌ 计算结果为空")
        return None
    
    # 3. 获取目标门店数据
    target = store_stats[store_stats['store_name'] == STORE_NAME]
    if target.empty:
        print(f"❌ 未找到门店: {STORE_NAME}")
        return None
    
    target = target.iloc[0]
    
    print(f"\n结果:")
    print(f"  订单数: {target['order_count']}")
    print(f"  销售额: ¥{target['total_revenue']:,.2f}")
    print(f"  总利润: ¥{target['total_profit']:,.2f}")
    
    return {
        'orders': target['order_count'],
        'sales': target['total_revenue'],
        'profit': target['total_profit']
    }


def compare_raw_data():
    """对比两个API加载的原始数据"""
    print("\n" + "=" * 60)
    print("【原始数据对比】")
    print("=" * 60)
    
    # orders.py 的数据加载
    df1 = get_order_data(STORE_NAME)
    df1['日期'] = pd.to_datetime(df1['日期'], errors='coerce')
    df1 = df1[(df1['日期'].dt.date >= START_DATE) & (df1['日期'].dt.date <= END_DATE)]
    
    # store_comparison.py 的数据加载
    df2 = get_all_stores_data(START_DATE, END_DATE, None)
    df2 = df2[df2['门店名称'] == STORE_NAME]
    
    print(f"orders.py 数据: {len(df1)} 条, {df1['订单ID'].nunique()} 订单")
    print(f"store_comparison.py 数据: {len(df2)} 条, {df2['订单ID'].nunique()} 订单")
    
    # 检查订单ID差异
    orders1 = set(df1['订单ID'].unique())
    orders2 = set(df2['订单ID'].unique())
    
    only_in_1 = orders1 - orders2
    only_in_2 = orders2 - orders1
    
    print(f"\n只在orders.py中的订单: {len(only_in_1)}")
    print(f"只在store_comparison.py中的订单: {len(only_in_2)}")
    
    if only_in_1:
        print(f"  示例: {list(only_in_1)[:5]}")
    if only_in_2:
        print(f"  示例: {list(only_in_2)[:5]}")
    
    # 检查关键字段
    print(f"\n关键字段对比:")
    print(f"  orders.py 利润额总和: ¥{df1['利润额'].sum():,.2f}")
    print(f"  store_comparison.py 利润额总和: ¥{df2['利润额'].sum():,.2f}")
    print(f"  orders.py 平台服务费总和: ¥{df1['平台服务费'].sum():,.2f}")
    print(f"  store_comparison.py 平台服务费总和: ¥{df2['平台服务费'].sum():,.2f}")
    print(f"  orders.py 物流配送费总和: ¥{df1['物流配送费'].sum():,.2f}")
    print(f"  store_comparison.py 物流配送费总和: ¥{df2['物流配送费'].sum():,.2f}")


if __name__ == "__main__":
    # 先对比原始数据
    compare_raw_data()
    
    # 再对比计算结果
    result1 = test_orders_api_logic()
    result2 = test_comparison_api_logic()
    
    if result1 and result2:
        print("\n" + "=" * 60)
        print("【差异汇总】")
        print("=" * 60)
        print(f"订单数差异: {result1['orders'] - result2['orders']}")
        print(f"销售额差异: ¥{result1['sales'] - result2['sales']:,.2f}")
        print(f"利润差异: ¥{result1['profit'] - result2['profit']:,.2f}")
