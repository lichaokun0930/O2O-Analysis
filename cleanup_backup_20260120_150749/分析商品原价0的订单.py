# -*- coding: utf-8 -*-
"""
分析商品原价=0的订单结构
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from database.connection import SessionLocal
from database.models import Order
import pandas as pd
from datetime import datetime
from sqlalchemy import cast, Date

STORE_NAME = "惠宜选超市（昆山淀山湖镇店）"
TEST_DATE = "2026-01-18"

def analyze():
    session = SessionLocal()
    try:
        test_date = datetime.strptime(TEST_DATE, "%Y-%m-%d").date()
        
        orders = session.query(Order).filter(
            Order.store_name == STORE_NAME,
            cast(Order.date, Date) == test_date
        ).all()
        
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '商品名称': order.product_name,
                '商品原价': float(order.original_price or 0),
                '月售': order.quantity if order.quantity is not None else 1,
                '打包袋金额': float(order.packaging_fee or 0),
                '用户支付配送费': float(order.user_paid_delivery_fee or 0),
            })
        
        df = pd.DataFrame(data)
        
        print("=" * 70)
        print("分析商品原价=0的订单")
        print("=" * 70)
        
        # 找出商品原价=0的行
        zero_price_rows = df[df['商品原价'] == 0]
        print(f"\n商品原价=0的行数: {len(zero_price_rows)}")
        
        # 找出这些行对应的唯一订单ID
        zero_price_order_ids = zero_price_rows['订单ID'].unique()
        print(f"涉及的唯一订单数: {len(zero_price_order_ids)}")
        
        # 检查这些订单是否还有其他商品原价>0的行
        print(f"\n检查这些订单的商品结构:")
        
        orders_with_only_zero = []  # 只有商品原价=0的订单
        orders_with_mixed = []  # 既有=0也有>0的订单
        
        for order_id in zero_price_order_ids:
            order_rows = df[df['订单ID'] == order_id]
            has_positive = (order_rows['商品原价'] > 0).any()
            
            if has_positive:
                orders_with_mixed.append(order_id)
            else:
                orders_with_only_zero.append(order_id)
        
        print(f"\n只有商品原价<=0的订单数: {len(orders_with_only_zero)}")
        print(f"既有商品原价=0也有>0的订单数: {len(orders_with_mixed)}")
        
        # 详细列出只有商品原价=0的订单
        print(f"\n只有商品原价<=0的订单详情:")
        print("-" * 70)
        
        total_packaging = 0
        total_delivery = 0
        
        for order_id in orders_with_only_zero:
            order_rows = df[df['订单ID'] == order_id]
            packaging = order_rows['打包袋金额'].iloc[0]
            delivery = order_rows['用户支付配送费'].iloc[0]
            total_packaging += packaging
            total_delivery += delivery
            print(f"订单 {order_id}: 打包袋={packaging}, 配送费={delivery}")
        
        print("-" * 70)
        print(f"合计: 打包袋={total_packaging}, 配送费={total_delivery}, 总计={total_packaging + total_delivery}")
        
        # 这才是应该剔除的金额
        print(f"\n✅ 应该从GMV中剔除的金额: ¥{total_packaging + total_delivery:.2f}")
        
    finally:
        session.close()

if __name__ == "__main__":
    analyze()
