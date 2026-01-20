# -*- coding: utf-8 -*-
"""
多维度营销成本率分析

使用所有可能的销售额字段计算营销成本率，
帮助确定哪个计算方式与用户预期的12.1%最接近
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from datetime import datetime
from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import and_

STORE_NAME = "惠宜选-徐州沛县店"

session = SessionLocal()
try:
    start_date = datetime(2026, 1, 12)
    end_date = datetime(2026, 1, 18, 23, 59, 59)
    
    orders = session.query(Order).filter(
        and_(
            Order.store_name == STORE_NAME,
            Order.date >= start_date,
            Order.date <= end_date
        )
    ).all()
    
    print("=" * 80)
    print(f"多维度营销成本率分析 - {STORE_NAME}")
    print(f"日期范围: 2026-01-12 ~ 2026-01-18")
    print(f"用户预期营销成本率: 12.1%")
    print("=" * 80)
    print(f"\n原始记录数: {len(orders)}")
    
    # 转换为DataFrame，包含所有可能的销售额字段
    data = []
    for order in orders:
        data.append({
            '订单ID': order.order_id,
            # 销售额相关字段
            '实收价格': float(order.actual_price or 0),
            '商品实售价': float(order.price or 0),
            '预计订单收入': float(order.amount or 0),
            '月售': order.quantity if order.quantity is not None else 1,
            # 营销成本字段
            '满减金额': float(order.full_reduction or 0),
            '商品减免金额': float(order.product_discount or 0),
            '商家代金券': float(order.merchant_voucher or 0),
            '商家承担部分券': float(order.merchant_share or 0),
            '满赠金额': float(order.gift_amount or 0),
            '商家其他优惠': float(order.other_merchant_discount or 0),
            '新客减免金额': float(order.new_customer_discount or 0),
            '配送费减免金额': float(order.delivery_discount or 0),
            # 其他可能的金额字段
            '利润额': float(order.profit or 0),
            '商品采购成本': float(order.cost or 0),
        })
    
    df = pd.DataFrame(data)
    
    # 计算各种销售额
    df['销售额_实收x月售'] = df['实收价格'] * df['月售']
    df['销售额_实售价x月售'] = df['商品实售价'] * df['月售']
    
    # 按订单聚合
    order_agg = df.groupby('订单ID').agg({
        '销售额_实收x月售': 'sum',
        '销售额_实售价x月售': 'sum',
        '预计订单收入': 'first',
        '利润额': 'sum',
        '商品采购成本': 'sum',
        '满减金额': 'first',
        '商品减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',
        '满赠金额': 'first',
        '商家其他优惠': 'first',
        '新客减免金额': 'first',
        '配送费减免金额': 'first',
    }).reset_index()
    
    total_orders = len(order_agg)
    print(f"订单数: {total_orders}")
    
    # 计算不同的营销成本组合
    marketing_7 = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', 
                   '满赠金额', '商家其他优惠', '新客减免金额']
    marketing_8 = marketing_7 + ['配送费减免金额']
    
    order_agg['营销成本_7字段'] = sum(order_agg[f].fillna(0) for f in marketing_7)
    order_agg['营销成本_8字段'] = sum(order_agg[f].fillna(0) for f in marketing_8)
    
    total_marketing_7 = order_agg['营销成本_7字段'].sum()
    total_marketing_8 = order_agg['营销成本_8字段'].sum()
    
    print(f"\n营销成本(7字段，不含配送减免): ¥{total_marketing_7:,.2f}")
    print(f"营销成本(8字段，含配送减免): ¥{total_marketing_8:,.2f}")
    
    # 各种销售额维度
    sales_dimensions = {
        '实收价格 × 月售': order_agg['销售额_实收x月售'].sum(),
        '商品实售价 × 月售': order_agg['销售额_实售价x月售'].sum(),
        '预计订单收入(订单级)': order_agg['预计订单收入'].sum(),
        '利润额 + 成本': order_agg['利润额'].sum() + order_agg['商品采购成本'].sum(),
    }
    
    # 计算原价（实收 + 所有折扣）
    all_discounts = order_agg['营销成本_8字段'].sum()
    sales_dimensions['实收 + 全部折扣(推算原价)'] = order_agg['销售额_实收x月售'].sum() + all_discounts
    
    print("\n" + "=" * 80)
    print("不同销售额维度 × 不同营销成本组合 的营销成本率")
    print("=" * 80)
    
    print(f"\n{'销售额维度':<30} | {'销售额':>15} | {'7字段成本率':>12} | {'8字段成本率':>12}")
    print("-" * 80)
    
    results = []
    for name, sales in sales_dimensions.items():
        rate_7 = (total_marketing_7 / sales * 100) if sales > 0 else 0
        rate_8 = (total_marketing_8 / sales * 100) if sales > 0 else 0
        print(f"{name:<30} | ¥{sales:>12,.2f} | {rate_7:>10.2f}% | {rate_8:>10.2f}%")
        results.append({
            'name': name,
            'sales': sales,
            'rate_7': rate_7,
            'rate_8': rate_8,
            'diff_7': abs(rate_7 - 12.1),
            'diff_8': abs(rate_8 - 12.1)
        })
    
    # 找出最接近12.1%的组合
    print("\n" + "=" * 80)
    print("与用户预期(12.1%)最接近的组合")
    print("=" * 80)
    
    # 按差异排序
    all_combinations = []
    for r in results:
        all_combinations.append({'name': r['name'], 'type': '7字段', 'rate': r['rate_7'], 'diff': r['diff_7']})
        all_combinations.append({'name': r['name'], 'type': '8字段', 'rate': r['rate_8'], 'diff': r['diff_8']})
    
    all_combinations.sort(key=lambda x: x['diff'])
    
    print(f"\n{'排名':<4} | {'销售额维度':<30} | {'营销成本':<8} | {'成本率':>10} | {'与12.1%差异':>12}")
    print("-" * 80)
    for i, c in enumerate(all_combinations[:6], 1):
        print(f"{i:<4} | {c['name']:<30} | {c['type']:<8} | {c['rate']:>8.2f}% | {c['diff']:>10.2f}%")
    
    # 详细字段明细
    print("\n" + "=" * 80)
    print("营销成本各字段明细")
    print("=" * 80)
    
    for field in marketing_8:
        total = order_agg[field].sum()
        pct = (total / total_marketing_8 * 100) if total_marketing_8 > 0 else 0
        print(f"{field:<20}: ¥{total:>10,.2f} ({pct:>5.1f}%)")
    
finally:
    session.close()
