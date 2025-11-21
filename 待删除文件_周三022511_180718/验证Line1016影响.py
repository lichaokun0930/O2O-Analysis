#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证:保留Line 1016剔除耗材逻辑,但在计算时不剔除
"""

import pandas as pd

df = pd.read_excel('实际数据/枫瑞.xlsx')
print(f"原始数据: {len(df)}行")

print("\n" + "="*80)
print("方案A: 在数据加载时剔除耗材(Line 1016逻辑)")
print("="*80)

# 模拟Line 1016: 数据加载时剔除耗材
df_loaded = df[df['一级分类名'] != '耗材'].copy()
print(f"加载数据(剔除耗材): {len(df_loaded)}行")

df_mt_a = df_loaded[df_loaded['渠道'] == '美团共橙'].copy()
print(f"美团共橙数据: {len(df_mt_a)}行, {df_mt_a['订单ID'].nunique()}个订单")

order_agg_a = df_mt_a.groupby('订单ID').agg({
    '利润额': 'sum',
    '平台服务费': 'sum',
    '物流配送费': 'first',
}).reset_index()

valid_a = order_agg_a[order_agg_a['平台服务费'] > 0].copy()
profit_a = (valid_a['利润额'] - valid_a['平台服务费'] - valid_a['物流配送费']).sum()

print(f"订单数: {len(valid_a)}")
print(f"利润额: {valid_a['利润额'].sum():.2f}")
print(f"订单实际利润: {profit_a:.2f} 元")

print("\n" + "="*80)
print("方案B: 数据加载时不剔除耗材")
print("="*80)

# 不剔除耗材
df_mt_b = df[df['渠道'] == '美团共橙'].copy()
print(f"美团共橙数据: {len(df_mt_b)}行, {df_mt_b['订单ID'].nunique()}个订单")

order_agg_b = df_mt_b.groupby('订单ID').agg({
    '利润额': 'sum',
    '平台服务费': 'sum',
    '物流配送费': 'first',
}).reset_index()

valid_b = order_agg_b[order_agg_b['平台服务费'] > 0].copy()
profit_b = (valid_b['利润额'] - valid_b['平台服务费'] - valid_b['物流配送费']).sum()

print(f"订单数: {len(valid_b)}")
print(f"利润额: {valid_b['利润额'].sum():.2f}")
print(f"订单实际利润: {profit_b:.2f} 元")

print("\n" + "="*80)
print("结论:")
print("="*80)
print(f"方案A(剔除耗材): {profit_a:.2f}元")
print(f"方案B(不剔除耗材): {profit_b:.2f}元")
print(f"\n要得到652.06元,必须使用方案B!")
print("因为Line 1016在数据加载时就把耗材删除了,")
print("后续计算中订单的利润额已经不包含耗材了!")
