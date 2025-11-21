#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对比三种利润计算方案
"""

import pandas as pd
import numpy as np

# 读取源数据
df = pd.read_excel('实际数据/枫瑞.xlsx')
print(f"原始数据: {len(df)}行")

# 筛选美团共橙
df_mt = df[df['渠道'] == '美团共橙'].copy()
print(f"美团共橙数据: {len(df_mt)}行, {df_mt['订单ID'].nunique()}个订单")

# 复制兜底逻辑
def calculate_with_fallback(data):
    """all_with_fallback模式 - 完全模拟核心代码逻辑"""
    order_agg = data.groupby('订单ID').agg({
        '利润额': 'sum',           # 商品级,sum
        '平台服务费': 'sum',       # 商品级,sum  
        '平台佣金': 'first',       # 订单级,first
        '物流配送费': 'first',     # ⭐订单级,first(不是sum!)
        '企客后返': 'sum'          # 商品级,sum
    }).reset_index()
    
    # 兜底逻辑
    service_fee = order_agg['平台服务费']
    commission = order_agg['平台佣金']
    fallback_mask = (service_fee <= 0)
    service_fee_final = service_fee.mask(fallback_mask, commission)
    
    profit = (
        order_agg['利润额'] -
        service_fee_final -
        order_agg['物流配送费'] +
        order_agg['企客后返']
    )
    
    return order_agg, profit.sum()

def calculate_no_fallback(data):
    """all_no_fallback模式"""
    order_agg = data.groupby('订单ID').agg({
        '利润额': 'sum',
        '平台服务费': 'sum',
        '物流配送费': 'first',    # ⭐订单级,first
        '企客后返': 'sum'
    }).reset_index()
    
    profit = (
        order_agg['利润额'] -
        order_agg['平台服务费'] -
        order_agg['物流配送费'] +
        order_agg['企客后返']
    )
    
    return order_agg, profit.sum()

print("\n" + "="*80)
print("方案对比:")
print("="*80)

# ========== 方案1:剔除耗材 + all_with_fallback(当前方案) ==========
print("\n【方案1:剔除耗材 + all_with_fallback(当前看板使用的方案)】")
df_no_hc = df_mt[df_mt['一级分类名'] != '耗材'].copy()
print(f"剔除耗材后: {len(df_no_hc)}行")
agg1, profit1 = calculate_with_fallback(df_no_hc)
print(f"订单数: {len(agg1)}")
print(f"利润额总和: {agg1['利润额'].sum():.2f}")
print(f"平台服务费: {agg1['平台服务费'].sum():.2f}")
print(f"物流配送费: {agg1['物流配送费'].sum():.2f}")
print(f"订单实际利润: {profit1:.2f} 元")
print("优点: 剔除亏损耗材,数据更全面(保留服务费为0的订单)")
print("缺点: 利润较低(因为保留了更多订单)")

# ========== 方案2:不剔除耗材 + all_with_fallback ==========
print("\n【方案2:不剔除耗材 + all_with_fallback】")
agg2, profit2 = calculate_with_fallback(df_mt)
print(f"订单数: {len(agg2)}")
print(f"利润额总和: {agg2['利润额'].sum():.2f}")
print(f"平台服务费: {agg2['平台服务费'].sum():.2f}")
print(f"物流配送费: {agg2['物流配送费'].sum():.2f}")
print(f"订单实际利润: {profit2:.2f} 元")
耗材利润 = agg2['利润额'].sum() - agg1['利润额'].sum()
print(f"耗材利润: {耗材利润:.2f} 元")
print("优点: 数据完整,包含所有商品")
print("缺点: 利润更低(因为耗材亏损)")

# ========== 方案3:剔除耗材 + all_no_fallback ==========
print("\n【方案3:剔除耗材 + all_no_fallback(不用兜底逻辑)】")
# 先过滤服务费为0的订单
valid_orders = df_no_hc.groupby('订单ID')['平台服务费'].sum()
valid_orders = valid_orders[valid_orders > 0].index
df_filtered = df_no_hc[df_no_hc['订单ID'].isin(valid_orders)].copy()
print(f"过滤服务费<=0订单后: {len(df_filtered)}行")
agg3, profit3 = calculate_no_fallback(df_filtered)
print(f"订单数: {len(agg3)}")
print(f"利润额总和: {agg3['利润额'].sum():.2f}")
print(f"平台服务费: {agg3['平台服务费'].sum():.2f}")
print(f"物流配送费: {agg3['物流配送费'].sum():.2f}")
print(f"订单实际利润: {profit3:.2f} 元")
被过滤订单 = len(agg1) - len(agg3)
print(f"被过滤掉的订单数: {被过滤订单}")
print("优点: 利润最高,只计算有服务费的订单")
print("缺点: 数据不全(丢失了服务费为0的订单)")

print("\n" + "="*80)
print("总结:")
print("="*80)
print(f"方案1(当前): {profit1:.2f}元 - 剔除耗材,保留所有订单")
print(f"方案2:        {profit2:.2f}元 - 包含耗材,保留所有订单")
print(f"方案3:        {profit3:.2f}元 - 剔除耗材,只保留有服务费的订单")

print("\n推荐方案:")
print("如果您认为耗材不应该计入利润 → 使用方案1(当前方案)")
print("如果您认为耗材也是成本的一部分 → 使用方案2")
print("如果您认为服务费为0的订单不合理 → 使用方案3")
