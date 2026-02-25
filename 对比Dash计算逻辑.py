# -*- coding: utf-8 -*-
"""
直接调用Dash版本的计算逻辑，对比结果
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import SessionLocal
from database.models import Order
from datetime import datetime, date
import pandas as pd

STORE_NAME = "惠宜选-淮安生态新城店"
START_DATE = date(2026, 1, 12)
END_DATE = date(2026, 1, 18)

# 从Dash版本复制的收费渠道列表
PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播',
    '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店'
]

def load_data_as_dash():
    """模拟Dash版本的数据加载方式"""
    session = SessionLocal()
    try:
        start_dt = datetime.combine(START_DATE, datetime.min.time())
        end_dt = datetime.combine(END_DATE, datetime.max.time())
        
        orders = session.query(Order).filter(
            Order.store_name == STORE_NAME,
            Order.date >= start_dt,
            Order.date <= end_dt
        ).all()
        
        data = []
        for o in orders:
            data.append({
                '订单ID': str(o.order_id),
                '日期': o.date,
                '渠道': o.channel,
                '商品名称': o.product_name,
                # 商品级字段
                '利润额': float(o.profit or 0),
                '平台服务费': float(o.platform_service_fee or 0),
                '企客后返': float(o.corporate_rebate or 0),
                '实收价格': float(o.actual_price or 0),
                '商品实售价': float(o.price or 0),
                '预计订单收入': float(o.amount or 0),
                '月售': o.quantity or 1,
                '商品采购成本': float(o.cost or 0),
                # 订单级字段
                '物流配送费': float(o.delivery_fee or 0),
                '平台佣金': float(o.commission or 0),
                '满减金额': float(o.full_reduction or 0),
                '商品减免金额': float(o.product_discount or 0),
                '商家代金券': float(o.merchant_voucher or 0),
                '商家承担部分券': float(o.merchant_share or 0),
                '配送费减免金额': float(o.delivery_discount or 0),
                '用户支付配送费': float(o.user_paid_delivery_fee or 0),
                '打包袋金额': float(o.packaging_fee or 0),
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


def calculate_order_metrics_dash_style(df):
    """
    模拟Dash版本的calculate_order_metrics函数
    """
    print("\n" + "=" * 70)
    print("【模拟Dash版本计算逻辑】")
    print("=" * 70)
    
    # 空值填充
    df['物流配送费'] = df['物流配送费'].fillna(0)
    df['配送费减免金额'] = df['配送费减免金额'].fillna(0)
    df['用户支付配送费'] = df['用户支付配送费'].fillna(0)
    
    # 计算订单总收入 = 实收价格 × 月售
    df['订单总收入'] = df['实收价格'] * df['月售']
    
    # 订单级聚合
    agg_dict = {
        '渠道': 'first',
        '商品实售价': 'sum',
        '预计订单收入': 'sum',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '物流配送费': 'first',
        '平台佣金': 'first',
        '月售': 'sum',
        '平台服务费': 'sum',
        '订单总收入': 'sum',
        '满减金额': 'first',
        '商品减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',
        '打包袋金额': 'first',
        '利润额': 'sum',
        '企客后返': 'sum',
        '商品采购成本': 'sum',
    }
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    print(f"聚合后订单数: {len(order_agg)}")
    
    # 计算订单实际利润（Dash版本公式）
    service_fee = order_agg.get('平台服务费', pd.Series(0, index=order_agg.index)).fillna(0)
    
    order_agg['订单实际利润'] = (
        order_agg['利润额'] -
        service_fee -
        order_agg['物流配送费'] +
        order_agg.get('企客后返', 0)
    )
    
    print(f"\n【过滤前】利润计算:")
    print(f"  利润额总和: ¥{order_agg['利润额'].sum():,.2f}")
    print(f"  平台服务费总和: ¥{service_fee.sum():,.2f}")
    print(f"  物流配送费总和: ¥{order_agg['物流配送费'].sum():,.2f}")
    print(f"  企客后返总和: ¥{order_agg.get('企客后返', pd.Series(0)).sum():,.2f}")
    print(f"  订单实际利润总和: ¥{order_agg['订单实际利润'].sum():,.2f}")
    
    # 按渠道类型过滤
    is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg.get('平台服务费', 0) <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    filtered = order_agg[~invalid_orders].copy()
    
    print(f"\n【过滤统计】")
    print(f"  总订单数: {len(order_agg)}")
    print(f"  收费渠道订单数: {is_fee_channel.sum()}")
    print(f"  不收费渠道订单数: {(~is_fee_channel).sum()}")
    print(f"  收费渠道中服务费=0的订单: {(is_fee_channel & is_zero_fee).sum()} (已剔除)")
    print(f"  最终保留订单数: {len(filtered)}")
    
    print(f"\n【过滤后】")
    print(f"  利润额: ¥{filtered['利润额'].sum():,.2f}")
    print(f"  平台服务费: ¥{filtered['平台服务费'].sum():,.2f}")
    print(f"  物流配送费: ¥{filtered['物流配送费'].sum():,.2f}")
    print(f"  企客后返: ¥{filtered.get('企客后返', pd.Series(0)).sum():,.2f}")
    print(f"  订单实际利润: ¥{filtered['订单实际利润'].sum():,.2f}")
    
    return filtered


def check_channel_distribution(df):
    """检查渠道分布"""
    print("\n" + "=" * 70)
    print("【渠道分布】")
    print("=" * 70)
    
    channel_counts = df.groupby('渠道')['订单ID'].nunique()
    print(channel_counts.to_string())
    
    print(f"\n收费渠道: {PLATFORM_FEE_CHANNELS}")


if __name__ == "__main__":
    print(f"门店: {STORE_NAME}")
    print(f"日期: {START_DATE} ~ {END_DATE}")
    
    df = load_data_as_dash()
    print(f"加载数据: {len(df)} 条, {df['订单ID'].nunique()} 订单")
    
    check_channel_distribution(df)
    
    filtered = calculate_order_metrics_dash_style(df)
    
    print("\n" + "=" * 70)
    print("【最终结论】")
    print("=" * 70)
    print(f"Dash风格计算结果: ¥{filtered['订单实际利润'].sum():,.2f}")
    print(f"用户期望: ¥3,554")
    print(f"差异: ¥{filtered['订单实际利润'].sum() - 3554:,.2f}")
