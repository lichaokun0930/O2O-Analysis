# -*- coding: utf-8 -*-
"""
使用权威公式诊断淮安店利润

权威公式（来自【权威】业务逻辑与数据字典完整手册.md）：
订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返

字段聚合方式：
- 利润额: 商品级字段，用 sum
- 平台服务费: 商品级字段，用 sum
- 物流配送费: 订单级字段，用 first
- 企客后返: 商品级字段，用 sum
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


def calculate_with_authority_formula(df):
    """使用权威公式计算"""
    print("\n" + "=" * 70)
    print("【使用权威公式计算】")
    print("=" * 70)
    print("公式: 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返")
    print("聚合方式:")
    print("  - 利润额: sum (商品级)")
    print("  - 平台服务费: sum (商品级)")
    print("  - 物流配送费: first (订单级)")
    print("  - 企客后返: sum (商品级)")
    
    # 按权威手册的聚合方式
    order_agg = df.groupby('订单ID').agg({
        '渠道': 'first',
        '利润额': 'sum',           # 商品级字段
        '平台服务费': 'sum',       # 商品级字段
        '物流配送费': 'first',     # 订单级字段
        '企客后返': 'sum',         # 商品级字段
    }).reset_index()
    
    print(f"\n聚合后订单数: {len(order_agg)}")
    
    # 计算订单实际利润
    order_agg['订单实际利润'] = (
        order_agg['利润额'] - 
        order_agg['平台服务费'] - 
        order_agg['物流配送费'] + 
        order_agg['企客后返']
    )
    
    print(f"\n【过滤前】")
    print(f"  利润额: ¥{order_agg['利润额'].sum():,.2f}")
    print(f"  平台服务费: ¥{order_agg['平台服务费'].sum():,.2f}")
    print(f"  物流配送费: ¥{order_agg['物流配送费'].sum():,.2f}")
    print(f"  企客后返: ¥{order_agg['企客后返'].sum():,.2f}")
    print(f"  订单实际利润: ¥{order_agg['订单实际利润'].sum():,.2f}")
    
    # 过滤异常订单
    is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    
    print(f"\n【异常订单】")
    print(f"  收费渠道订单: {is_fee_channel.sum()}")
    print(f"  平台服务费=0: {is_zero_fee.sum()}")
    print(f"  异常订单数: {invalid_orders.sum()}")
    
    filtered = order_agg[~invalid_orders]
    
    print(f"\n【过滤后】")
    print(f"  订单数: {len(filtered)}")
    print(f"  利润额: ¥{filtered['利润额'].sum():,.2f}")
    print(f"  平台服务费: ¥{filtered['平台服务费'].sum():,.2f}")
    print(f"  物流配送费: ¥{filtered['物流配送费'].sum():,.2f}")
    print(f"  企客后返: ¥{filtered['企客后返'].sum():,.2f}")
    print(f"  订单实际利润: ¥{filtered['订单实际利润'].sum():,.2f}")
    
    print(f"\n【对比】")
    print(f"  用户期望: ¥3,554")
    print(f"  我们计算: ¥{filtered['订单实际利润'].sum():,.2f}")
    print(f"  差异: ¥{filtered['订单实际利润'].sum() - 3554:,.2f}")
    
    return filtered['订单实际利润'].sum()


def check_sql_calculation():
    """使用SQL直接计算验证"""
    print("\n" + "=" * 70)
    print("【SQL直接计算验证】")
    print("=" * 70)
    
    session = SessionLocal()
    try:
        # 使用SQL按权威公式计算
        sql = """
        WITH order_agg AS (
            SELECT 
                order_id,
                channel,
                SUM(profit) as profit,                    -- 商品级，用SUM
                SUM(platform_service_fee) as platform_fee, -- 商品级，用SUM
                MAX(delivery_fee) as delivery_fee,        -- 订单级，用MAX/FIRST
                SUM(corporate_rebate) as rebate           -- 商品级，用SUM
            FROM orders
            WHERE store_name = :store_name
              AND date >= :start_date
              AND date <= :end_date
            GROUP BY order_id, channel
        ),
        filtered AS (
            SELECT * FROM order_agg
            WHERE NOT (
                channel IN ('饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店')
                AND platform_fee <= 0
            )
        )
        SELECT 
            COUNT(*) as order_count,
            SUM(profit) as total_profit,
            SUM(platform_fee) as total_platform_fee,
            SUM(delivery_fee) as total_delivery_fee,
            SUM(rebate) as total_rebate,
            SUM(profit - platform_fee - delivery_fee + rebate) as actual_profit
        FROM filtered
        """
        result = session.execute(text(sql), {
            'store_name': STORE_NAME,
            'start_date': datetime.combine(START_DATE, datetime.min.time()),
            'end_date': datetime.combine(END_DATE, datetime.max.time())
        })
        row = result.fetchone()
        
        print(f"订单数: {row[0]}")
        print(f"利润额: ¥{row[1]:,.2f}")
        print(f"平台服务费: ¥{row[2]:,.2f}")
        print(f"物流配送费: ¥{row[3]:,.2f}")
        print(f"企客后返: ¥{row[4]:,.2f}")
        print(f"订单实际利润: ¥{row[5]:,.2f}")
        
        print(f"\n公式验证:")
        print(f"  {row[1]:.2f} - {row[2]:.2f} - {row[3]:.2f} + {row[4]:.2f} = {row[1] - row[2] - row[3] + row[4]:.2f}")
        
        return row[5]
        
    finally:
        session.close()


if __name__ == "__main__":
    df = load_data()
    print(f"加载数据: {len(df)} 条, {df['订单ID'].nunique()} 订单")
    print(f"日期范围: {START_DATE} ~ {END_DATE}")
    
    # Python计算
    python_result = calculate_with_authority_formula(df)
    
    # SQL计算
    sql_result = check_sql_calculation()
    
    print("\n" + "=" * 70)
    print("【最终结论】")
    print("=" * 70)
    print(f"Python计算: ¥{python_result:,.2f}")
    print(f"SQL计算: ¥{sql_result:,.2f}")
    print(f"用户期望: ¥3,554")
    print(f"差异: ¥{python_result - 3554:,.2f}")
