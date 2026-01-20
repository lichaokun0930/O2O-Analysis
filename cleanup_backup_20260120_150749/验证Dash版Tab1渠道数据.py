#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证Dash版Tab1中渠道统计的具体数据

目标：找出你看到的饿了么5.58和美团共橙5.19是如何计算的
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from database.models import Order

# 测试参数
TEST_STORE = "惠宜选-泰州泰兴店"
START_DATE = datetime(2026, 1, 12)
END_DATE = datetime(2026, 1, 18, 23, 59, 59)

# 收费渠道列表
PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播',
    '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店'
]

def load_data():
    """加载数据"""
    session = SessionLocal()
    try:
        orders = session.query(Order).filter(
            Order.store_name == TEST_STORE,
            Order.date >= START_DATE,
            Order.date <= END_DATE
        ).all()
        
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '日期': order.date,
                '渠道': order.channel,
                '商品名称': order.product_name,
                '一级分类名': order.category_level1,
                '月售': order.quantity if order.quantity is not None else 1,
                '实收价格': float(order.actual_price or 0),
                '商品实售价': float(order.price or 0),
                '商品采购成本': float(order.cost or 0),
                '利润额': float(order.profit or 0),
                '物流配送费': float(order.delivery_fee or 0),
                '平台服务费': float(order.platform_service_fee or 0),
                '平台佣金': float(order.commission or 0),
                '企客后返': float(order.corporate_rebate or 0),
                '用户支付配送费': float(order.user_paid_delivery_fee or 0),
                '配送费减免金额': float(order.delivery_discount or 0),
                '满减金额': float(order.full_reduction or 0),
                '商品减免金额': float(order.product_discount or 0),
                '新客减免金额': float(order.new_customer_discount or 0),
                '商家代金券': float(order.merchant_voucher or 0),
                '商家承担部分券': float(order.merchant_share or 0),
                '满赠金额': float(order.gift_amount or 0),
                '商家其他优惠': float(order.other_merchant_discount or 0),
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()

def calculate_dash_tab1_logic(df):
    """
    完全按照Dash版Tab1的逻辑计算
    
    关键：可能在Tab1中有特殊的过滤或计算逻辑
    """
    print("="*80)
    print("🔍 Dash版Tab1逻辑分析")
    print("="*80)
    
    # Step 1: 订单级聚合
    agg_dict = {
        '商品实售价': 'sum',
        '实收价格': 'sum',
        '月售': 'sum',
        '利润额': 'sum',
        '商品采购成本': 'sum',
        '物流配送费': 'first',
        '平台服务费': 'sum',
        '平台佣金': 'first',
        '企客后返': 'sum',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '满减金额': 'first',
        '商品减免金额': 'first',
        '新客减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',
        '满赠金额': 'first',
        '商家其他优惠': 'first',
        '渠道': 'first',
        '一级分类名': 'first',
    }
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    print(f"\n订单聚合后: {len(order_agg)} 条订单")
    
    # Step 2: 计算商家活动成本
    marketing_fields = ['配送费减免金额', '满减金额', '商品减免金额', '商家代金券', 
                       '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
    order_agg['商家活动成本'] = 0
    for field in marketing_fields:
        if field in order_agg.columns:
            order_agg['商家活动成本'] += order_agg[field].fillna(0)
    
    # Step 3: 过滤异常订单（收费渠道但平台服务费为0）
    print(f"\n过滤前订单数: {len(order_agg)}")
    is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    print(f"异常订单数（收费渠道但服务费为0）: {invalid_orders.sum()}")
    
    order_agg_filtered = order_agg[~invalid_orders].copy()
    print(f"过滤后订单数: {len(order_agg_filtered)}")
    
    # Step 4: 按渠道统计（过滤后）
    print("\n" + "="*80)
    print("📊 按渠道统计（过滤异常订单后）")
    print("="*80)
    
    for channel in ['饿了么', '美团共橙']:
        channel_data = order_agg_filtered[order_agg_filtered['渠道'] == channel]
        
        if len(channel_data) == 0:
            continue
        
        order_count = len(channel_data)
        total_marketing = channel_data['商家活动成本'].sum()
        total_delivery = channel_data['物流配送费'].sum()
        
        avg_marketing = total_marketing / order_count
        avg_delivery = total_delivery / order_count
        
        print(f"\n{channel}:")
        print(f"  订单数: {order_count}")
        print(f"  总营销成本: ¥{total_marketing:.2f}")
        print(f"  总配送费: ¥{total_delivery:.2f}")
        print(f"  单均营销: ¥{avg_marketing:.2f}")
        print(f"  单均配送: ¥{avg_delivery:.2f}")
    
    # Step 5: 尝试其他可能的计算方式
    print("\n" + "="*80)
    print("🔍 尝试其他可能的计算方式")
    print("="*80)
    
    # 可能性1：排除耗材后计算
    print("\n可能性1：排除耗材后计算")
    order_agg_no_consumable = order_agg_filtered[order_agg_filtered['一级分类名'] != '耗材'].copy()
    print(f"排除耗材后订单数: {len(order_agg_no_consumable)}")
    
    for channel in ['饿了么', '美团共橙']:
        channel_data = order_agg_no_consumable[order_agg_no_consumable['渠道'] == channel]
        if len(channel_data) == 0:
            continue
        
        order_count = len(channel_data)
        total_marketing = channel_data['商家活动成本'].sum()
        avg_marketing = total_marketing / order_count
        
        print(f"  {channel}: 单均营销 ¥{avg_marketing:.2f}")
    
    # 可能性2：只计算有营销活动的订单
    print("\n可能性2：只计算有营销活动的订单")
    order_agg_with_marketing = order_agg_filtered[order_agg_filtered['商家活动成本'] > 0].copy()
    print(f"有营销活动的订单数: {len(order_agg_with_marketing)}")
    
    for channel in ['饿了么', '美团共橙']:
        channel_data = order_agg_with_marketing[order_agg_with_marketing['渠道'] == channel]
        if len(channel_data) == 0:
            continue
        
        order_count = len(channel_data)
        total_marketing = channel_data['商家活动成本'].sum()
        avg_marketing = total_marketing / order_count
        
        print(f"  {channel}: 单均营销 ¥{avg_marketing:.2f} (仅有营销活动的订单)")
    
    # 可能性3：按原始数据行计算（不聚合到订单级）
    print("\n可能性3：按原始数据行计算（不聚合）")
    df_filtered = df[df['渠道'].isin(['饿了么', '美团共橙'])].copy()
    
    # 计算每行的营销成本
    df_filtered['商家活动成本'] = 0
    for field in marketing_fields:
        if field in df_filtered.columns:
            df_filtered['商家活动成本'] += df_filtered[field].fillna(0)
    
    for channel in ['饿了么', '美团共橙']:
        channel_data = df_filtered[df_filtered['渠道'] == channel]
        
        row_count = len(channel_data)
        total_marketing = channel_data['商家活动成本'].sum()
        avg_marketing = total_marketing / row_count if row_count > 0 else 0
        
        print(f"  {channel}: 单均营销 ¥{avg_marketing:.2f} (按行计算，共{row_count}行)")

def main():
    """主函数"""
    print("="*80)
    print("🔍 验证Dash版Tab1渠道数据")
    print("="*80)
    print(f"门店: {TEST_STORE}")
    print(f"日期: {START_DATE.date()} ~ {END_DATE.date()}")
    
    df = load_data()
    
    if df.empty:
        print("\n❌ 未找到数据")
        return
    
    print(f"\n✅ 加载完成: {len(df)} 条记录")
    print(f"   订单数: {df['订单ID'].nunique()}")
    
    calculate_dash_tab1_logic(df)
    
    print("\n" + "="*80)
    print("✅ 分析完成")
    print("="*80)
    print("\n💡 结论：")
    print("   如果以上任何一种计算方式的结果接近5.58和5.19，")
    print("   那就说明Dash版Tab1使用了该种计算逻辑。")

if __name__ == "__main__":
    main()
