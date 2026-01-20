#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比Dash版和React版的单均营销和单均配送计算差异

测试门店：泰州泰兴店
测试日期：2025-01-12 ~ 2025-01-18
测试渠道：饿了么、美团共橙

预期结果（Dash版）：
- 饿了么：单均营销 5.58，单均配送 1.61
- 美团共橙：单均营销 5.19，单均配送 3.89

实际结果（React版）：
- 全渠道：单均营销 8.7，单均配送 4.6
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from database.models import Order

# 测试参数
TEST_STORE = "惠宜选-泰州泰兴店"
START_DATE = datetime(2026, 1, 12)
END_DATE = datetime(2026, 1, 18, 23, 59, 59)

def load_test_data():
    """加载测试数据"""
    print("="*80)
    print(f"📊 加载测试数据")
    print("="*80)
    print(f"门店: {TEST_STORE}")
    print(f"日期: {START_DATE.date()} ~ {END_DATE.date()}")
    
    session = SessionLocal()
    try:
        orders = session.query(Order).filter(
            Order.store_name == TEST_STORE,
            Order.date >= START_DATE,
            Order.date <= END_DATE
        ).all()
        
        if not orders:
            print("❌ 未找到测试数据")
            return pd.DataFrame()
        
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '日期': order.date,
                '渠道': order.channel,
                '商品名称': order.product_name,
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
        
        df = pd.DataFrame(data)
        print(f"✅ 加载完成: {len(df)} 条记录")
        print(f"   订单数: {df['订单ID'].nunique()}")
        print(f"   渠道: {df['渠道'].unique().tolist()}")
        
        return df
    finally:
        session.close()

def dash_version_calculation(df):
    """Dash版本的计算逻辑"""
    print("\n" + "="*80)
    print("📊 Dash版本计算逻辑")
    print("="*80)
    
    if df.empty:
        return
    
    # Step 1: 订单级聚合
    agg_dict = {
        '商品实售价': 'sum',
        '实收价格': 'sum',
        '月售': 'sum',
        '利润额': 'sum',
        '物流配送费': 'first',
        '平台服务费': 'sum',
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
        '门店名称': 'first',
    }
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    
    # Step 2: 计算商家活动成本（8个营销字段）
    marketing_fields = ['配送费减免金额', '满减金额', '商品减免金额', '商家代金券', 
                       '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
    order_agg['商家活动成本'] = 0
    for field in marketing_fields:
        if field in order_agg.columns:
            order_agg['商家活动成本'] += order_agg[field].fillna(0)
    
    # Step 3: 按渠道统计
    print("\n按渠道统计:")
    print("-"*80)
    
    for channel in order_agg['渠道'].unique():
        channel_data = order_agg[order_agg['渠道'] == channel]
        
        order_count = len(channel_data)
        total_marketing = channel_data['商家活动成本'].sum()
        total_delivery = channel_data['物流配送费'].sum()
        
        avg_marketing = total_marketing / order_count if order_count > 0 else 0
        avg_delivery = total_delivery / order_count if order_count > 0 else 0
        
        print(f"\n{channel}:")
        print(f"  订单数: {order_count}")
        print(f"  总营销成本: ¥{total_marketing:.2f}")
        print(f"  总配送费: ¥{total_delivery:.2f}")
        print(f"  单均营销: ¥{avg_marketing:.2f}")
        print(f"  单均配送: ¥{avg_delivery:.2f}")
        
        # 详细分解营销成本
        print(f"\n  营销成本明细:")
        for field in marketing_fields:
            if field in channel_data.columns:
                field_sum = channel_data[field].sum()
                print(f"    {field}: ¥{field_sum:.2f}")
    
    # 全渠道统计
    print(f"\n全渠道合计:")
    print("-"*80)
    total_orders = len(order_agg)
    total_marketing_all = order_agg['商家活动成本'].sum()
    total_delivery_all = order_agg['物流配送费'].sum()
    
    avg_marketing_all = total_marketing_all / total_orders if total_orders > 0 else 0
    avg_delivery_all = total_delivery_all / total_orders if total_orders > 0 else 0
    
    print(f"  订单数: {total_orders}")
    print(f"  总营销成本: ¥{total_marketing_all:.2f}")
    print(f"  总配送费: ¥{total_delivery_all:.2f}")
    print(f"  单均营销: ¥{avg_marketing_all:.2f}")
    print(f"  单均配送: ¥{avg_delivery_all:.2f}")

def react_version_calculation(df):
    """React版本的计算逻辑（使用calculate_order_metrics）"""
    print("\n" + "="*80)
    print("📊 React版本计算逻辑")
    print("="*80)
    
    if df.empty:
        return
    
    # 导入React版本的计算函数
    sys.path.insert(0, str(PROJECT_ROOT / 'backend'))
    from app.api.v1.orders import calculate_order_metrics
    
    # 使用React版本的计算函数
    order_agg = calculate_order_metrics(df)
    
    if order_agg.empty:
        print("❌ 订单聚合失败")
        return
    
    print(f"\n订单聚合后: {len(order_agg)} 条订单")
    
    # 检查关键字段
    print(f"\n关键字段检查:")
    print(f"  商家活动成本字段存在: {'商家活动成本' in order_agg.columns}")
    print(f"  物流配送费字段存在: {'物流配送费' in order_agg.columns}")
    
    if '商家活动成本' not in order_agg.columns:
        print("❌ 缺少商家活动成本字段")
        return
    
    # 按渠道统计
    print("\n按渠道统计:")
    print("-"*80)
    
    if '渠道' in order_agg.columns:
        for channel in order_agg['渠道'].unique():
            channel_data = order_agg[order_agg['渠道'] == channel]
            
            order_count = len(channel_data)
            total_marketing = channel_data['商家活动成本'].sum()
            total_delivery = channel_data['物流配送费'].sum() if '物流配送费' in channel_data.columns else 0
            
            avg_marketing = total_marketing / order_count if order_count > 0 else 0
            avg_delivery = total_delivery / order_count if order_count > 0 else 0
            
            print(f"\n{channel}:")
            print(f"  订单数: {order_count}")
            print(f"  总营销成本: ¥{total_marketing:.2f}")
            print(f"  总配送费: ¥{total_delivery:.2f}")
            print(f"  单均营销: ¥{avg_marketing:.2f}")
            print(f"  单均配送: ¥{avg_delivery:.2f}")
    
    # 全渠道统计
    print(f"\n全渠道合计:")
    print("-"*80)
    total_orders = len(order_agg)
    total_marketing_all = order_agg['商家活动成本'].sum()
    total_delivery_all = order_agg['物流配送费'].sum() if '物流配送费' in order_agg.columns else 0
    
    avg_marketing_all = total_marketing_all / total_orders if total_orders > 0 else 0
    avg_delivery_all = total_delivery_all / total_orders if total_orders > 0 else 0
    
    print(f"  订单数: {total_orders}")
    print(f"  总营销成本: ¥{total_marketing_all:.2f}")
    print(f"  总配送费: ¥{total_delivery_all:.2f}")
    print(f"  单均营销: ¥{avg_marketing_all:.2f}")
    print(f"  单均配送: ¥{avg_delivery_all:.2f}")

def compare_results():
    """对比两个版本的结果"""
    print("\n" + "="*80)
    print("📊 结果对比")
    print("="*80)
    
    print("\n预期结果（Dash版）：")
    print("  饿了么：单均营销 5.58，单均配送 1.61")
    print("  美团共橙：单均营销 5.19，单均配送 3.89")
    
    print("\n实际结果（React版）：")
    print("  全渠道：单均营销 8.7，单均配送 4.6")
    
    print("\n可能的差异原因：")
    print("  1. 订单级聚合逻辑不同（first vs sum）")
    print("  2. 营销字段的聚合方式不同")
    print("  3. 异常订单过滤逻辑不同")
    print("  4. 配送费计算逻辑不同（净成本 vs 总费用）")

def main():
    """主函数"""
    print("="*80)
    print("🔍 Dash版 vs React版 单均营销和单均配送计算对比")
    print("="*80)
    
    # 加载测试数据
    df = load_test_data()
    
    if df.empty:
        print("\n❌ 无法加载测试数据，请检查数据库连接和数据")
        return
    
    # Dash版本计算
    dash_version_calculation(df.copy())
    
    # React版本计算
    react_version_calculation(df.copy())
    
    # 对比结果
    compare_results()
    
    print("\n" + "="*80)
    print("✅ 对比完成")
    print("="*80)

if __name__ == "__main__":
    main()
