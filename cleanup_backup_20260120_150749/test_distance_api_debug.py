# -*- coding: utf-8 -*-
"""
调试距离分析API的订单聚合逻辑
"""
import sys
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(APP_DIR / "backend" / "app"))

from database.connection import SessionLocal
from database.models import Order
import pandas as pd
import numpy as np

# 导入API中的函数
from api.v1.orders import get_order_data, calculate_order_metrics, DISTANCE_BANDS, get_distance_band_index

def debug_distance_analysis():
    """调试距离分析逻辑"""
    print("=" * 80)
    print("🔍 调试距离分析API逻辑")
    print("=" * 80)
    
    # 1. 加载数据（模拟API调用）
    print("\n1️⃣ 加载订单数据...")
    df = get_order_data(None)  # 不筛选门店
    print(f"   原始数据行数: {len(df)}")
    print(f"   唯一订单ID数: {df['订单ID'].nunique()}")
    
    # 2. 计算订单级指标
    print("\n2️⃣ 计算订单级指标（calculate_order_metrics）...")
    order_agg = calculate_order_metrics(df)
    print(f"   聚合后订单数: {len(order_agg)}")
    
    # 3. 检查order_agg中是否有配送距离
    print("\n3️⃣ 检查order_agg中的字段...")
    print(f"   order_agg列: {list(order_agg.columns)}")
    
    # 4. 模拟API中获取配送距离的逻辑
    print("\n4️⃣ 模拟API中获取配送距离的逻辑...")
    
    # 从数据库获取配送距离
    session = SessionLocal()
    try:
        order_ids = order_agg['订单ID'].unique().tolist()
        print(f"   需要查询的订单ID数: {len(order_ids)}")
        
        # 批量查询配送距离
        orders_with_distance = session.query(
            Order.order_id, 
            Order.delivery_distance
        ).filter(
            Order.order_id.in_(order_ids)
        ).all()
        
        distance_map = {}
        for order_id, distance in orders_with_distance:
            if distance is not None:
                distance_map[str(order_id)] = float(distance)
        
        print(f"   获取到配送距离的订单数: {len(distance_map)}")
        
        # 检测单位
        if distance_map:
            avg_dist = sum(distance_map.values()) / len(distance_map)
            print(f"   平均配送距离（原始）: {avg_dist:.2f}")
            
            if avg_dist > 100:
                print(f"   ⚠️ 检测为【米】，转换为公里...")
                distance_map = {k: v / 1000 for k, v in distance_map.items()}
                avg_dist_km = sum(distance_map.values()) / len(distance_map)
                print(f"   平均配送距离（公里）: {avg_dist_km:.2f}")
        
        # 将配送距离添加到order_agg
        order_agg['配送距离'] = order_agg['订单ID'].astype(str).map(distance_map).fillna(0)
        
        print(f"\n   配送距离统计:")
        print(f"   - 非零值数量: {(order_agg['配送距离'] > 0).sum()}")
        print(f"   - 零值数量: {(order_agg['配送距离'] == 0).sum()}")
        print(f"   - 最小值: {order_agg['配送距离'].min():.2f}")
        print(f"   - 最大值: {order_agg['配送距离'].max():.2f}")
        print(f"   - 平均值: {order_agg['配送距离'].mean():.2f}")
        
    finally:
        session.close()
    
    # 5. 按距离区间分组
    print("\n5️⃣ 按距离区间分组...")
    order_agg['距离区间'] = order_agg['配送距离'].apply(get_distance_band_index)
    
    for i, band in enumerate(DISTANCE_BANDS):
        band_df = order_agg[order_agg['距离区间'] == i]
        order_count = len(band_df)
        revenue = float(band_df['实收价格'].sum()) if '实收价格' in band_df.columns and order_count > 0 else 0
        profit = float(band_df['订单实际利润'].sum()) if '订单实际利润' in band_df.columns and order_count > 0 else 0
        profit_rate = round(profit / revenue * 100, 2) if revenue > 0 else 0
        
        print(f"   {band['label']}: 订单数={order_count}, 销售额={revenue:.2f}, 利润率={profit_rate:.2f}%")
    
    # 6. 对比：直接从数据库按订单ID去重统计
    print("\n6️⃣ 对比：直接从数据库统计（按订单ID去重）...")
    session = SessionLocal()
    try:
        from sqlalchemy import func, distinct, case
        
        # 按订单ID去重，统计各距离区间的订单数
        query = session.query(
            Order.order_id,
            Order.delivery_distance
        ).distinct(Order.order_id)
        
        results = query.all()
        
        # 转换为DataFrame
        db_df = pd.DataFrame(results, columns=['订单ID', '配送距离'])
        
        # 转换单位
        db_df['配送距离_km'] = db_df['配送距离'] / 1000
        
        # 分配区间
        db_df['距离区间'] = db_df['配送距离_km'].apply(get_distance_band_index)
        
        for i, band in enumerate(DISTANCE_BANDS):
            band_df = db_df[db_df['距离区间'] == i]
            print(f"   {band['label']}: 订单数={len(band_df)}")
        
    finally:
        session.close()
    
    print("\n" + "=" * 80)
    print("✅ 调试完成")
    print("=" * 80)


if __name__ == "__main__":
    debug_distance_analysis()
