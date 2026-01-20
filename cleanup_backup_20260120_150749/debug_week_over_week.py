#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试环比数据API - 查看返回的字段名
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import json

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.connection import SessionLocal
from database.models import Order
from backend.app.api.v1.store_comparison import get_all_stores_data, calculate_store_metrics

def debug_week_over_week():
    """调试环比数据"""
    print("=" * 80)
    print("调试环比数据API")
    print("=" * 80)
    
    session = SessionLocal()
    
    # 获取数据日期范围
    max_date_result = session.query(Order.date).order_by(Order.date.desc()).first()
    if not max_date_result:
        print("❌ 数据库中没有数据")
        return
    
    end_date = max_date_result[0].date()
    start_date = end_date - timedelta(days=6)
    
    print(f"\n本期: {start_date} ~ {end_date}")
    
    # 计算上期
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=6)
    
    print(f"上期: {prev_start} ~ {prev_end}")
    
    # 加载数据
    print("\n加载数据...")
    this_week_df = get_all_stores_data(start_date, end_date)
    last_week_df = get_all_stores_data(prev_start, prev_end)
    
    print(f"本期数据: {len(this_week_df)} 条")
    print(f"上期数据: {len(last_week_df)} 条")
    
    # 计算指标
    print("\n计算指标...")
    this_week_stats = calculate_store_metrics(this_week_df)
    last_week_stats = calculate_store_metrics(last_week_df)
    
    print(f"本期门店: {len(this_week_stats)} 个")
    print(f"上期门店: {len(last_week_stats)} 个")
    
    if this_week_stats.empty:
        print("❌ 本期没有数据")
        return
    
    # 查看第一个门店的数据
    print("\n" + "=" * 80)
    print("第一个门店的详细数据")
    print("=" * 80)
    
    first_store = this_week_stats.iloc[0]
    store_name = first_store['store_name']
    
    print(f"\n门店名称: {store_name}")
    print("\n本期数据:")
    print(f"  订单量: {first_store['order_count']}")
    print(f"  销售额: ¥{first_store['total_revenue']:.2f}")
    print(f"  利润: ¥{first_store['total_profit']:.2f}")
    print(f"  利润率: {first_store['profit_margin']:.2f}%")
    print(f"  客单价: ¥{first_store['aov']:.2f}")
    print(f"  单均配送费: ¥{first_store['avg_delivery_fee']:.2f}")
    print(f"  单均营销费: ¥{first_store['avg_marketing_cost']:.2f}")
    print(f"  配送成本率: {first_store['delivery_cost_rate']:.2f}%")
    print(f"  营销成本率: {first_store['marketing_cost_rate']:.2f}%")
    
    # 查找上期数据
    prev_store = last_week_stats[last_week_stats['store_name'] == store_name]
    
    if not prev_store.empty:
        prev_store = prev_store.iloc[0]
        print("\n上期数据:")
        print(f"  订单量: {prev_store['order_count']}")
        print(f"  销售额: ¥{prev_store['total_revenue']:.2f}")
        print(f"  利润: ¥{prev_store['total_profit']:.2f}")
        print(f"  利润率: {prev_store['profit_margin']:.2f}%")
        print(f"  客单价: ¥{prev_store['aov']:.2f}")
        print(f"  单均配送费: ¥{prev_store['avg_delivery_fee']:.2f}")
        print(f"  单均营销费: ¥{prev_store['avg_marketing_cost']:.2f}")
        
        print("\n环比变化:")
        print(f"  订单量: {((first_store['order_count'] - prev_store['order_count']) / prev_store['order_count'] * 100):.2f}%")
        print(f"  销售额: {((first_store['total_revenue'] - prev_store['total_revenue']) / prev_store['total_revenue'] * 100):.2f}%")
        print(f"  利润: {((first_store['total_profit'] - prev_store['total_profit']) / prev_store['total_profit'] * 100):.2f}%")
        print(f"  利润率: {(first_store['profit_margin'] - prev_store['profit_margin']):.2f} 百分点")
        print(f"  客单价: {((first_store['aov'] - prev_store['aov']) / prev_store['aov'] * 100):.2f}%")
        print(f"  单均配送费: {((first_store['avg_delivery_fee'] - prev_store['avg_delivery_fee']) / prev_store['avg_delivery_fee'] * 100):.2f}%")
        print(f"  单均营销费: {((first_store['avg_marketing_cost'] - prev_store['avg_marketing_cost']) / prev_store['avg_marketing_cost'] * 100):.2f}%")
    else:
        print("\n⚠️ 上期没有该门店的数据")
    
    print("\n" + "=" * 80)
    print("✅ 调试完成")
    print("=" * 80)
    
    session.close()


if __name__ == "__main__":
    debug_week_over_week()
