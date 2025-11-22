#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path.cwd()))
from database.data_source_manager import DataSourceManager

dsm = DataSourceManager()

# 加载祥和路店数据
print('尝试加载祥和路店数据...')
try:
    result = dsm.load_from_database(store_name='惠宜选超市（苏州祥和路店）')
    print('✅ 成功加载祥和路店')
except Exception as e:
    print(f'❌ 加载祥和路店失败: {e}')
    print('\n尝试加载枫瑞路店...')
    result = dsm.load_from_database(store_name='惠宜选超市（苏州枫瑞路店）')
    print('⚠️ 使用枫瑞路店数据替代')

if isinstance(result, dict):
    df_full = result['full']
    df_display = result['display']
else:
    df_full = result
    df_display = result[result['一级分类名'] != '耗材'].copy() if '一级分类名' in result.columns else result.copy()

print(f'完整数据: {len(df_full):,}行, 展示数据: {len(df_display):,}行, 耗材: {len(df_full)-len(df_display):,}行')
profit_cols = [c for c in df_full.columns if '利润' in c]
print(f'\n利润相关字段: {profit_cols}')

# 方法1: 直接sum
if '利润额' in df_full.columns:
    profit1 = df_full['利润额'].sum()
    print(f'\n方法1-直接sum利润额: ¥{profit1:,.2f}')

# 方法2: 按订单聚合
if '订单ID' in df_full.columns and '利润额' in df_full.columns:
    order_profit = df_full.groupby('订单ID')['利润额'].first().sum()
    print(f'方法2-按订单聚合: ¥{order_profit:,.2f}')
    print(f'  订单数: {df_full["订单ID"].nunique():,}')

# 分渠道
if '渠道' in df_full.columns and '订单ID' in df_full.columns:
    order_df = df_full.groupby('订单ID').agg({'渠道': 'first', '利润额': 'first'}).reset_index()
    print(f'\n分渠道利润:')
    for ch, p in order_df.groupby('渠道')['利润额'].sum().items():
        print(f'  {ch}: ¥{p:,.2f}')
    print(f'  合计: ¥{order_df["利润额"].sum():,.2f}')

print(f'\n用户数据: 总利润¥23,332, 美团¥15,066, 饿了么¥6,826, 京东¥1,439, 合计¥{15066+6826+1439:,}')
