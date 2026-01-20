#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

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

# 订单级聚合
df['订单ID'] = df['订单ID'].astype(str)

agg_dict = {
    '渠道': 'first',
    '平台服务费': 'sum',
}

# 商家活动成本相关字段 (v3.1更新：包含全部8个营销字段)
for field in ['配送费减免金额', '满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']:
    if field in df.columns:
        agg_dict[field] = 'first'

order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()

# 过滤异常订单
PLATFORM_FEE_CHANNELS = ['饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店']
if '平台服务费' not in order_agg.columns:
    order_agg['平台服务费'] = 0
order_agg['平台服务费'] = order_agg['平台服务费'].fillna(0)

is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
is_zero_fee = order_agg['平台服务费'] <= 0
invalid_orders = is_fee_channel & is_zero_fee
print(f"过滤异常订单: {invalid_orders.sum()} 单")
order_agg = order_agg[~invalid_orders].copy()

# 计算商家活动成本 (v3.1更新：包含全部8个营销字段)
marketing_fields = ['配送费减免金额', '满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
order_agg['商家活动成本'] = 0
for field in marketing_fields:
    if field in order_agg.columns:
        order_agg['商家活动成本'] += order_agg[field].fillna(0)

# 按渠道统计
channel_stats = order_agg.groupby('渠道').agg({
    '订单ID': 'count',
    '商家活动成本': 'sum',
    '满减金额': 'sum',
    '商品减免金额': 'sum',
    '商家代金券': 'sum',
    '商家承担部分券': 'sum',
    '满赠金额': 'sum',
    '商家其他优惠': 'sum',
}).reset_index()

print("\n按渠道统计商家活动成本:")
print("-" * 80)
for _, row in channel_stats.iterrows():
    print(f"\n{row['渠道']} ({row['订单ID']}单):")
    print(f"  商家活动成本: {row['商家活动成本']:.2f}")
    print(f"    满减金额: {row['满减金额']:.2f}")
    print(f"    商品减免金额: {row['商品减免金额']:.2f}")
    print(f"    商家代金券: {row['商家代金券']:.2f}")
    print(f"    商家承担部分券: {row['商家承担部分券']:.2f}")
    print(f"    满赠金额: {row['满赠金额']:.2f}")
    print(f"    商家其他优惠: {row['商家其他优惠']:.2f}")

print(f"\n总计: {channel_stats['商家活动成本'].sum():.2f}")
