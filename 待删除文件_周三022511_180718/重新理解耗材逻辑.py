#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重新理解耗材逻辑
"""

import pandas as pd

# 读取源数据
df = pd.read_excel('实际数据/枫瑞.xlsx')
df_mt = df[df['渠道'] == '美团共橙'].copy()

print("="*80)
print("理解耗材对利润的影响")
print("="*80)

# 1. 检查耗材数据
haocai = df_mt[df_mt['一级分类名'] == '耗材'].copy()
print(f"\n耗材数据:")
print(f"  行数: {len(haocai)}")
print(f"  订单数: {haocai['订单ID'].nunique()}")
print(f"  利润额总和: {haocai['利润额'].sum():.2f} 元")

# 2. 正常商品数据
normal = df_mt[df_mt['一级分类名'] != '耗材'].copy()
print(f"\n正常商品数据:")
print(f"  行数: {len(normal)}")
print(f"  订单数: {normal['订单ID'].nunique()}")
print(f"  利润额总和: {normal['利润额'].sum():.2f} 元")

# 3. 全部数据
print(f"\n全部数据:")
print(f"  行数: {len(df_mt)}")
print(f"  订单数: {df_mt['订单ID'].nunique()}")
print(f"  利润额总和: {df_mt['利润额'].sum():.2f} 元")

# 4. 验证公式
耗材利润 = haocai['利润额'].sum()
正常利润 = normal['利润额'].sum()
全部利润 = df_mt['利润额'].sum()

print(f"\n验证公式:")
print(f"  正常商品利润: {正常利润:.2f}")
print(f"  耗材利润(负值): {耗材利润:.2f}")
print(f"  理论总利润: {正常利润:.2f} + ({耗材利润:.2f}) = {正常利润 + 耗材利润:.2f}")
print(f"  实际总利润: {全部利润:.2f}")
print(f"  ✅ 公式验证: {abs((正常利润 + 耗材利润) - 全部利润) < 0.01}")

print("\n" + "="*80)
print("结论:")
print("="*80)
print("耗材利润是负值(-548.81元),在计算总利润时会**自动减去**")
print("所以:")
print(f"  不剔除耗材: 利润额 = {全部利润:.2f}元 (已经减去了耗材亏损)")
print(f"  剔除耗材后: 利润额 = {正常利润:.2f}元 (去掉负值,反而更高)")

# 5. 现在计算订单实际利润
print("\n" + "="*80)
print("计算订单实际利润(不剔除耗材):")
print("="*80)

# 按订单聚合
order_agg = df_mt.groupby('订单ID').agg({
    '利润额': 'sum',
    '平台服务费': 'sum',
    '平台佣金': 'first',
    '物流配送费': 'first',
    '企客后返': 'sum'
}).reset_index()

print(f"订单数: {len(order_agg)}")
print(f"利润额总和: {order_agg['利润额'].sum():.2f}")
print(f"平台服务费总和: {order_agg['平台服务费'].sum():.2f}")
print(f"物流配送费总和: {order_agg['物流配送费'].sum():.2f}")

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

print(f"\n订单实际利润(all_with_fallback): {profit.sum():.2f} 元")

# 不用兜底逻辑
valid_orders = order_agg[order_agg['平台服务费'] > 0]
profit_no_fallback = (
    valid_orders['利润额'] -
    valid_orders['平台服务费'] -
    valid_orders['物流配送费'] +
    valid_orders['企客后返']
)

print(f"订单实际利润(all_no_fallback): {profit_no_fallback.sum():.2f} 元")
print(f"被过滤订单数: {len(order_agg) - len(valid_orders)}")
