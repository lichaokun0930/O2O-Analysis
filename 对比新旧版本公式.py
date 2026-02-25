# -*- coding: utf-8 -*-
"""
对比新旧版本的利润计算公式

老版本公式: 订单实际利润 = 利润额 - 物流配送费 - 平台佣金
新版本公式: 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
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
                '订单ID': str(o.order_id),
                '日期': o.date,
                '渠道': o.channel,
                '利润额': float(o.profit or 0),
                '平台服务费': float(o.platform_service_fee or 0),
                '平台佣金': float(o.commission or 0),
                '物流配送费': float(o.delivery_fee or 0),
                '企客后返': float(o.corporate_rebate or 0),
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


def calculate_both_formulas(df):
    """计算两种公式的结果"""
    print("\n" + "=" * 70)
    print("【对比新旧版本公式】")
    print("=" * 70)
    
    # 订单级聚合
    order_agg = df.groupby('订单ID').agg({
        '渠道': 'first',
        '利润额': 'sum',           # 商品级
        '平台服务费': 'sum',       # 商品级
        '平台佣金': 'first',       # 订单级
        '物流配送费': 'first',     # 订单级
        '企客后返': 'sum',         # 商品级
    }).reset_index()
    
    print(f"聚合后订单数: {len(order_agg)}")
    
    # 老版本公式（不过滤异常订单）
    order_agg['老版本利润'] = (
        order_agg['利润额'] - 
        order_agg['物流配送费'] - 
        order_agg['平台佣金']
    )
    
    # 新版本公式（不过滤异常订单）
    order_agg['新版本利润'] = (
        order_agg['利润额'] - 
        order_agg['平台服务费'] - 
        order_agg['物流配送费'] + 
        order_agg['企客后返']
    )
    
    print(f"\n【不过滤异常订单】")
    print(f"  订单数: {len(order_agg)}")
    print(f"  利润额: ¥{order_agg['利润额'].sum():,.2f}")
    print(f"  平台佣金: ¥{order_agg['平台佣金'].sum():,.2f}")
    print(f"  平台服务费: ¥{order_agg['平台服务费'].sum():,.2f}")
    print(f"  物流配送费: ¥{order_agg['物流配送费'].sum():,.2f}")
    print(f"  企客后返: ¥{order_agg['企客后返'].sum():,.2f}")
    print()
    print(f"  老版本公式结果: ¥{order_agg['老版本利润'].sum():,.2f}")
    print(f"  新版本公式结果: ¥{order_agg['新版本利润'].sum():,.2f}")
    print(f"  差异: ¥{order_agg['新版本利润'].sum() - order_agg['老版本利润'].sum():,.2f}")
    
    # 过滤异常订单（新版本逻辑）
    is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    filtered = order_agg[~invalid_orders].copy()
    
    print(f"\n【过滤异常订单后（新版本过滤逻辑）】")
    print(f"  剔除订单数: {invalid_orders.sum()}")
    print(f"  保留订单数: {len(filtered)}")
    print()
    print(f"  老版本公式结果: ¥{filtered['老版本利润'].sum():,.2f}")
    print(f"  新版本公式结果: ¥{filtered['新版本利润'].sum():,.2f}")
    
    print(f"\n【与用户期望值对比】")
    print(f"  用户期望: ¥3,554")
    print(f"  老版本(不过滤): ¥{order_agg['老版本利润'].sum():,.2f}, 差异: ¥{order_agg['老版本利润'].sum() - 3554:,.2f}")
    print(f"  老版本(过滤后): ¥{filtered['老版本利润'].sum():,.2f}, 差异: ¥{filtered['老版本利润'].sum() - 3554:,.2f}")
    print(f"  新版本(不过滤): ¥{order_agg['新版本利润'].sum():,.2f}, 差异: ¥{order_agg['新版本利润'].sum() - 3554:,.2f}")
    print(f"  新版本(过滤后): ¥{filtered['新版本利润'].sum():,.2f}, 差异: ¥{filtered['新版本利润'].sum() - 3554:,.2f}")
    
    # 检查平台佣金和平台服务费的差异
    print(f"\n【平台佣金 vs 平台服务费】")
    print(f"  平台佣金总和: ¥{order_agg['平台佣金'].sum():,.2f}")
    print(f"  平台服务费总和: ¥{order_agg['平台服务费'].sum():,.2f}")
    print(f"  差异: ¥{order_agg['平台佣金'].sum() - order_agg['平台服务费'].sum():,.2f}")
    
    # 分析差异来源
    print(f"\n【差异分析】")
    diff = order_agg['老版本利润'].sum() - 3554
    print(f"  老版本(不过滤)与用户期望差异: ¥{diff:,.2f}")
    
    # 检查是否有其他可能的扣减项
    print(f"\n【可能的解释】")
    print(f"  1. 用户可能使用了不同的数据源（如Excel原始数据）")
    print(f"  2. 用户可能有额外的扣减项我们没有考虑")
    print(f"  3. 数据库中的数据可能与用户看到的不一致")
    
    return order_agg


if __name__ == "__main__":
    print(f"门店: {STORE_NAME}")
    print(f"日期: {START_DATE} ~ {END_DATE}")
    
    df = load_data()
    print(f"加载数据: {len(df)} 条, {df['订单ID'].nunique()} 订单")
    
    calculate_both_formulas(df)
