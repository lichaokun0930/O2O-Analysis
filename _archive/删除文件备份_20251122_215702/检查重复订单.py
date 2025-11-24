#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查Excel数据中的重复订单ID问题
"""

import pandas as pd

# 读取Excel
df = pd.read_excel('实际数据/2025-10-23 00_00_00至2025-11-21 23_59_59订单明细数据导出汇总.xlsx')

print("=" * 70)
print("📊 Excel数据分析")
print("=" * 70)
print(f'Excel总行数: {len(df):,}')
print(f'唯一订单ID数: {df["订单ID"].nunique():,}')
print(f'重复订单ID数: {len(df) - df["订单ID"].nunique():,}')
print(f'重复率: {(len(df) - df["订单ID"].nunique()) / len(df) * 100:.1f}%')

# 检查重复订单
duplicates = df[df.duplicated(subset=['订单ID'], keep=False)].sort_values('订单ID')
print(f'\n重复订单总数: {len(duplicates):,}')
print(f'\n前10个重复订单示例:')
print(duplicates[['订单ID', '商品名称', '一级分类名']].head(10).to_string())

# 统计每个订单ID的重复次数
order_counts = df['订单ID'].value_counts()
max_duplicate = order_counts.max()
print(f'\n最多重复次数: {max_duplicate}')
print(f'重复超过5次的订单: {(order_counts > 5).sum()}个')

# 分析原因：一个订单包含多个商品
print("\n" + "=" * 70)
print("🔍 原因分析")
print("=" * 70)
print("美团订单特点：一个订单ID可以购买多个不同商品")
print("例如：订单2409300025410600包含3件商品（纯牛奶、旺旺雪饼、百吉福芝士）")
print("\n当前问题：数据库设计用order_id作为主键，但一个订单有多行数据")
print("解决方案：使用复合主键 (order_id + 商品名称) 或添加行号字段")
