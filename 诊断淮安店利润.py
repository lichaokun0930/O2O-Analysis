# -*- coding: utf-8 -*-
"""
诊断淮安生态新城店利润计算

用户反馈：实际利润3554，看板显示4630，差异约1076
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import SessionLocal
from database.models import Order
from datetime import datetime, date
from sqlalchemy import text
import pandas as pd

STORE_NAME = "惠宜选-淮安生态新城店"
START_DATE = date(2026, 1, 12)
END_DATE = date(2026, 1, 18)

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


def analyze_profit(df):
    """分析利润计算"""
    print("\n" + "=" * 70)
    print(f"【{STORE_NAME}】利润分析")
    print(f"日期范围: {START_DATE} ~ {END_DATE}")
    print("=" * 70)
    
    print(f"\n原始数据: {len(df)} 条, {df['订单ID'].nunique()} 订单")
    
    # 方法1：企客后返用first（订单级字段）
    order_agg_first = df.groupby('订单ID').agg({
        '渠道': 'first',
        '利润额': 'sum',
        '平台服务费': 'sum',
        '物流配送费': 'first',
        '企客后返': 'first',
    }).reset_index()
    
    order_agg_first['订单实际利润'] = (
        order_agg_first['利润额'] - 
        order_agg_first['平台服务费'] - 
        order_agg_first['物流配送费'] + 
        order_agg_first['企客后返']
    )
    
    # 方法2：企客后返用sum（商品级字段）
    order_agg_sum = df.groupby('订单ID').agg({
        '渠道': 'first',
        '利润额': 'sum',
        '平台服务费': 'sum',
        '物流配送费': 'first',
        '企客后返': 'sum',
    }).reset_index()
    
    order_agg_sum['订单实际利润'] = (
        order_agg_sum['利润额'] - 
        order_agg_sum['平台服务费'] - 
        order_agg_sum['物流配送费'] + 
        order_agg_sum['企客后返']
    )
    
    print(f"\n【聚合后】订单数: {len(order_agg_first)}")
    
    # 检查企客后返差异
    rebate_first = order_agg_first['企客后返'].sum()
    rebate_sum = order_agg_sum['企客后返'].sum()
    print(f"\n企客后返:")
    print(f"  first聚合: ¥{rebate_first:,.2f}")
    print(f"  sum聚合: ¥{rebate_sum:,.2f}")
    print(f"  差异: ¥{rebate_sum - rebate_first:,.2f}")
    
    # 过滤前
    print(f"\n【过滤前】")
    print(f"  利润额: ¥{order_agg_first['利润额'].sum():,.2f}")
    print(f"  平台服务费: ¥{order_agg_first['平台服务费'].sum():,.2f}")
    print(f"  物流配送费: ¥{order_agg_first['物流配送费'].sum():,.2f}")
    print(f"  企客后返(first): ¥{rebate_first:,.2f}")
    print(f"  订单实际利润(first): ¥{order_agg_first['订单实际利润'].sum():,.2f}")
    print(f"  订单实际利润(sum): ¥{order_agg_sum['订单实际利润'].sum():,.2f}")
    
    # 过滤异常订单
    is_fee_channel = order_agg_first['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg_first['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    
    print(f"\n【异常订单】")
    print(f"  收费渠道订单: {is_fee_channel.sum()}")
    print(f"  平台服务费=0: {is_zero_fee.sum()}")
    print(f"  异常订单数: {invalid_orders.sum()}")
    
    # 过滤后
    filtered_first = order_agg_first[~invalid_orders]
    filtered_sum = order_agg_sum[~invalid_orders]
    
    print(f"\n【过滤后】")
    print(f"  订单数: {len(filtered_first)}")
    print(f"  利润额: ¥{filtered_first['利润额'].sum():,.2f}")
    print(f"  平台服务费: ¥{filtered_first['平台服务费'].sum():,.2f}")
    print(f"  物流配送费: ¥{filtered_first['物流配送费'].sum():,.2f}")
    print(f"  企客后返(first): ¥{filtered_first['企客后返'].sum():,.2f}")
    print(f"  订单实际利润(first): ¥{filtered_first['订单实际利润'].sum():,.2f}")
    print(f"  订单实际利润(sum): ¥{filtered_sum['订单实际利润'].sum():,.2f}")
    
    # 对比用户期望
    print(f"\n【用户期望对比】")
    print(f"  用户期望: ¥3,554")
    print(f"  看板显示: ¥4,630")
    print(f"  差异: ¥1,076")
    print(f"\n  我们计算(first): ¥{filtered_first['订单实际利润'].sum():,.2f}")
    print(f"  我们计算(sum): ¥{filtered_sum['订单实际利润'].sum():,.2f}")
    
    # 检查是否有重复数据
    print(f"\n【重复数据检查】")
    dup_check = df.groupby(['订单ID', '利润额', '平台服务费']).size().reset_index(name='count')
    dup_rows = dup_check[dup_check['count'] > 1]
    if len(dup_rows) > 0:
        print(f"  发现重复行: {len(dup_rows)} 组")
        print(f"  示例:")
        print(dup_rows.head())
    else:
        print(f"  无重复行")
    
    return filtered_first['订单实际利润'].sum()


def check_raw_data():
    """检查原始数据"""
    print("\n" + "=" * 70)
    print("【原始数据检查】")
    print("=" * 70)
    
    session = SessionLocal()
    try:
        # 检查该门店是否有重复导入
        sql = """
        SELECT 
            order_id,
            COUNT(*) as row_count,
            COUNT(DISTINCT profit) as profit_values,
            SUM(profit) as total_profit
        FROM orders
        WHERE store_name = :store_name
          AND date >= :start_date
          AND date <= :end_date
        GROUP BY order_id
        HAVING COUNT(*) > 10
        ORDER BY COUNT(*) DESC
        LIMIT 10
        """
        result = session.execute(text(sql), {
            'store_name': STORE_NAME,
            'start_date': datetime.combine(START_DATE, datetime.min.time()),
            'end_date': datetime.combine(END_DATE, datetime.max.time())
        })
        rows = result.fetchall()
        
        if rows:
            print(f"订单行数超过10的订单（可能有重复）:")
            for row in rows:
                print(f"  订单 {row[0]}: {row[1]} 行, {row[2]} 个不同利润值, 利润总计 ¥{row[3]:.2f}")
        else:
            print("没有发现异常多行的订单")
        
        # 检查总行数和订单数
        sql2 = """
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT order_id) as total_orders
        FROM orders
        WHERE store_name = :store_name
          AND date >= :start_date
          AND date <= :end_date
        """
        result2 = session.execute(text(sql2), {
            'store_name': STORE_NAME,
            'start_date': datetime.combine(START_DATE, datetime.min.time()),
            'end_date': datetime.combine(END_DATE, datetime.max.time())
        })
        row = result2.fetchone()
        print(f"\n总行数: {row[0]}, 总订单数: {row[1]}")
        print(f"平均每订单行数: {row[0]/row[1]:.1f}")
        
    finally:
        session.close()


def check_without_filter():
    """不过滤异常订单的计算"""
    print("\n" + "=" * 70)
    print("【不过滤异常订单】")
    print("=" * 70)
    
    df = load_data()
    
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
    
    print(f"不过滤时的订单实际利润: ¥{order_agg['订单实际利润'].sum():,.2f}")
    print(f"看板显示: ¥4,630")
    print(f"差异: ¥{4630 - order_agg['订单实际利润'].sum():,.2f}")


if __name__ == "__main__":
    check_raw_data()
    df = load_data()
    analyze_profit(df)
    check_without_filter()
