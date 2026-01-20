#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试order_agg中的字段
"""
import sys
import io
import pandas as pd
from pathlib import Path

# 解决Windows编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 加载数据
data_dir = Path('实际数据')
order_file = None
for f in data_dir.glob('*.xlsx'):
    if '订单' in f.name:
        order_file = f
        break

df = pd.read_excel(order_file)
df = df[df['门店名称'] == '共橙一站式超市（灵璧县新河路店）']

# 排除咖啡渠道
CHANNELS_TO_REMOVE = ['美团咖啡店', '饿了么咖啡店', '饿了么咖啡', '美团咖啡']
df = df[~df['渠道'].isin(CHANNELS_TO_REMOVE)]

print(f"原始数据: {len(df)} 行")
print(f"原始数据字段: {df.columns.tolist()}")

# 检查商家活动成本相关字段 (v3.1更新：包含全部8个营销字段)
marketing_fields = ['配送费减免金额', '满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
print("\n商家活动成本相关字段:")
for field in marketing_fields:
    if field in df.columns:
        print(f"  {field}: 存在, 非空值数={df[field].notna().sum()}, 总计={df[field].sum():.2f}")
    else:
        print(f"  {field}: 不存在")

# 模拟API的聚合逻辑
df['订单ID'] = df['订单ID'].astype(str)

agg_dict = {
    '渠道': 'first',
    '平台服务费': 'sum',
}

# 添加商家活动成本相关字段
for field in marketing_fields:
    if field in df.columns:
        agg_dict[field] = 'first'

print(f"\n聚合字典: {agg_dict}")

order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
print(f"\n聚合后字段: {order_agg.columns.tolist()}")
print(f"聚合后行数: {len(order_agg)}")

# 检查聚合后的字段值
print("\n聚合后商家活动成本相关字段:")
for field in marketing_fields:
    if field in order_agg.columns:
        print(f"  {field}: 非空值数={order_agg[field].notna().sum()}, 总计={order_agg[field].sum():.2f}")
    else:
        print(f"  {field}: 不存在")
