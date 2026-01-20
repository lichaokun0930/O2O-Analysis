# -*- coding: utf-8 -*-
"""
验证日期范围对计算结果的影响

Dash 版本可能使用的是特定日期范围（如最近7天）
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func

# 收费渠道列表
PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购',
    '抖音', '抖音直播', '淘鲜达', '京东秒送',
    '美团咖啡店', '饿了么咖啡店'
]


def load_store_data_by_date(store_name: str, channel: str, start_date=None, end_date=None) -> pd.DataFrame:
    """加载指定门店和渠道的数据"""
    session = SessionLocal()
    try:
        query = session.query(Order).filter(
            Order.store_name == store_name,
            Order.channel == channel
        )
        
        if start_date:
            query = query.filter(Order.date >= start_date)
        if end_date:
            query = query.filter(Order.date <= end_date)
        
        orders = query.all()
        
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '日期': order.date,
                '渠道': order.channel,
                '物流配送费': float(order.delivery_fee or 0),
                '用户支付配送费': float(order.user_paid_delivery_fee or 0),
                '配送费减免金额': float(order.delivery_discount or 0),
                '企客后返': float(order.corporate_rebate or 0),
                '平台服务费': float(order.platform_service_fee or 0),
                '满减金额': float(order.full_reduction or 0),
                '商品减免金额': float(order.product_discount or 0),
                '商家代金券': float(order.merchant_voucher or 0),
                '商家承担部分券': float(order.merchant_share or 0),
                '满赠金额': float(order.gift_amount or 0),
                '商家其他优惠': float(order.other_merchant_discount or 0),
                '新客减免金额': float(order.new_customer_discount or 0),
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


def calculate_metrics(df: pd.DataFrame) -> dict:
    """计算订单级指标"""
    if df.empty:
        return {'order_count': 0, 'avg_delivery_fee': 0, 'avg_marketing_cost': 0}
    
    # 订单级聚合
    order_agg = df.groupby('订单ID').agg({
        '渠道': 'first',
        '物流配送费': 'first',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '企客后返': 'sum',
        '平台服务费': 'sum',
        '满减金额': 'first',
        '商品减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',
        '满赠金额': 'first',
        '商家其他优惠': 'first',
        '新客减免金额': 'first',
    }).reset_index()
    
    # 过滤异常订单
    is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    order_agg = order_agg[~invalid_orders].copy()
    
    if order_agg.empty:
        return {'order_count': 0, 'avg_delivery_fee': 0, 'avg_marketing_cost': 0}
    
    # 计算配送净成本
    order_agg['配送净成本'] = (
        order_agg['物流配送费'] -
        (order_agg['用户支付配送费'] - order_agg['配送费减免金额']) -
        order_agg['企客后返']
    )
    
    # 计算商家活动成本
    marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', 
                       '满赠金额', '商家其他优惠', '新客减免金额']
    order_agg['商家活动成本'] = sum(order_agg[field].fillna(0) for field in marketing_fields)
    
    order_count = len(order_agg)
    
    return {
        'order_count': order_count,
        'avg_delivery_fee': order_agg['配送净成本'].sum() / order_count if order_count > 0 else 0,
        'avg_marketing_cost': order_agg['商家活动成本'].sum() / order_count if order_count > 0 else 0,
    }


def main():
    store_name = "惠宜选-泰州泰兴店"
    
    # 获取数据库中的日期范围
    session = SessionLocal()
    try:
        max_date = session.query(func.max(Order.date)).filter(
            Order.store_name == store_name
        ).scalar()
        min_date = session.query(func.min(Order.date)).filter(
            Order.store_name == store_name
        ).scalar()
    finally:
        session.close()
    
    print("="*80)
    print(f"验证日期范围影响 - {store_name}")
    print(f"数据日期范围: {min_date} ~ {max_date}")
    print("="*80)
    
    # 测试不同日期范围
    test_ranges = [
        ("全部数据", None, None),
        ("最近7天", max_date - timedelta(days=6), max_date),
        ("最近14天", max_date - timedelta(days=13), max_date),
        ("最近30天", max_date - timedelta(days=29), max_date),
    ]
    
    channels = ['美团共橙', '饿了么']
    
    for range_name, start_date, end_date in test_ranges:
        print(f"\n📊 {range_name}:")
        if start_date and end_date:
            print(f"   日期: {start_date.date()} ~ {end_date.date()}")
        print("-"*60)
        
        for channel in channels:
            df = load_store_data_by_date(store_name, channel, start_date, end_date)
            metrics = calculate_metrics(df)
            
            print(f"  {channel}:")
            print(f"    订单数: {metrics['order_count']}")
            print(f"    单均配送费: ¥{metrics['avg_delivery_fee']:.2f}")
            print(f"    单均营销费: ¥{metrics['avg_marketing_cost']:.2f}")
    
    print("\n" + "="*80)
    print("📋 Dash 版本参考值:")
    print("  美团共橙: 单均配送 ¥3.89")
    print("  饿了么: 单均配送 ¥1.61")
    print("="*80)


if __name__ == "__main__":
    main()
