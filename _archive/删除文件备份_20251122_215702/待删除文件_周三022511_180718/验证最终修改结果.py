#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证修改后的最终结果
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from 智能门店看板_Dash版 import calculate_order_metrics

# 加载数据
df = pd.read_excel('实际数据/枫瑞.xlsx')

print("=" * 80)
print("验证修改后的计算结果")
print("=" * 80)

# 不剔除耗材(因为已经注释掉Line 1016)
print(f"\n原始数据: {len(df)}行")

# 筛选美团共橙渠道
mt_data = df[df['渠道'] == '美团共橙'].copy()
print(f"美团共橙数据: {len(mt_data)}行, {mt_data['订单ID'].nunique()}个订单")

# 使用核心代码的calculate_order_metrics函数(all_no_fallback模式)
print(f"\n调用 calculate_order_metrics(calc_mode='all_no_fallback')")
order_agg = calculate_order_metrics(mt_data, calc_mode='all_no_fallback')

# 统计结果
print(f"\n" + "=" * 80)
print(f"📊 最终计算结果:")
print(f"=" * 80)
print(f"  订单数: {len(order_agg)}")
print(f"  利润额总和: {order_agg['利润额'].sum():.2f}")
print(f"  平台服务费总和: {order_agg['平台服务费'].sum():.2f}")
print(f"  物流配送费总和: {order_agg['物流配送费'].sum():.2f}")
print(f"  企客后返总和: {order_agg['企客后返'].sum():.2f}")
print(f"  订单实际利润总和: {order_agg['订单实际利润'].sum():.2f}")

print(f"\n✅ 美团共橙订单实际利润 = {order_agg['订单实际利润'].sum():.2f} 元")
print(f"\n{'='*80}")
print(f"预期结果: 652.06元")
print(f"实际结果: {order_agg['订单实际利润'].sum():.2f}元")
print(f"是否匹配: {'✅ 完全正确!' if abs(order_agg['订单实际利润'].sum() - 652.06) < 0.01 else '❌ 不匹配'}")
print("=" * 80)
