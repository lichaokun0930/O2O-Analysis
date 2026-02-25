# -*- coding: utf-8 -*-
"""
诊断淮安生态新城店利润计算 - 详细版

用户期望: 3554
看板显示: 4630
差异: 1076

可能的原因：
1. 企客后返应该是减去而不是加上？
2. 还有其他扣减项没有计入？
3. 用户的计算公式不同？
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

def load_all_fields():
    """加载所有可能影响利润的字段"""
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
                '平台佣金': float(o.commission or 0),
                '物流配送费': float(o.delivery_fee or 0),
                '企客后返': float(o.corporate_rebate or 0),
                '用户支付配送费': float(o.user_paid_delivery_fee or 0),
                '配送费减免金额': float(o.delivery_discount or 0),
                '满减金额': float(o.full_reduction or 0),
                '商品减免金额': float(o.product_discount or 0),
                '新客减免金额': float(o.new_customer_discount or 0),
                '商家代金券': float(o.merchant_voucher or 0),
                '商家承担部分券': float(o.merchant_share or 0),
                '满赠金额': float(o.gift_amount or 0),
                '商家其他优惠': float(o.other_merchant_discount or 0),
                '实收价格': float(o.actual_price or 0),
                '商品采购成本': float(o.cost or 0),
                '月售': o.quantity or 1,
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


def analyze_all_cost_components(df):
    """分析所有成本组成"""
    print("\n" + "=" * 70)
    print("【所有成本组成分析】")
    print("=" * 70)
    
    # 订单级聚合
    order_agg = df.groupby('订单ID').agg({
        '渠道': 'first',
        '利润额': 'sum',
        '平台服务费': 'sum',
        '平台佣金': 'first',
        '物流配送费': 'first',
        '企客后返': 'first',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '满减金额': 'first',
        '商品减免金额': 'first',
        '新客减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',
        '满赠金额': 'first',
        '商家其他优惠': 'first',
        '实收价格': 'sum',
        '商品采购成本': 'sum',
    }).reset_index()
    
    # 过滤异常订单
    is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    filtered = order_agg[~invalid_orders]
    
    print(f"过滤后订单数: {len(filtered)}")
    
    # 各字段汇总
    print(f"\n【各字段汇总】")
    print(f"  利润额: ¥{filtered['利润额'].sum():,.2f}")
    print(f"  平台服务费: ¥{filtered['平台服务费'].sum():,.2f}")
    print(f"  平台佣金: ¥{filtered['平台佣金'].sum():,.2f}")
    print(f"  物流配送费: ¥{filtered['物流配送费'].sum():,.2f}")
    print(f"  企客后返: ¥{filtered['企客后返'].sum():,.2f}")
    print(f"  用户支付配送费: ¥{filtered['用户支付配送费'].sum():,.2f}")
    print(f"  配送费减免金额: ¥{filtered['配送费减免金额'].sum():,.2f}")
    
    print(f"\n【营销成本字段】")
    print(f"  满减金额: ¥{filtered['满减金额'].sum():,.2f}")
    print(f"  商品减免金额: ¥{filtered['商品减免金额'].sum():,.2f}")
    print(f"  新客减免金额: ¥{filtered['新客减免金额'].sum():,.2f}")
    print(f"  商家代金券: ¥{filtered['商家代金券'].sum():,.2f}")
    print(f"  商家承担部分券: ¥{filtered['商家承担部分券'].sum():,.2f}")
    print(f"  满赠金额: ¥{filtered['满赠金额'].sum():,.2f}")
    print(f"  商家其他优惠: ¥{filtered['商家其他优惠'].sum():,.2f}")
    
    # 营销成本总计
    marketing_cost = (
        filtered['满减金额'].sum() +
        filtered['商品减免金额'].sum() +
        filtered['新客减免金额'].sum() +
        filtered['商家代金券'].sum() +
        filtered['商家承担部分券'].sum() +
        filtered['满赠金额'].sum() +
        filtered['商家其他优惠'].sum()
    )
    print(f"  营销成本总计: ¥{marketing_cost:,.2f}")
    
    # 配送净成本
    delivery_net = (
        filtered['物流配送费'].sum() -
        (filtered['用户支付配送费'].sum() - filtered['配送费减免金额'].sum()) -
        filtered['企客后返'].sum()
    )
    print(f"\n【配送净成本】")
    print(f"  物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返")
    print(f"  = {filtered['物流配送费'].sum():.2f} - ({filtered['用户支付配送费'].sum():.2f} - {filtered['配送费减免金额'].sum():.2f}) - {filtered['企客后返'].sum():.2f}")
    print(f"  = ¥{delivery_net:,.2f}")
    
    # 不同公式计算利润
    print(f"\n【不同公式计算利润】")
    
    # 公式1: 当前公式
    profit1 = filtered['利润额'].sum() - filtered['平台服务费'].sum() - filtered['物流配送费'].sum() + filtered['企客后返'].sum()
    print(f"  公式1 (当前): 利润额 - 平台服务费 - 物流配送费 + 企客后返")
    print(f"    = {filtered['利润额'].sum():.2f} - {filtered['平台服务费'].sum():.2f} - {filtered['物流配送费'].sum():.2f} + {filtered['企客后返'].sum():.2f}")
    print(f"    = ¥{profit1:,.2f}")
    
    # 公式2: 使用配送净成本
    profit2 = filtered['利润额'].sum() - filtered['平台服务费'].sum() - delivery_net
    print(f"\n  公式2: 利润额 - 平台服务费 - 配送净成本")
    print(f"    = {filtered['利润额'].sum():.2f} - {filtered['平台服务费'].sum():.2f} - {delivery_net:.2f}")
    print(f"    = ¥{profit2:,.2f}")
    
    # 公式3: 扣除营销成本
    profit3 = profit1 - marketing_cost
    print(f"\n  公式3: 公式1 - 营销成本")
    print(f"    = {profit1:.2f} - {marketing_cost:.2f}")
    print(f"    = ¥{profit3:,.2f}")
    
    # 公式4: 使用平台佣金代替平台服务费
    profit4 = filtered['利润额'].sum() - filtered['平台佣金'].sum() - filtered['物流配送费'].sum() + filtered['企客后返'].sum()
    print(f"\n  公式4: 利润额 - 平台佣金 - 物流配送费 + 企客后返")
    print(f"    = {filtered['利润额'].sum():.2f} - {filtered['平台佣金'].sum():.2f} - {filtered['物流配送费'].sum():.2f} + {filtered['企客后返'].sum():.2f}")
    print(f"    = ¥{profit4:,.2f}")
    
    # 公式5: 实收 - 成本 - 平台服务费 - 物流配送费
    profit5 = filtered['实收价格'].sum() - filtered['商品采购成本'].sum() - filtered['平台服务费'].sum() - filtered['物流配送费'].sum()
    print(f"\n  公式5: 实收价格 - 商品采购成本 - 平台服务费 - 物流配送费")
    print(f"    = {filtered['实收价格'].sum():.2f} - {filtered['商品采购成本'].sum():.2f} - {filtered['平台服务费'].sum():.2f} - {filtered['物流配送费'].sum():.2f}")
    print(f"    = ¥{profit5:,.2f}")
    
    print(f"\n【用户期望】")
    print(f"  用户期望: ¥3,554")
    print(f"  看板显示: ¥4,630")
    print(f"  差异: ¥1,076")
    
    # 检查哪个公式最接近用户期望
    print(f"\n【哪个公式最接近用户期望？】")
    formulas = [
        ("公式1 (当前)", profit1),
        ("公式2 (配送净成本)", profit2),
        ("公式3 (扣营销)", profit3),
        ("公式4 (平台佣金)", profit4),
        ("公式5 (实收-成本)", profit5),
    ]
    for name, value in formulas:
        diff = abs(value - 3554)
        print(f"  {name}: ¥{value:,.2f}, 与用户期望差异: ¥{diff:,.2f}")


if __name__ == "__main__":
    df = load_all_fields()
    print(f"加载数据: {len(df)} 条, {df['订单ID'].nunique()} 订单")
    analyze_all_cost_components(df)
