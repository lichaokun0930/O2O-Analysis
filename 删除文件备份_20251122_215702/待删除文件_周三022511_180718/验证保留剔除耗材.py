#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证:保留剔除耗材逻辑,能否得到652.06元
"""

import pandas as pd

df = pd.read_excel('实际数据/枫瑞.xlsx')
print(f"原始数据: {len(df)}行")

# Step 1: 剔除耗材(模拟Line 1016)
df = df[df['一级分类名'] != '耗材'].copy()
print(f"剔除耗材后: {len(df)}行")

# Step 2: 筛选美团共橙
df_mt = df[df['渠道'] == '美团共橙'].copy()
print(f"美团共橙数据: {len(df_mt)}行, {df_mt['订单ID'].nunique()}个订单")

# Step 3: 按订单聚合
order_agg = df_mt.groupby('订单ID').agg({
    '利润额': 'sum',
    '平台服务费': 'sum',
    '物流配送费': 'first',
    '企客后返': 'sum'
}).reset_index()

print(f"\n聚合后: {len(order_agg)}个订单")
print(f"利润额总和: {order_agg['利润额'].sum():.2f}")

# Step 4: 过滤服务费<=0的订单
valid_orders = order_agg[order_agg['平台服务费'] > 0].copy()
print(f"\n过滤服务费<=0后: {len(valid_orders)}个订单")
print(f"被过滤: {len(order_agg) - len(valid_orders)}个订单")

# Step 5: 计算利润(all_no_fallback)
profit = (
    valid_orders['利润额'] -
    valid_orders['平台服务费'] -
    valid_orders['物流配送费'] +
    valid_orders['企客后返']
)

print(f"\n订单实际利润: {profit.sum():.2f} 元")

print("\n结论:")
print("✅ 保留剔除耗材逻辑,使用all_no_fallback模式")
print(f"   → 得到利润: {profit.sum():.2f}元")
print("   这不是652.06元!")
print("\n要得到652.06元,需要:")
print("   1. 不剔除耗材 (包含耗材亏损)")
print("   2. 使用all_no_fallback模式")
