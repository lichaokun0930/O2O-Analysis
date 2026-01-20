# -*- coding: utf-8 -*-
"""
用商品原价字段计算营销成本率
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
    
    print("=" * 70)
    print(f"用商品原价计算营销成本率 - {STORE_NAME}")
    print(f"日期范围: 2026-01-12 ~ 2026-01-18")
    print(f"用户预期: 12.1%")
    print("=" * 70)
    print(f"\n原始记录数: {len(orders)}")
    
    data = []
    for order in orders:
        data.append({
            '订单ID': order.order_id,
            '商品原价': float(order.original_price or 0),
            '月售': order.quantity if order.quantity is not None else 1,
            # 营销成本7字段
            '满减金额': float(order.full_reduction or 0),
            '商品减免金额': float(order.product_discount or 0),
            '商家代金券': float(order.merchant_voucher or 0),
            '商家承担部分券': float(order.merchant_share or 0),
            '满赠金额': float(order.gift_amount or 0),
            '商家其他优惠': float(order.other_merchant_discount or 0),
            '新客减免金额': float(order.new_customer_discount or 0),
        })
    
    df = pd.DataFrame(data)
    
    # 计算商品原价×销量
    df['原价销售额'] = df['商品原价'] * df['月售']
    
    # 按订单聚合
    order_agg = df.groupby('订单ID').agg({
        '商品原价': 'sum',  # 商品级字段sum
        '原价销售额': 'sum',  # 商品级字段sum
        '满减金额': 'first',  # 订单级字段first
        '商品减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',
        '满赠金额': 'first',
        '商家其他优惠': 'first',
        '新客减免金额': 'first',
    }).reset_index()
    
    total_orders = len(order_agg)
    print(f"订单数: {total_orders}")
    
    # 计算营销成本（7字段）
    marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', 
                        '满赠金额', '商家其他优惠', '新客减免金额']
    order_agg['营销成本'] = sum(order_agg[f].fillna(0) for f in marketing_fields)
    
    total_marketing = order_agg['营销成本'].sum()
    total_original_price = order_agg['商品原价'].sum()
    total_original_sales = order_agg['原价销售额'].sum()
    
    print(f"\n商品原价 sum: ¥{total_original_price:,.2f}")
    print(f"商品原价×销量 sum: ¥{total_original_sales:,.2f}")
    print(f"营销成本(7字段): ¥{total_marketing:,.2f}")
    
    # 计算营销成本率
    rate1 = total_marketing / total_original_price * 100 if total_original_price > 0 else 0
    rate2 = total_marketing / total_original_sales * 100 if total_original_sales > 0 else 0
    
    print(f"\n" + "=" * 70)
    print(f"营销成本率计算结果:")
    print("=" * 70)
    print(f"方案1: 营销成本 / 商品原价 = {total_marketing:,.2f} / {total_original_price:,.2f} = {rate1:.2f}%")
    print(f"方案2: 营销成本 / (商品原价×销量) = {total_marketing:,.2f} / {total_original_sales:,.2f} = {rate2:.2f}%")
    
    print(f"\n与12.1%的差异:")
    print(f"方案1差异: {abs(rate1 - 12.1):.2f}个百分点")
    print(f"方案2差异: {abs(rate2 - 12.1):.2f}个百分点")
    
finally:
    session.close()
