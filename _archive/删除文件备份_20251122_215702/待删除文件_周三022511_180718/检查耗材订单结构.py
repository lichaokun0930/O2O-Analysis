#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查耗材和正常商品是否在同一订单
"""

import pandas as pd

df = pd.read_excel('实际数据/枫瑞.xlsx')
df_mt = df[df['渠道'] == '美团共橙'].copy()

print("="*80)
print("检查耗材订单结构")
print("="*80)

# 统计每个订单的商品类型
order_analysis = df_mt.groupby('订单ID').apply(
    lambda x: pd.Series({
        '总商品数': len(x),
        '耗材数': len(x[x['一级分类名'] == '耗材']),
        '正常商品数': len(x[x['一级分类名'] != '耗材']),
        '是否纯耗材订单': (x['一级分类名'] == '耗材').all(),
        '是否混合订单': (x['一级分类名'] == '耗材').any() and not (x['一级分类名'] == '耗材').all()
    })
).reset_index()

print(f"\n订单类型分布:")
纯耗材订单 = order_analysis[order_analysis['是否纯耗材订单']].shape[0]
混合订单 = order_analysis[order_analysis['是否混合订单']].shape[0]
纯正常订单 = order_analysis[(~order_analysis['是否纯耗材订单']) & (~order_analysis['是否混合订单'])].shape[0]

print(f"  纯正常商品订单: {纯正常订单} 个")
print(f"  混合订单(既有正常商品又有耗材): {混合订单} 个")
print(f"  纯耗材订单: {纯耗材订单} 个")
print(f"  总订单数: {len(order_analysis)} 个")

# 看看混合订单的例子
if 混合订单 > 0:
    print(f"\n混合订单示例(前5个):")
    mixed_orders = order_analysis[order_analysis['是否混合订单']].head()
    for _, row in mixed_orders.iterrows():
        order_id = row['订单ID']
        print(f"\n  订单ID: {order_id}")
        print(f"    正常商品: {int(row['正常商品数'])}件")
        print(f"    耗材: {int(row['耗材数'])}件")
        
        # 显示这个订单的明细
        order_detail = df_mt[df_mt['订单ID'] == order_id][['商品名称', '一级分类名', '利润额']]
        for idx, item in order_detail.iterrows():
            print(f"      - {item['商品名称'][:20]:20s} | {item['一级分类名']:6s} | 利润:{item['利润额']:8.2f}")

print("\n" + "="*80)
print("关键问题:")
print("="*80)

# 计算利润差异
不剔除耗材_按订单汇总 = df_mt.groupby('订单ID')['利润额'].sum().sum()
剔除耗材_按订单汇总 = df_mt[df_mt['一级分类名'] != '耗材'].groupby('订单ID')['利润额'].sum().sum()

print(f"\n情况1: 不剔除耗材,按订单汇总利润额")
print(f"  利润额总和: {不剔除耗材_按订单汇总:.2f}")

print(f"\n情况2: 先剔除耗材,再按订单汇总利润额")
print(f"  利润额总和: {剔除耗材_按订单汇总:.2f}")

print(f"\n差异: {剔除耗材_按订单汇总 - 不剔除耗材_按订单汇总:.2f}元")

# 如果有混合订单
if 混合订单 > 0:
    print("\n" + "="*80)
    print("您说得对!")
    print("="*80)
    print(f"在{混合订单}个混合订单中,耗材和正常商品在同一订单里。")
    print("当我们剔除耗材时:")
    print("  ✅ 订单还在(因为还有正常商品)")
    print("  ❌ 但是订单的利润额少了(因为耗材的负值不算了)")
    print("\n这就是为什么剔除耗材后,利润反而增加!")
    print("因为那些负值不再拉低订单利润了!")
