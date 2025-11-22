#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终完整计算 - 不剔除耗材 + all_no_fallback
"""

import pandas as pd

df = pd.read_excel('实际数据/枫瑞.xlsx')
print(f"原始数据: {len(df)}行")

# ✅ 不剔除耗材
df_mt = df[df['渠道'] == '美团共橙'].copy()
print(f"美团共橙数据: {len(df_mt)}行, {df_mt['订单ID'].nunique()}个订单")

# 按订单聚合
order_agg = df_mt.groupby('订单ID').agg({
    '利润额': 'sum',
    '平台服务费': 'sum',
    '物流配送费': 'first',
    '企客后返': 'sum'
}).reset_index()

print(f"\n聚合后: {len(order_agg)}个订单")
print(f"利润额总和: {order_agg['利润额'].sum():.2f}")
print(f"平台服务费总和: {order_agg['平台服务费'].sum():.2f}")
print(f"物流配送费总和: {order_agg['物流配送费'].sum():.2f}")
print(f"企客后返总和: {order_agg['企客后返'].sum():.2f}")

# 过滤服务费<=0的订单
print("\n" + "="*80)
print("过滤服务费<=0的订单:")
print("="*80)
valid_orders = order_agg[order_agg['平台服务费'] > 0].copy()
print(f"过滤前: {len(order_agg)}个订单")
print(f"过滤后: {len(valid_orders)}个订单")
print(f"被过滤: {len(order_agg) - len(valid_orders)}个订单")

print(f"\n过滤后数据:")
print(f"利润额总和: {valid_orders['利润额'].sum():.2f}")
print(f"平台服务费总和: {valid_orders['平台服务费'].sum():.2f}")
print(f"物流配送费总和: {valid_orders['物流配送费'].sum():.2f}")
print(f"企客后返总和: {valid_orders['企客后返'].sum():.2f}")

# 计算订单实际利润 (all_no_fallback模式)
profit = (
    valid_orders['利润额'] -
    valid_orders['平台服务费'] -
    valid_orders['物流配送费'] +
    valid_orders['企客后返']
)

print("\n" + "="*80)
print("最终结果:")
print("="*80)
print(f"计算公式: 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返")
print(f"\n订单实际利润 = {valid_orders['利润额'].sum():.2f} - {valid_orders['平台服务费'].sum():.2f} - {valid_orders['物流配送费'].sum():.2f} + {valid_orders['企客后返'].sum():.2f}")
print(f"             = {profit.sum():.2f} 元")

print("\n✅ 这就是不剔除耗材 + all_no_fallback的结果!")
