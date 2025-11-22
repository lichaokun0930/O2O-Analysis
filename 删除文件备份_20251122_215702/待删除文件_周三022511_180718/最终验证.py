#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终验证:确认美团共橙利润为652.06元
"""

from database.connection import SessionLocal
from database.models import Order
import pandas as pd

print("="*80)
print("🎯 最终验证:美团共橙利润计算")
print("="*80)

db = SessionLocal()

# 查询美团共橙数据
print("\n【Step 1: 从数据库加载美团共橙数据】")
query = db.query(Order).filter(
    Order.store_name == '惠宜选超市（苏州枫瑞路店）',
    Order.channel == '美团共橙'
)

orders = query.all()
print(f"订单数: {len(orders):,} 条")

# 转换为DataFrame
data = []
for order in orders:
    data.append({
        '订单ID': order.order_id,
        '利润额': order.profit or 0,
        '平台服务费': order.platform_service_fee or 0,
        '物流配送费': order.delivery_fee or 0,
        '企客后返': order.corporate_rebate or 0,
    })

df = pd.DataFrame(data)
print(f"\n原始数据: {len(df)} 行")
print(f"唯一订单: {df['订单ID'].nunique()} 个")

# 按订单聚合
print("\n【Step 2: 按订单聚合】")
order_agg = df.groupby('订单ID').agg({
    '利润额': 'sum',
    '平台服务费': 'sum',
    '物流配送费': 'sum',
    '企客后返': 'sum',
}).reset_index()

print(f"聚合后订单数: {len(order_agg)}")

# 过滤服务费<=0的订单
print("\n【Step 3: 过滤服务费<=0的订单(all_no_fallback模式)】")
before = len(order_agg)
order_agg = order_agg[order_agg['平台服务费'] > 0]
filtered = before - len(order_agg)
print(f"过滤掉: {filtered} 个订单")
print(f"剩余: {len(order_agg)} 个订单")

# 计算订单实际利润
print("\n【Step 4: 计算订单实际利润】")
order_agg['订单实际利润'] = (
    order_agg['利润额'] 
    - order_agg['平台服务费'] 
    - order_agg['物流配送费']
    + order_agg['企客后返']
)

total_profit = order_agg['订单实际利润'].sum()

print(f"\n{'='*80}")
print(f"🎯 最终结果:")
print(f"{'='*80}")
print(f"  订单数: {len(order_agg)}")
print(f"  利润额: {order_agg['利润额'].sum():.2f}")
print(f"  平台服务费: {order_agg['平台服务费'].sum():.2f}")
print(f"  物流配送费: {order_agg['物流配送费'].sum():.2f}")
print(f"  企客后返: {order_agg['企客后返'].sum():.2f}")
print(f"  订单实际利润: {total_profit:.2f}")
print(f"{'='*80}")

if abs(total_profit - 652.06) < 1:
    print("✅ 结果正确! 利润为652.06元")
else:
    print(f"❌ 结果异常: {total_profit:.2f} (预期: 652.06)")

db.close()
