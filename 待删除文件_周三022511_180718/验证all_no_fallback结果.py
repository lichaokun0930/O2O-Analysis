#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证:改为all_no_fallback后是否得到652.06
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# 模拟核心代码逻辑
df = pd.read_excel('实际数据/枫瑞.xlsx')
print(f"原始数据: {len(df)}行")

# Step 1: 剔除耗材(Line 1016逻辑)
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
print(f"利润额: {order_agg['利润额'].sum():.2f}")

# Step 4: all_no_fallback模式 - 过滤服务费<=0
valid_orders = order_agg[order_agg['平台服务费'] > 0].copy()
print(f"\n过滤服务费<=0后: {len(valid_orders)}个订单")
print(f"被过滤: {len(order_agg) - len(valid_orders)}个订单")

# Step 5: 计算利润(不用兜底逻辑)
profit = (
    valid_orders['利润额'] -
    valid_orders['平台服务费'] -
    valid_orders['物流配送费'] +
    valid_orders['企客后返']
)

print(f"\n最终结果:")
print(f"订单实际利润 = {profit.sum():.2f} 元")
print(f"\n✅ 这就是改为all_no_fallback后的结果!")
print(f"{'='*60}")
print(f"预期结果: 652.06元")
print(f"实际结果: {profit.sum():.2f}元")
print(f"是否匹配: {'✅ 正确!' if abs(profit.sum() - 652.06) < 0.01 else '❌ 不匹配'}")
