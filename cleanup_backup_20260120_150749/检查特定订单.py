# -*- coding: utf-8 -*-
"""
检查用户提供的11个订单
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

# 用户提供的11个订单ID
USER_ORDER_IDS = [
    '2277931284', '2277949046', '2277974124', '2277980066', '2278009970',
    '2278099034', '2278160587', '2278160754', '2278221720', '2278276356', '2278483878'
]

def check():
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
                '订单ID': str(order.order_id),
                '商品名称': order.product_name,
                '商品原价': float(order.original_price or 0),
                '月售': order.quantity if order.quantity is not None else 1,
                '打包袋金额': float(order.packaging_fee or 0),
                '用户支付配送费': float(order.user_paid_delivery_fee or 0),
            })
        
        df = pd.DataFrame(data)
        
        print("=" * 70)
        print("检查用户提供的11个订单")
        print("=" * 70)
        
        # 检查这些订单是否存在
        found_orders = df[df['订单ID'].isin(USER_ORDER_IDS)]
        print(f"\n在数据库中找到的订单数: {found_orders['订单ID'].nunique()}")
        
        if found_orders.empty:
            print("❌ 未找到任何订单！")
            print(f"\n数据库中的订单ID样例:")
            print(df['订单ID'].head(20).tolist())
            return
        
        # 详细列出每个订单
        print(f"\n订单详情:")
        print("-" * 70)
        
        total_packaging = 0
        total_delivery = 0
        
        for order_id in USER_ORDER_IDS:
            order_rows = df[df['订单ID'] == order_id]
            if order_rows.empty:
                print(f"订单 {order_id}: ❌ 未找到")
                continue
            
            packaging = order_rows['打包袋金额'].iloc[0]
            delivery = order_rows['用户支付配送费'].iloc[0]
            original_prices = order_rows['商品原价'].tolist()
            
            total_packaging += packaging
            total_delivery += delivery
            
            print(f"订单 {order_id}:")
            print(f"  商品原价列表: {original_prices}")
            print(f"  打包袋金额: {packaging}")
            print(f"  用户支付配送费: {delivery}")
        
        print("-" * 70)
        print(f"合计: 打包袋={total_packaging}, 配送费={total_delivery}, 总计={total_packaging + total_delivery}")
        
    finally:
        session.close()

if __name__ == "__main__":
    check()
