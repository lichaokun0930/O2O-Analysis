# -*- coding: utf-8 -*-
"""
诊断利润计算详情

详细分析利润额和订单实际利润的差异
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import SessionLocal
from database.models import Order
from datetime import datetime, date
from sqlalchemy import text
import pandas as pd

STORE_NAME = "惠宜选-泰州兴化店"
START_DATE = date(2026, 1, 16)
END_DATE = date(2026, 1, 22)

# 收费渠道列表
PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播',
    '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店'
]

def load_data():
    """加载数据"""
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
                '订单ID': o.order_id,
                '日期': o.date,
                '渠道': o.channel,
                '利润额': float(o.profit or 0),
                '平台服务费': float(o.platform_service_fee or 0),
                '物流配送费': float(o.delivery_fee or 0),
                '企客后返': float(o.corporate_rebate or 0),
                '实收价格': float(o.actual_price or 0),
                '月售': o.quantity or 1,
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


def analyze_profit_components(df):
    """分析利润各组成部分"""
    print("\n" + "=" * 70)
    print("【利润计算详情分析】")
    print("=" * 70)
    
    # 订单级聚合
    order_agg = df.groupby('订单ID').agg({
        '渠道': 'first',
        '利润额': 'sum',           # 商品级字段，用sum
        '平台服务费': 'sum',       # 商品级字段，用sum
        '物流配送费': 'first',     # 订单级字段，用first
        '企客后返': 'first',       # 订单级字段，用first
        '实收价格': lambda x: (df.loc[x.index, '实收价格'] * df.loc[x.index, '月售']).sum(),
    }).reset_index()
    
    print(f"\n聚合后订单数: {len(order_agg)}")
    
    # 计算订单实际利润
    order_agg['订单实际利润'] = (
        order_agg['利润额'] - 
        order_agg['平台服务费'] - 
        order_agg['物流配送费'] + 
        order_agg['企客后返']
    )
    
    # 过滤前的汇总
    print(f"\n【过滤前】")
    print(f"  订单数: {len(order_agg)}")
    print(f"  利润额总计: ¥{order_agg['利润额'].sum():,.2f}")
    print(f"  平台服务费总计: ¥{order_agg['平台服务费'].sum():,.2f}")
    print(f"  物流配送费总计: ¥{order_agg['物流配送费'].sum():,.2f}")
    print(f"  企客后返总计: ¥{order_agg['企客后返'].sum():,.2f}")
    print(f"  订单实际利润总计: ¥{order_agg['订单实际利润'].sum():,.2f}")
    
    # 验证公式
    calculated = (order_agg['利润额'].sum() - 
                  order_agg['平台服务费'].sum() - 
                  order_agg['物流配送费'].sum() + 
                  order_agg['企客后返'].sum())
    print(f"  公式验证: {order_agg['利润额'].sum():.2f} - {order_agg['平台服务费'].sum():.2f} - {order_agg['物流配送费'].sum():.2f} + {order_agg['企客后返'].sum():.2f} = {calculated:.2f}")
    
    # 过滤异常订单
    is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    
    print(f"\n【异常订单分析】")
    print(f"  收费渠道订单数: {is_fee_channel.sum()}")
    print(f"  平台服务费=0的订单数: {is_zero_fee.sum()}")
    print(f"  异常订单数（收费渠道但服务费=0）: {invalid_orders.sum()}")
    
    # 异常订单的利润影响
    invalid_df = order_agg[invalid_orders]
    if len(invalid_df) > 0:
        print(f"\n  异常订单利润影响:")
        print(f"    利润额: ¥{invalid_df['利润额'].sum():,.2f}")
        print(f"    平台服务费: ¥{invalid_df['平台服务费'].sum():,.2f}")
        print(f"    物流配送费: ¥{invalid_df['物流配送费'].sum():,.2f}")
        print(f"    企客后返: ¥{invalid_df['企客后返'].sum():,.2f}")
        print(f"    订单实际利润: ¥{invalid_df['订单实际利润'].sum():,.2f}")
    
    # 过滤后的汇总
    filtered_agg = order_agg[~invalid_orders]
    
    print(f"\n【过滤后】")
    print(f"  订单数: {len(filtered_agg)}")
    print(f"  利润额总计: ¥{filtered_agg['利润额'].sum():,.2f}")
    print(f"  平台服务费总计: ¥{filtered_agg['平台服务费'].sum():,.2f}")
    print(f"  物流配送费总计: ¥{filtered_agg['物流配送费'].sum():,.2f}")
    print(f"  企客后返总计: ¥{filtered_agg['企客后返'].sum():,.2f}")
    print(f"  订单实际利润总计: ¥{filtered_agg['订单实际利润'].sum():,.2f}")
    
    # 验证公式
    calculated_filtered = (filtered_agg['利润额'].sum() - 
                           filtered_agg['平台服务费'].sum() - 
                           filtered_agg['物流配送费'].sum() + 
                           filtered_agg['企客后返'].sum())
    print(f"  公式验证: {filtered_agg['利润额'].sum():.2f} - {filtered_agg['平台服务费'].sum():.2f} - {filtered_agg['物流配送费'].sum():.2f} + {filtered_agg['企客后返'].sum():.2f} = {calculated_filtered:.2f}")
    
    return filtered_agg


def check_user_expected_value():
    """检查用户期望值"""
    print("\n" + "=" * 70)
    print("【用户期望值对比】")
    print("=" * 70)
    print(f"用户反馈:")
    print(f"  经营总览TAB: ¥3,555.50")
    print(f"  全量门店对比TAB: ¥3,335.61")
    print(f"  差异: ¥219.89")
    print(f"\n我们计算的结果: ¥3,335.61")
    print(f"\n差异分析:")
    print(f"  3555.50 - 3335.61 = 219.89")
    print(f"  这个差异可能来自:")
    print(f"  1. 缓存问题 - 经营总览TAB使用了旧缓存")
    print(f"  2. 参数差异 - 两个TAB传递的日期参数不同")
    print(f"  3. 计算逻辑差异 - 某个字段的聚合方式不同")


def check_all_dates():
    """检查全部日期的利润"""
    print("\n" + "=" * 70)
    print("【全部日期利润检查】")
    print("=" * 70)
    
    session = SessionLocal()
    try:
        orders = session.query(Order).filter(
            Order.store_name == STORE_NAME
        ).all()
        
        data = []
        for o in orders:
            data.append({
                '订单ID': o.order_id,
                '日期': o.date,
                '渠道': o.channel,
                '利润额': float(o.profit or 0),
                '平台服务费': float(o.platform_service_fee or 0),
                '物流配送费': float(o.delivery_fee or 0),
                '企客后返': float(o.corporate_rebate or 0),
            })
        
        df = pd.DataFrame(data)
        print(f"全部数据: {len(df)} 条, {df['订单ID'].nunique()} 订单")
        
        # 订单级聚合
        order_agg = df.groupby('订单ID').agg({
            '渠道': 'first',
            '利润额': 'sum',
            '平台服务费': 'sum',
            '物流配送费': 'first',
            '企客后返': 'first',
        }).reset_index()
        
        order_agg['订单实际利润'] = (
            order_agg['利润额'] - 
            order_agg['平台服务费'] - 
            order_agg['物流配送费'] + 
            order_agg['企客后返']
        )
        
        # 过滤异常订单
        is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
        is_zero_fee = order_agg['平台服务费'] <= 0
        invalid_orders = is_fee_channel & is_zero_fee
        filtered_agg = order_agg[~invalid_orders]
        
        print(f"\n全部日期（过滤后）:")
        print(f"  订单数: {len(filtered_agg)}")
        print(f"  利润额总计: ¥{filtered_agg['利润额'].sum():,.2f}")
        print(f"  订单实际利润总计: ¥{filtered_agg['订单实际利润'].sum():,.2f}")
        print(f"\n用户期望全部日期利润: ¥17,341")
        
    finally:
        session.close()


if __name__ == "__main__":
    df = load_data()
    print(f"加载数据: {len(df)} 条, {df['订单ID'].nunique()} 订单")
    print(f"日期范围: {START_DATE} ~ {END_DATE}")
    
    analyze_profit_components(df)
    check_user_expected_value()
    check_all_dates()
