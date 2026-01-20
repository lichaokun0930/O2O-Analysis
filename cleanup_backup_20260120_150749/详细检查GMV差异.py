# -*- coding: utf-8 -*-
"""
详细检查GMV差异 - 分析商品原价<0的订单
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

def check_gmv_details():
    session = SessionLocal()
    
    try:
        test_date = datetime.strptime(TEST_DATE, "%Y-%m-%d").date()
        
        orders = session.query(Order).filter(
            Order.store_name == STORE_NAME,
            cast(Order.date, Date) == test_date
        ).all()
        
        print(f"=" * 70)
        print(f"详细检查GMV差异 - {STORE_NAME}")
        print(f"日期: {TEST_DATE}")
        print(f"=" * 70)
        
        # 转换为DataFrame
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
        
        print(f"\n原始数据统计:")
        print(f"  总记录数: {len(df)}")
        print(f"  唯一订单数: {df['订单ID'].nunique()}")
        
        # 检查商品原价<0的情况
        negative_price = df[df['商品原价'] < 0]
        print(f"\n商品原价<0的记录:")
        print(f"  记录数: {len(negative_price)}")
        
        if len(negative_price) > 0:
            # 找出包含商品原价<0的订单
            orders_with_negative = negative_price['订单ID'].unique()
            print(f"  涉及订单数: {len(orders_with_negative)}")
            
            # 这些订单的打包袋金额和用户支付配送费
            affected_orders = df[df['订单ID'].isin(orders_with_negative)]
            affected_packaging = affected_orders.groupby('订单ID')['打包袋金额'].first().sum()
            affected_delivery = affected_orders.groupby('订单ID')['用户支付配送费'].first().sum()
            
            print(f"\n  这些订单的打包袋金额总计: ¥{affected_packaging:.2f}")
            print(f"  这些订单的用户支付配送费总计: ¥{affected_delivery:.2f}")
            print(f"  合计影响: ¥{affected_packaging + affected_delivery:.2f}")
            
            # 显示具体订单
            print(f"\n  具体订单明细:")
            for order_id in orders_with_negative[:5]:  # 只显示前5个
                order_data = df[df['订单ID'] == order_id]
                packaging = order_data['打包袋金额'].iloc[0]
                delivery = order_data['用户支付配送费'].iloc[0]
                neg_items = order_data[order_data['商品原价'] < 0]
                print(f"    订单 {order_id}:")
                print(f"      商品数: {len(order_data)}, 负价商品数: {len(neg_items)}")
                print(f"      打包袋金额: ¥{packaging:.2f}, 用户支付配送费: ¥{delivery:.2f}")
        
        # ==================== 正确的GMV计算（剔除整行） ====================
        print(f"\n" + "=" * 70)
        print("正确的GMV计算（剔除商品原价<0的整行）:")
        print("=" * 70)
        
        # 剔除商品原价<0的整行
        df_clean = df[df['商品原价'] >= 0].copy()
        print(f"\n剔除后记录数: {len(df_clean)}")
        print(f"剔除后唯一订单数: {df_clean['订单ID'].nunique()}")
        
        # 计算各部分
        df_clean['原价销售额'] = df_clean['商品原价'] * df_clean['月售']
        original_price_sales = df_clean['原价销售额'].sum()
        
        # 用清洗后的数据计算订单级字段
        order_level = df_clean.groupby('订单ID').agg({
            '打包袋金额': 'first',
            '用户支付配送费': 'first',
        }).reset_index()
        
        packaging_fee = order_level['打包袋金额'].sum()
        user_delivery_fee = order_level['用户支付配送费'].sum()
        
        gmv = original_price_sales + packaging_fee + user_delivery_fee
        
        print(f"\nGMV各部分:")
        print(f"  商品原价销售额: ¥{original_price_sales:.2f}")
        print(f"  打包袋金额: ¥{packaging_fee:.2f}")
        print(f"  用户支付配送费: ¥{user_delivery_fee:.2f}")
        print(f"  GMV合计: ¥{gmv:.2f}")
        
        print(f"\n用户预期GMV: ¥8,440.66")
        print(f"差异: ¥{gmv - 8440.66:.2f}")
        
    finally:
        session.close()


if __name__ == "__main__":
    check_gmv_details()
