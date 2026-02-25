# -*- coding: utf-8 -*-
"""
完全模拟老版本的计算逻辑（不过滤任何订单）

老版本公式: 订单实际利润 = 利润额 - 物流配送费 - 平台佣金
老版本没有任何异常订单过滤逻辑
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
                '订单ID': str(o.order_id),
                '利润额': float(o.profit or 0),
                '平台佣金': float(o.commission or 0),
                '物流配送费': float(o.delivery_fee or 0),
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


def calculate_old_version(df):
    """完全模拟老版本计算"""
    print("\n" + "=" * 70)
    print("【完全模拟老版本计算】")
    print("=" * 70)
    print("公式: 订单实际利润 = 利润额 - 物流配送费 - 平台佣金")
    print("过滤: 无（老版本不过滤任何订单）")
    
    # 订单级聚合（老版本的聚合方式）
    order_agg = df.groupby('订单ID').agg({
        '利润额': 'sum',           # 商品级
        '平台佣金': 'first',       # 订单级
        '物流配送费': 'first',     # 订单级
    }).reset_index()
    
    print(f"\n订单数: {len(order_agg)}")
    
    # 老版本公式
    order_agg['订单实际利润'] = (
        order_agg['利润额'] - 
        order_agg['物流配送费'] - 
        order_agg['平台佣金']
    )
    
    profit = order_agg['利润额'].sum()
    delivery = order_agg['物流配送费'].sum()
    commission = order_agg['平台佣金'].sum()
    result = order_agg['订单实际利润'].sum()
    
    print(f"\n计算过程:")
    print(f"  利润额: ¥{profit:,.2f}")
    print(f"  物流配送费: ¥{delivery:,.2f}")
    print(f"  平台佣金: ¥{commission:,.2f}")
    print(f"  ----------------------------------------")
    print(f"  {profit:.2f} - {delivery:.2f} - {commission:.2f} = {result:.2f}")
    print(f"\n【老版本结果】: ¥{result:,.2f}")
    
    print(f"\n【与用户期望对比】")
    print(f"  用户期望: ¥3,554")
    print(f"  老版本结果: ¥{result:,.2f}")
    print(f"  差异: ¥{result - 3554:,.2f}")
    
    return result


if __name__ == "__main__":
    print(f"门店: {STORE_NAME}")
    print(f"日期: {START_DATE} ~ {END_DATE}")
    
    df = load_data()
    print(f"加载数据: {len(df)} 条, {df['订单ID'].nunique()} 订单")
    
    calculate_old_version(df)
