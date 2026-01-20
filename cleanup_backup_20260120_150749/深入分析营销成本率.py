# -*- coding: utf-8 -*-
"""
深入分析营销成本率差异

用户预期: 12.1%
系统计算: 16.77%

分析不同计算方式的结果
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
    
    print(f"门店: {STORE_NAME}")
    print(f"日期: 2026-01-12 ~ 2026-01-18")
    print(f"原始记录数: {len(orders)}")
    print()
    
    # 转换为DataFrame
    data = []
    for order in orders:
        data.append({
            '订单ID': order.order_id,
            '实收价格': float(order.actual_price or 0),
            '商品实售价': float(order.price or 0),
            '预计订单收入': float(order.amount or 0),
            '月售': order.quantity if order.quantity is not None else 1,
            '满减金额': float(order.full_reduction or 0),
            '商品减免金额': float(order.product_discount or 0),
            '商家代金券': float(order.merchant_voucher or 0),
            '商家承担部分券': float(order.merchant_share or 0),
            '满赠金额': float(order.gift_amount or 0),
            '商家其他优惠': float(order.other_merchant_discount or 0),
            '新客减免金额': float(order.new_customer_discount or 0),
            '配送费减免金额': float(order.delivery_discount or 0),
        })
    
    df = pd.DataFrame(data)
    
    # 计算不同的销售额
    df['销售额_实收x月售'] = df['实收价格'] * df['月售']
    df['销售额_实售价x月售'] = df['商品实售价'] * df['月售']
    df['销售额_预计收入'] = df['预计订单收入']
    
    # 按订单聚合
    order_agg = df.groupby('订单ID').agg({
        '销售额_实收x月售': 'sum',
        '销售额_实售价x月售': 'sum',
        '销售额_预计收入': 'first',  # 订单级字段
        '满减金额': 'first',
        '商品减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',
        '满赠金额': 'first',
        '商家其他优惠': 'first',
        '新客减免金额': 'first',
        '配送费减免金额': 'first',
    }).reset_index()
    
    # 计算营销成本（7字段）
    marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', 
                       '满赠金额', '商家其他优惠', '新客减免金额']
    order_agg['营销成本'] = sum(order_agg[f].fillna(0) for f in marketing_fields)
    
    # 汇总
    total_orders = len(order_agg)
    total_marketing = order_agg['营销成本'].sum()
    
    print(f"订单数: {total_orders}")
    print(f"营销成本(7字段): ¥{total_marketing:,.2f}")
    print()
    
    # 不同销售额计算方式
    print("=" * 60)
    print("不同销售额计算方式对营销成本率的影响")
    print("=" * 60)
    
    sales_methods = [
        ('实收价格 × 月售', order_agg['销售额_实收x月售'].sum()),
        ('商品实售价 × 月售', order_agg['销售额_实售价x月售'].sum()),
        ('预计订单收入', order_agg['销售额_预计收入'].sum()),
    ]
    
    print(f"\n| 销售额计算方式 | 销售额 | 营销成本率 |")
    print(f"|---------------|--------|-----------|")
    for method, sales in sales_methods:
        rate = (total_marketing / sales * 100) if sales > 0 else 0
        print(f"| {method} | ¥{sales:,.2f} | {rate:.2f}% |")
    
    # 如果用户预期是12.1%，反推销售额
    print()
    print("=" * 60)
    print("反推分析")
    print("=" * 60)
    expected_rate = 12.1
    expected_sales = total_marketing / (expected_rate / 100)
    print(f"\n如果营销成本率 = {expected_rate}%")
    print(f"则销售额应为: ¥{expected_sales:,.2f}")
    print(f"当前销售额(实收×月售): ¥{order_agg['销售额_实收x月售'].sum():,.2f}")
    print(f"差异: ¥{expected_sales - order_agg['销售额_实收x月售'].sum():,.2f}")
    
finally:
    session.close()
