# -*- coding: utf-8 -*-
"""
验证 API 修复效果

模拟 store_comparison API 的计算逻辑，验证单均配送费修复
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

# 导入修复后的函数
from backend.app.api.v1.orders import calculate_order_metrics


def get_all_stores_data(start_date=None, end_date=None, channel=None):
    """模拟 store_comparison.py 中的 get_all_stores_data 函数"""
    CHANNEL_PREFIX_MAP = {
        '美团': 'SG',
        '饿了么': 'ELE',
        '京东': 'JD'
    }
    
    session = SessionLocal()
    try:
        query = session.query(Order)
        
        if start_date:
            query = query.filter(Order.date >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(Order.date <= datetime.combine(end_date, datetime.max.time()))
        
        if channel and channel in CHANNEL_PREFIX_MAP:
            prefix = CHANNEL_PREFIX_MAP[channel]
            query = query.filter(Order.order_number.like(f'{prefix}%'))
        
        orders = query.all()
        
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '日期': order.date,
                '渠道': order.channel,
                '月售': order.quantity if order.quantity is not None else 1,
                '实收价格': float(order.actual_price or 0),
                '商品实售价': float(order.price or 0),
                '商品采购成本': float(order.cost or 0),
                '利润额': float(order.profit or 0),
                '物流配送费': float(order.delivery_fee or 0),
                '平台服务费': float(order.platform_service_fee or 0),
                '平台佣金': float(order.commission or 0),
                '预计订单收入': float(order.amount or 0),
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


def calculate_store_metrics(df):
    """模拟修复后的 calculate_store_metrics 函数"""
    if df.empty or '门店名称' not in df.columns:
        return pd.DataFrame()
    
    # 使用修复后的 calculate_order_metrics
    order_agg = calculate_order_metrics(df)
    
    if order_agg.empty or '门店名称' not in order_agg.columns:
        return pd.DataFrame()
    
    # 确保配送净成本字段存在
    if '配送净成本' not in order_agg.columns:
        order_agg['配送净成本'] = (
            order_agg['物流配送费'].fillna(0) -
            (order_agg.get('用户支付配送费', 0) - order_agg.get('配送费减免金额', 0)) -
            order_agg.get('企客后返', 0)
        )
    
    # 按门店聚合 - 使用配送净成本
    store_stats = order_agg.groupby('门店名称').agg({
        '订单ID': 'count',
        '实收价格': 'sum',
        '订单实际利润': 'sum',
        '配送净成本': 'sum',
        '商家活动成本': 'sum',
    }).reset_index()
    
    store_stats.columns = ['store_name', 'order_count', 'total_revenue', 'total_profit', 'total_delivery_cost', 'total_marketing_cost']
    
    # 计算派生指标
    store_stats['avg_delivery_fee'] = store_stats.apply(
        lambda r: r['total_delivery_cost'] / r['order_count'] if r['order_count'] > 0 else 0, axis=1
    )
    store_stats['avg_marketing_cost'] = store_stats.apply(
        lambda r: r['total_marketing_cost'] / r['order_count'] if r['order_count'] > 0 else 0, axis=1
    )
    
    return store_stats


def main():
    store_name = "惠宜选-泰州泰兴店"
    
    # 获取数据库中的最大日期
    session = SessionLocal()
    try:
        max_date = session.query(func.max(Order.date)).filter(
            Order.store_name == store_name
        ).scalar()
    finally:
        session.close()
    
    # 计算最近7天的日期范围
    end_date = max_date.date()
    start_date = end_date - timedelta(days=6)
    
    print("="*80)
    print(f"验证 API 修复效果 - {store_name}")
    print(f"日期范围: {start_date} ~ {end_date} (最近7天)")
    print("="*80)
    
    channels = ['美团', '饿了么']
    
    for channel in channels:
        print(f"\n📊 {channel}渠道:")
        print("-"*60)
        
        df = get_all_stores_data(start_date, end_date, channel)
        
        if df.empty:
            print("  无数据")
            continue
        
        # 筛选目标门店
        df_store = df[df['门店名称'] == store_name]
        
        if df_store.empty:
            print("  无数据")
            continue
        
        store_stats = calculate_store_metrics(df_store)
        
        if store_stats.empty:
            print("  计算失败")
            continue
        
        row = store_stats.iloc[0]
        print(f"  订单数: {row['order_count']}")
        print(f"  单均配送费: ¥{row['avg_delivery_fee']:.2f}")
        print(f"  单均营销费: ¥{row['avg_marketing_cost']:.2f}")
    
    print("\n" + "="*80)
    print("📋 Dash 版本参考值 (最近7天):")
    print("  美团渠道: 单均配送 ¥3.89")
    print("  饿了么渠道: 单均配送 ¥1.61")
    print("="*80)
    
    print("\n✅ 修复说明:")
    print("  - 单均配送费现在使用'配送净成本'计算（与Dash版本一致）")
    print("  - 配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返")
    print("  - 请重启后端服务使修改生效")


if __name__ == "__main__":
    main()
