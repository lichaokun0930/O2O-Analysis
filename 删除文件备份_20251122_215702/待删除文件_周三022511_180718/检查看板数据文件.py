#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查看板实际加载的数据文件
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from 智能门店看板_Dash版 import calculate_order_metrics

# 看板实际加载的文件
file = '实际数据/2025-10-19 00_00_00至2025-11-17 23_59_59订单明细数据导出汇总.xlsx'
df = pd.read_excel(file)

print(f"看板加载的文件: {file}")
print(f"原始数据: {len(df)}行")

# 检查是否有耗材
if '一级分类名' in df.columns:
    haocai = df[df['一级分类名'] == '耗材']
    print(f"耗材数据: {len(haocai)}行")
    if len(haocai) > 0:
        print(f"耗材利润: {haocai['利润额'].sum():.2f}元")

# 检查美团共橙数据
if '渠道' in df.columns:
    mt = df[df['渠道'] == '美团共橙']
    print(f"\n美团共橙数据: {len(mt)}行, {mt['订单ID'].nunique()}个订单")
    print(f"美团共橙利润额总和: {mt['利润额'].sum():.2f}元")
    
    # 计算订单实际利润
    print("\n使用calculate_order_metrics计算:")
    order_agg = calculate_order_metrics(mt, calc_mode='all_no_fallback')
    print(f"订单数: {len(order_agg)}")
    print(f"利润额: {order_agg['利润额'].sum():.2f}")
    print(f"订单实际利润: {order_agg['订单实际利润'].sum():.2f} 元")
else:
    print("数据中没有渠道字段!")
