#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整自检:模拟看板完整流程
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("="*80)
print("🔍 完整自检:模拟看板加载流程")
print("="*80)

# ========== Step 1: 模拟数据库加载 ==========
print("\n【Step 1: 模拟数据库加载】")
from database.data_source_manager import DataSourceManager

dsm = DataSourceManager()
df_from_db = dsm.load_from_database(
    store_name='惠宜选超市（苏州枫瑞路店）',
    start_date=None,
    end_date=None
)

print(f"数据库加载结果: {len(df_from_db)}行")
if '一级分类名' in df_from_db.columns:
    haocai_count = (df_from_db['一级分类名'] == '耗材').sum()
    print(f"耗材行数: {haocai_count}")
    if haocai_count > 0:
        haocai_profit = df_from_db[df_from_db['一级分类名'] == '耗材']['利润额'].sum()
        print(f"耗材利润: {haocai_profit:.2f}")

# 检查美团共橙
if '渠道' in df_from_db.columns:
    mt = df_from_db[df_from_db['渠道'] == '美团共橙']
    print(f"\n美团共橙数据: {len(mt)}行, {mt['订单ID'].nunique() if len(mt) > 0 else 0}个订单")
    if len(mt) > 0:
        print(f"美团共橙利润额: {mt['利润额'].sum():.2f}")

# ========== Step 2: 使用核心代码计算 ==========
print("\n【Step 2: 使用calculate_order_metrics计算】")
from 智能门店看板_Dash版 import calculate_order_metrics

if len(mt) > 0:
    order_agg = calculate_order_metrics(mt, calc_mode='all_no_fallback')
    
    print(f"\n最终结果:")
    print(f"  订单数: {len(order_agg)}")
    print(f"  利润额: {order_agg['利润额'].sum():.2f}")
    print(f"  平台服务费: {order_agg['平台服务费'].sum():.2f}")
    print(f"  物流配送费: {order_agg['物流配送费'].sum():.2f}")
    print(f"  订单实际利润: {order_agg['订单实际利润'].sum():.2f}")
    
    print(f"\n{'='*80}")
    print(f"🎯 预期: 652.06元")
    print(f"🎯 实际: {order_agg['订单实际利润'].sum():.2f}元")
    print(f"{'='*80}")
    
    if abs(order_agg['订单实际利润'].sum() - 652.06) < 0.01:
        print("✅ 结果正确!")
    elif abs(order_agg['订单实际利润'].sum() - 1201.17) < 0.01:
        print("❌ 还是1201.17,耗材未被保留!")
    else:
        print(f"❌ 结果不符,实际为{order_agg['订单实际利润'].sum():.2f}")
else:
    print("❌ 没有美团共橙数据!")
