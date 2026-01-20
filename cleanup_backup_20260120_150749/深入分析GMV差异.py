# -*- coding: utf-8 -*-
"""
深入分析GMV差异 - 检查各种可能的清洗规则
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
EXPECTED_GMV = 8440.66

def analyze_gmv_difference():
    session = SessionLocal()
    
    try:
        test_date = datetime.strptime(TEST_DATE, "%Y-%m-%d").date()
        
        orders = session.query(Order).filter(
            Order.store_name == STORE_NAME,
            cast(Order.date, Date) == test_date
        ).all()
        
        print(f"=" * 70)
        print(f"深入分析GMV差异 - {STORE_NAME}")
        print(f"日期: {TEST_DATE}")
        print(f"用户预期GMV: ¥{EXPECTED_GMV:,.2f}")
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
                '一级分类名': order.category_level1,
            })
        
        df = pd.DataFrame(data)
        
        # 基础统计
        print(f"\n原始数据:")
        print(f"  总记录数: {len(df)}")
        print(f"  唯一订单数: {df['订单ID'].nunique()}")
        
        # 检查商品原价=0的情况
        zero_price = df[df['商品原价'] == 0]
        print(f"\n商品原价=0的记录: {len(zero_price)}")
        if len(zero_price) > 0:
            print(f"  涉及订单数: {zero_price['订单ID'].nunique()}")
            # 这些订单的打包袋和配送费
            zero_orders = zero_price['订单ID'].unique()
            zero_order_data = df[df['订单ID'].isin(zero_orders)]
            zero_packaging = zero_order_data.groupby('订单ID')['打包袋金额'].first().sum()
            zero_delivery = zero_order_data.groupby('订单ID')['用户支付配送费'].first().sum()
            print(f"  这些订单的打包袋金额: ¥{zero_packaging:.2f}")
            print(f"  这些订单的用户支付配送费: ¥{zero_delivery:.2f}")
        
        # 检查耗材分类
        if '一级分类名' in df.columns:
            consumables = df[df['一级分类名'] == '耗材']
            print(f"\n耗材分类记录: {len(consumables)}")
            if len(consumables) > 0:
                print(f"  涉及订单数: {consumables['订单ID'].nunique()}")
                consumable_orders = consumables['订单ID'].unique()
                consumable_data = df[df['订单ID'].isin(consumable_orders)]
                consumable_packaging = consumable_data.groupby('订单ID')['打包袋金额'].first().sum()
                consumable_delivery = consumable_data.groupby('订单ID')['用户支付配送费'].first().sum()
                print(f"  这些订单的打包袋金额: ¥{consumable_packaging:.2f}")
                print(f"  这些订单的用户支付配送费: ¥{consumable_delivery:.2f}")
        
        # 尝试不同的清洗规则
        print(f"\n" + "=" * 70)
        print("尝试不同的清洗规则:")
        print("=" * 70)
        
        def calc_gmv(df_input, desc):
            df_calc = df_input.copy()
            df_calc['原价销售额'] = df_calc['商品原价'] * df_calc['月售']
            original_sales = df_calc['原价销售额'].sum()
            order_level = df_calc.groupby('订单ID').agg({
                '打包袋金额': 'first',
                '用户支付配送费': 'first',
            }).reset_index()
            packaging = order_level['打包袋金额'].sum()
            delivery = order_level['用户支付配送费'].sum()
            gmv = original_sales + packaging + delivery
            diff = gmv - EXPECTED_GMV
            print(f"\n{desc}:")
            print(f"  记录数: {len(df_calc)}, 订单数: {df_calc['订单ID'].nunique()}")
            print(f"  原价销售额: ¥{original_sales:.2f}")
            print(f"  打包袋: ¥{packaging:.2f}, 配送费: ¥{delivery:.2f}")
            print(f"  GMV: ¥{gmv:.2f} (差异: {diff:+.2f})")
            return gmv
        
        # 方案1: 原始数据（无清洗）
        calc_gmv(df, "方案1: 原始数据（无清洗）")
        
        # 方案2: 剔除商品原价<0
        df2 = df[df['商品原价'] >= 0]
        calc_gmv(df2, "方案2: 剔除商品原价<0")
        
        # 方案3: 剔除商品原价<=0
        df3 = df[df['商品原价'] > 0]
        calc_gmv(df3, "方案3: 剔除商品原价<=0（即原价>0）")
        
        # 方案4: 剔除耗材
        if '一级分类名' in df.columns:
            df4 = df[df['一级分类名'] != '耗材']
            calc_gmv(df4, "方案4: 剔除耗材分类")
        
        # 方案5: 剔除商品原价<=0 且 剔除耗材
        if '一级分类名' in df.columns:
            df5 = df[(df['商品原价'] > 0) & (df['一级分类名'] != '耗材')]
            calc_gmv(df5, "方案5: 剔除原价<=0 且 剔除耗材")
        
        # 方案6: 剔除商品原价<0 且 剔除耗材
        if '一级分类名' in df.columns:
            df6 = df[(df['商品原价'] >= 0) & (df['一级分类名'] != '耗材')]
            calc_gmv(df6, "方案6: 剔除原价<0 且 剔除耗材")
        
        # 方案7: 剔除销量=0的记录
        df7 = df[df['月售'] > 0]
        calc_gmv(df7, "方案7: 剔除销量=0")
        
        # 方案8: 剔除原价<0 且 销量=0
        df8 = df[(df['商品原价'] >= 0) & (df['月售'] > 0)]
        calc_gmv(df8, "方案8: 剔除原价<0 且 销量=0")
        
    finally:
        session.close()


if __name__ == "__main__":
    analyze_gmv_difference()
