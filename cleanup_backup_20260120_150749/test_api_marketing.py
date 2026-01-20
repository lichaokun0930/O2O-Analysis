#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API中商家活动成本的计算逻辑
"""
import sys
import io
import pandas as pd
from pathlib import Path

# 解决Windows编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 模拟API中的calculate_order_metrics函数
def calculate_order_metrics(df):
    if df.empty or '订单ID' not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df['订单ID'] = df['订单ID'].astype(str)
    
    cost_field = '商品采购成本' if '商品采购成本' in df.columns else '成本'
    sales_field = '月售' if '月售' in df.columns else '销量'
    
    df['物流配送费'] = df['物流配送费'].fillna(0)
    df['配送费减免金额'] = df['配送费减免金额'].fillna(0)
    df['用户支付配送费'] = df['用户支付配送费'].fillna(0)
    
    if '实收价格' in df.columns and sales_field in df.columns:
        df['订单总收入'] = df['实收价格'] * df[sales_field]
    
    agg_dict = {
        '商品实售价': 'sum',
        '预计订单收入': 'sum',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '物流配送费': 'first',
        '平台佣金': 'first',
    }
    
    if sales_field in df.columns:
        agg_dict[sales_field] = 'sum'
    if '平台服务费' in df.columns:
        agg_dict['平台服务费'] = 'sum'
    if '订单总收入' in df.columns:
        agg_dict['订单总收入'] = 'sum'
    if '利润额' in df.columns:
        agg_dict['利润额'] = 'sum'
    if '企客后返' in df.columns:
        agg_dict['企客后返'] = 'sum'
    if cost_field in df.columns:
        agg_dict[cost_field] = 'sum'
    
    # 订单级字段用first
    for field in ['满减金额', '商品减免金额', '新客减免金额', '渠道', '门店名称', '日期', 
                  '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠']:
        if field in df.columns:
            agg_dict[field] = 'first'
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    
    if '订单总收入' in order_agg.columns:
        order_agg['实收价格'] = order_agg['订单总收入']
    
    if cost_field == '成本' and cost_field in order_agg.columns:
        order_agg['商品采购成本'] = order_agg['成本']
    
    if '平台服务费' not in order_agg.columns:
        order_agg['平台服务费'] = 0
    order_agg['平台服务费'] = order_agg['平台服务费'].fillna(0)
    
    if '企客后返' not in order_agg.columns:
        order_agg['企客后返'] = 0
    order_agg['企客后返'] = order_agg['企客后返'].fillna(0)
    
    if '平台佣金' not in order_agg.columns:
        order_agg['平台佣金'] = order_agg['平台服务费']
    order_agg['平台佣金'] = order_agg['平台佣金'].fillna(0)
    
    if '利润额' not in order_agg.columns:
        order_agg['利润额'] = 0
    order_agg['利润额'] = order_agg['利润额'].fillna(0)
    
    order_agg['订单实际利润'] = (
        order_agg['利润额'] -
        order_agg['平台服务费'] -
        order_agg['物流配送费'] +
        order_agg['企客后返']
    )
    
    order_agg['配送净成本'] = (
        order_agg['物流配送费'] -
        (order_agg['用户支付配送费'] - order_agg['配送费减免金额']) -
        order_agg['企客后返']
    )
    
    # 计算商家活动成本 (v3.1更新：包含全部8个营销字段)
    marketing_fields = ['配送费减免金额', '满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
    order_agg['商家活动成本'] = 0
    for field in marketing_fields:
        if field in order_agg.columns:
            field_sum = order_agg[field].fillna(0).sum()
            order_agg['商家活动成本'] += order_agg[field].fillna(0)
            print(f"  {field}: {field_sum:.2f}")
    print(f"  商家活动成本总计: {order_agg['商家活动成本'].sum():.2f}")
    
    # 过滤异常订单
    PLATFORM_FEE_CHANNELS = ['饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店']
    if '渠道' in order_agg.columns:
        is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
        is_zero_fee = order_agg['平台服务费'] <= 0
        invalid_orders = is_fee_channel & is_zero_fee
        print(f"  过滤异常订单: {invalid_orders.sum()} 单")
        order_agg = order_agg[~invalid_orders].copy()
    
    return order_agg


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
print("\n计算订单指标:")
order_agg = calculate_order_metrics(df)
print(f"\n订单聚合后: {len(order_agg)} 订单")

# 按渠道统计
channel_stats = order_agg.groupby('渠道').agg({
    '订单ID': 'count',
    '商家活动成本': 'sum',
}).reset_index()

print("\n按渠道统计商家活动成本:")
for _, row in channel_stats.iterrows():
    print(f"  {row['渠道']}: {row['商家活动成本']:.2f} ({row['订单ID']}单)")

print(f"\n总计: {channel_stats['商家活动成本'].sum():.2f}")
