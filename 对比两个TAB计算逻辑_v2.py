# -*- coding: utf-8 -*-
"""
对比经营总览TAB和全量门店对比TAB的计算逻辑 v2

直接从数据库计算，模拟两个API的逻辑
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

def load_data_orders_style():
    """
    模拟 orders.py 的数据加载方式
    - 先加载门店全部数据
    - 然后在 Python 层面做日期筛选
    """
    print("\n" + "=" * 60)
    print("【orders.py 风格】先加载全部，再筛选日期")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # 只按门店筛选
        orders = session.query(Order).filter(Order.store_name == STORE_NAME).all()
        
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
        
        df = pd.DataFrame(data)
        print(f"加载全部数据: {len(df)} 条, {df['订单ID'].nunique()} 订单")
        
        # Python层面日期筛选
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        df = df[(df['日期'].dt.date >= START_DATE) & (df['日期'].dt.date <= END_DATE)]
        print(f"日期筛选后: {len(df)} 条, {df['订单ID'].nunique()} 订单")
        
        return df
    finally:
        session.close()


def load_data_comparison_style():
    """
    模拟 store_comparison.py 的数据加载方式
    - 在 SQL 层面做日期筛选
    """
    print("\n" + "=" * 60)
    print("【store_comparison.py 风格】SQL层面筛选日期")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # SQL层面日期筛选
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
        
        df = pd.DataFrame(data)
        print(f"SQL筛选后: {len(df)} 条, {df['订单ID'].nunique()} 订单")
        
        return df
    finally:
        session.close()


def calculate_profit(df, label):
    """计算利润（模拟API逻辑）"""
    print(f"\n【{label}】计算利润")
    print("-" * 50)
    
    if df.empty:
        print("数据为空")
        return 0
    
    # 订单级聚合
    order_agg = df.groupby('订单ID').agg({
        '渠道': 'first',
        '利润额': 'sum',
        '平台服务费': 'sum',
        '物流配送费': 'first',  # 订单级字段
        '企客后返': 'sum',
        '实收价格': lambda x: (df.loc[x.index, '实收价格'] * df.loc[x.index, '月售']).sum(),
    }).reset_index()
    
    print(f"聚合后订单数: {len(order_agg)}")
    
    # 计算订单实际利润
    order_agg['订单实际利润'] = (
        order_agg['利润额'] - 
        order_agg['平台服务费'] - 
        order_agg['物流配送费'] + 
        order_agg['企客后返']
    )
    
    print(f"过滤前利润: ¥{order_agg['订单实际利润'].sum():,.2f}")
    
    # 过滤异常订单
    is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    
    print(f"异常订单数: {invalid_orders.sum()}")
    
    filtered_agg = order_agg[~invalid_orders]
    
    total_profit = filtered_agg['订单实际利润'].sum()
    print(f"过滤后订单数: {len(filtered_agg)}")
    print(f"过滤后利润: ¥{total_profit:,.2f}")
    
    return total_profit


def check_date_range():
    """检查数据库中的日期范围"""
    print("\n" + "=" * 60)
    print("【检查日期范围】")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        sql = """
        SELECT 
            MIN(date) as min_date,
            MAX(date) as max_date,
            COUNT(DISTINCT DATE(date)) as date_count
        FROM orders
        WHERE store_name = :store_name
        """
        result = session.execute(text(sql), {'store_name': STORE_NAME})
        row = result.fetchone()
        
        print(f"门店: {STORE_NAME}")
        print(f"最早日期: {row[0]}")
        print(f"最晚日期: {row[1]}")
        print(f"日期数: {row[2]}")
        
        # 检查指定日期范围内的数据
        sql2 = """
        SELECT 
            DATE(date) as order_date,
            COUNT(DISTINCT order_id) as order_count,
            COUNT(*) as row_count
        FROM orders
        WHERE store_name = :store_name
          AND DATE(date) >= :start_date
          AND DATE(date) <= :end_date
        GROUP BY DATE(date)
        ORDER BY DATE(date)
        """
        result2 = session.execute(text(sql2), {
            'store_name': STORE_NAME,
            'start_date': START_DATE,
            'end_date': END_DATE
        })
        rows = result2.fetchall()
        
        print(f"\n日期范围 {START_DATE} ~ {END_DATE} 内的数据:")
        total_orders = 0
        total_rows = 0
        for row in rows:
            print(f"  {row[0]}: {row[1]} 订单, {row[2]} 行")
            total_orders += row[1]
            total_rows += row[2]
        print(f"  合计: {total_orders} 订单, {total_rows} 行")
        
    finally:
        session.close()


if __name__ == "__main__":
    # 检查日期范围
    check_date_range()
    
    # 两种方式加载数据
    df1 = load_data_orders_style()
    df2 = load_data_comparison_style()
    
    # 对比订单ID
    print("\n" + "=" * 60)
    print("【订单ID对比】")
    print("=" * 60)
    
    orders1 = set(df1['订单ID'].unique())
    orders2 = set(df2['订单ID'].unique())
    
    only_in_1 = orders1 - orders2
    only_in_2 = orders2 - orders1
    
    print(f"orders.py 风格: {len(orders1)} 订单")
    print(f"store_comparison.py 风格: {len(orders2)} 订单")
    print(f"只在orders.py中: {len(only_in_1)}")
    print(f"只在store_comparison.py中: {len(only_in_2)}")
    
    if only_in_1:
        # 检查这些订单的日期
        missing_df = df1[df1['订单ID'].isin(only_in_1)]
        print(f"\n只在orders.py中的订单日期分布:")
        print(missing_df.groupby(missing_df['日期'].dt.date)['订单ID'].nunique())
    
    # 计算利润
    profit1 = calculate_profit(df1.copy(), "orders.py 风格")
    profit2 = calculate_profit(df2.copy(), "store_comparison.py 风格")
    
    print("\n" + "=" * 60)
    print("【最终对比】")
    print("=" * 60)
    print(f"orders.py 风格利润: ¥{profit1:,.2f}")
    print(f"store_comparison.py 风格利润: ¥{profit2:,.2f}")
    print(f"差异: ¥{profit1 - profit2:,.2f}")
