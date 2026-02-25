# -*- coding: utf-8 -*-
"""
详细诊断利润差异 - 检查所有可能的扣减项
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

PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播',
    '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店'
]

def load_all_fields():
    """加载所有可能相关的字段"""
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
                '商品名称': o.product_name,
                # 核心利润字段
                '利润额': float(o.profit or 0),
                '平台服务费': float(o.platform_service_fee or 0),
                '物流配送费': float(o.delivery_fee or 0),
                '企客后返': float(o.corporate_rebate or 0),
                # 其他可能的扣减项
                '平台佣金': float(o.commission or 0),
                '满减金额': float(o.full_reduction or 0),
                '商品减免金额': float(o.product_discount or 0),
                '商家代金券': float(o.merchant_voucher or 0),
                '商家承担部分券': float(o.merchant_share or 0),
                '配送费减免金额': float(o.delivery_discount or 0),
                '用户支付配送费': float(o.user_paid_delivery_fee or 0),
                '打包袋金额': float(o.packaging_fee or 0),
                # 收入字段
                '实收价格': float(o.actual_price or 0),
                '商品实售价': float(o.price or 0),
                '预计订单收入': float(o.amount or 0),
                '月售': o.quantity or 1,
                '商品采购成本': float(o.cost or 0),
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


def analyze_all_costs(df):
    """分析所有成本项"""
    print("\n" + "=" * 70)
    print("【所有字段汇总】")
    print("=" * 70)
    
    # 按订单聚合
    order_agg = df.groupby('订单ID').agg({
        '渠道': 'first',
        # 商品级字段 - sum
        '利润额': 'sum',
        '平台服务费': 'sum',
        '企客后返': 'sum',
        '实收价格': 'sum',
        '商品实售价': 'sum',
        '预计订单收入': 'sum',
        '月售': 'sum',
        '商品采购成本': 'sum',
        # 订单级字段 - first
        '物流配送费': 'first',
        '平台佣金': 'first',
        '满减金额': 'first',
        '商品减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',
        '配送费减免金额': 'first',
        '用户支付配送费': 'first',
        '打包袋金额': 'first',
    }).reset_index()
    
    # 过滤异常订单
    is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    filtered = order_agg[~invalid_orders]
    
    print(f"过滤后订单数: {len(filtered)}")
    print()
    
    # 打印所有字段汇总
    fields = [
        ('利润额', '商品级'),
        ('平台服务费', '商品级'),
        ('物流配送费', '订单级'),
        ('企客后返', '商品级'),
        ('平台佣金', '订单级'),
        ('满减金额', '订单级'),
        ('商品减免金额', '订单级'),
        ('商家代金券', '订单级'),
        ('商家承担部分券', '订单级'),
        ('配送费减免金额', '订单级'),
        ('用户支付配送费', '订单级'),
        ('打包袋金额', '订单级'),
        ('实收价格', '商品级'),
        ('商品实售价', '商品级'),
        ('预计订单收入', '商品级'),
        ('商品采购成本', '商品级'),
    ]
    
    for field, level in fields:
        total = filtered[field].sum()
        print(f"  {field} ({level}): ¥{total:,.2f}")
    
    return filtered


def calculate_different_formulas(filtered):
    """尝试不同的利润计算公式"""
    print("\n" + "=" * 70)
    print("【不同公式计算结果】")
    print("=" * 70)
    
    profit = filtered['利润额'].sum()
    platform_fee = filtered['平台服务费'].sum()
    delivery_fee = filtered['物流配送费'].sum()
    rebate = filtered['企客后返'].sum()
    commission = filtered['平台佣金'].sum()
    full_reduction = filtered['满减金额'].sum()
    product_discount = filtered['商品减免金额'].sum()
    merchant_voucher = filtered['商家代金券'].sum()
    merchant_share = filtered['商家承担部分券'].sum()
    delivery_discount = filtered['配送费减免金额'].sum()
    user_delivery = filtered['用户支付配送费'].sum()
    
    print("\n【公式1】权威公式:")
    print(f"  订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返")
    result1 = profit - platform_fee - delivery_fee + rebate
    print(f"  = {profit:.2f} - {platform_fee:.2f} - {delivery_fee:.2f} + {rebate:.2f}")
    print(f"  = ¥{result1:,.2f}")
    
    print("\n【公式2】扣除配送净成本:")
    print(f"  配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额)")
    delivery_net = delivery_fee - (user_delivery - delivery_discount)
    print(f"  = {delivery_fee:.2f} - ({user_delivery:.2f} - {delivery_discount:.2f})")
    print(f"  = ¥{delivery_net:,.2f}")
    result2 = profit - platform_fee - delivery_net + rebate
    print(f"  订单实际利润 = 利润额 - 平台服务费 - 配送净成本 + 企客后返")
    print(f"  = {profit:.2f} - {platform_fee:.2f} - {delivery_net:.2f} + {rebate:.2f}")
    print(f"  = ¥{result2:,.2f}")
    
    print("\n【公式3】扣除营销成本:")
    marketing = full_reduction + product_discount + merchant_voucher + merchant_share
    print(f"  营销成本 = 满减 + 商品减免 + 商家代金券 + 商家承担券")
    print(f"  = {full_reduction:.2f} + {product_discount:.2f} + {merchant_voucher:.2f} + {merchant_share:.2f}")
    print(f"  = ¥{marketing:,.2f}")
    result3 = profit - platform_fee - delivery_fee + rebate - marketing
    print(f"  订单实际利润 = 权威公式结果 - 营销成本")
    print(f"  = {result1:.2f} - {marketing:.2f}")
    print(f"  = ¥{result3:,.2f}")
    
    print("\n【公式4】使用平台佣金代替平台服务费:")
    result4 = profit - commission - delivery_fee + rebate
    print(f"  订单实际利润 = 利润额 - 平台佣金 - 物流配送费 + 企客后返")
    print(f"  = {profit:.2f} - {commission:.2f} - {delivery_fee:.2f} + {rebate:.2f}")
    print(f"  = ¥{result4:,.2f}")
    
    print("\n【公式5】扣除配送费减免:")
    result5 = profit - platform_fee - delivery_fee + rebate - delivery_discount
    print(f"  订单实际利润 = 权威公式 - 配送费减免金额")
    print(f"  = {result1:.2f} - {delivery_discount:.2f}")
    print(f"  = ¥{result5:,.2f}")
    
    print("\n" + "=" * 70)
    print("【与用户期望值对比】")
    print("=" * 70)
    user_expected = 3554
    print(f"用户期望: ¥{user_expected:,.2f}")
    print()
    print(f"公式1 差异: ¥{result1 - user_expected:,.2f}")
    print(f"公式2 差异: ¥{result2 - user_expected:,.2f}")
    print(f"公式3 差异: ¥{result3 - user_expected:,.2f}")
    print(f"公式4 差异: ¥{result4 - user_expected:,.2f}")
    print(f"公式5 差异: ¥{result5 - user_expected:,.2f}")
    
    # 检查哪个公式最接近
    results = [
        ('公式1-权威公式', result1),
        ('公式2-配送净成本', result2),
        ('公式3-扣营销成本', result3),
        ('公式4-用平台佣金', result4),
        ('公式5-扣配送减免', result5),
    ]
    
    closest = min(results, key=lambda x: abs(x[1] - user_expected))
    print(f"\n最接近用户期望的是: {closest[0]} = ¥{closest[1]:,.2f}")


def check_daily_breakdown(df):
    """按日期分解检查"""
    print("\n" + "=" * 70)
    print("【按日期分解】")
    print("=" * 70)
    
    # 按订单聚合
    order_agg = df.groupby('订单ID').agg({
        '日期': 'first',
        '渠道': 'first',
        '利润额': 'sum',
        '平台服务费': 'sum',
        '物流配送费': 'first',
        '企客后返': 'sum',
    }).reset_index()
    
    # 过滤
    is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    filtered = order_agg[~invalid_orders]
    
    # 计算订单实际利润
    filtered['订单实际利润'] = (
        filtered['利润额'] - 
        filtered['平台服务费'] - 
        filtered['物流配送费'] + 
        filtered['企客后返']
    )
    
    # 按日期汇总
    filtered['日期'] = pd.to_datetime(filtered['日期']).dt.date
    daily = filtered.groupby('日期').agg({
        '订单ID': 'count',
        '利润额': 'sum',
        '平台服务费': 'sum',
        '物流配送费': 'sum',
        '订单实际利润': 'sum',
    }).reset_index()
    daily.columns = ['日期', '订单数', '利润额', '平台服务费', '物流配送费', '订单实际利润']
    
    print(daily.to_string(index=False))
    print()
    print(f"合计: 订单数={daily['订单数'].sum()}, 订单实际利润=¥{daily['订单实际利润'].sum():,.2f}")


if __name__ == "__main__":
    print(f"门店: {STORE_NAME}")
    print(f"日期: {START_DATE} ~ {END_DATE}")
    
    df = load_all_fields()
    print(f"加载数据: {len(df)} 条, {df['订单ID'].nunique()} 订单")
    
    filtered = analyze_all_costs(df)
    calculate_different_formulas(filtered)
    check_daily_breakdown(df)
