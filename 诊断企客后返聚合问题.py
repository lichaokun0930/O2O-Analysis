# -*- coding: utf-8 -*-
"""
诊断企客后返字段聚合方式问题

问题：经营总览TAB显示利润3555.5，全量门店对比TAB显示3335.61
差异约220元

假设：企客后返字段在orders.py中使用sum聚合，但实际应该用first
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


def check_corporate_rebate_distribution(df):
    """检查企客后返字段的分布"""
    print("\n" + "=" * 60)
    print("【企客后返字段分析】")
    print("=" * 60)
    
    # 检查每个订单的企客后返值
    order_rebate = df.groupby('订单ID').agg({
        '企客后返': ['first', 'sum', 'count', 'nunique']
    }).reset_index()
    order_rebate.columns = ['订单ID', '企客后返_first', '企客后返_sum', '行数', '唯一值数']
    
    # 找出first和sum不同的订单
    diff_orders = order_rebate[order_rebate['企客后返_first'] != order_rebate['企客后返_sum']]
    
    print(f"总订单数: {len(order_rebate)}")
    print(f"first和sum不同的订单数: {len(diff_orders)}")
    
    if len(diff_orders) > 0:
        print(f"\n差异订单示例（前10个）:")
        for _, row in diff_orders.head(10).iterrows():
            print(f"  订单 {row['订单ID']}: first={row['企客后返_first']:.2f}, sum={row['企客后返_sum']:.2f}, 行数={row['行数']}")
        
        # 计算总差异
        total_first = order_rebate['企客后返_first'].sum()
        total_sum = order_rebate['企客后返_sum'].sum()
        print(f"\n企客后返总计:")
        print(f"  使用first: ¥{total_first:,.2f}")
        print(f"  使用sum: ¥{total_sum:,.2f}")
        print(f"  差异: ¥{total_sum - total_first:,.2f}")
        
        return total_first, total_sum
    else:
        print("所有订单的first和sum值相同，企客后返是订单级字段")
        return None, None


def calculate_profit_with_different_aggregation(df):
    """使用不同聚合方式计算利润"""
    print("\n" + "=" * 60)
    print("【不同聚合方式对比】")
    print("=" * 60)
    
    # 方式1：企客后返用first（正确方式）
    order_agg_first = df.groupby('订单ID').agg({
        '渠道': 'first',
        '利润额': 'sum',
        '平台服务费': 'sum',
        '物流配送费': 'first',
        '企客后返': 'first',  # 订单级字段
    }).reset_index()
    
    order_agg_first['订单实际利润'] = (
        order_agg_first['利润额'] - 
        order_agg_first['平台服务费'] - 
        order_agg_first['物流配送费'] + 
        order_agg_first['企客后返']
    )
    
    # 过滤异常订单
    is_fee_channel = order_agg_first['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg_first['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    filtered_first = order_agg_first[~invalid_orders]
    
    profit_first = filtered_first['订单实际利润'].sum()
    
    # 方式2：企客后返用sum（可能错误的方式）
    order_agg_sum = df.groupby('订单ID').agg({
        '渠道': 'first',
        '利润额': 'sum',
        '平台服务费': 'sum',
        '物流配送费': 'first',
        '企客后返': 'sum',  # 商品级聚合
    }).reset_index()
    
    order_agg_sum['订单实际利润'] = (
        order_agg_sum['利润额'] - 
        order_agg_sum['平台服务费'] - 
        order_agg_sum['物流配送费'] + 
        order_agg_sum['企客后返']
    )
    
    # 过滤异常订单
    is_fee_channel = order_agg_sum['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg_sum['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    filtered_sum = order_agg_sum[~invalid_orders]
    
    profit_sum = filtered_sum['订单实际利润'].sum()
    
    print(f"企客后返用first聚合: ¥{profit_first:,.2f}")
    print(f"企客后返用sum聚合: ¥{profit_sum:,.2f}")
    print(f"差异: ¥{profit_sum - profit_first:,.2f}")
    
    print(f"\n用户反馈:")
    print(f"  经营总览TAB: ¥3,555.50")
    print(f"  全量门店对比TAB: ¥3,335.61")
    print(f"  差异: ¥219.89")
    
    return profit_first, profit_sum


if __name__ == "__main__":
    df = load_data()
    print(f"加载数据: {len(df)} 条, {df['订单ID'].nunique()} 订单")
    
    # 检查企客后返分布
    check_corporate_rebate_distribution(df)
    
    # 对比不同聚合方式
    calculate_profit_with_different_aggregation(df)
