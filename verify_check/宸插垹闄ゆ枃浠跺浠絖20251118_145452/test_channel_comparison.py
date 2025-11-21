# -*- coding: utf-8 -*-
"""测试渠道环比计算"""
import pandas as pd
from datetime import datetime, date
from database.models import Order
from database.connection import get_db
from sqlalchemy import cast, Date

db = next(get_db())

store_name = '共橙超市-南通海安店'
target_date = date(2025, 10, 31)

print(f"测试门店: {store_name}")
print(f"目标日期: {target_date}\n")

# 查询完整数据
orders = db.query(Order).filter(Order.store_name == store_name).all()

data = []
for order in orders:
    # 渠道字段可能叫channel,不是platform
    channel = getattr(order, 'channel', None) or getattr(order, 'platform', None) or '未知渠道'
    # 过滤特殊渠道
    if channel in ['收银机订单', '闪购小程序']:
        continue
    
    data.append({
        '订单ID': order.order_id,
        '日期': order.date,
        '渠道': channel,
        '商品实售价': order.amount or 0,
        '利润额': order.profit or 0,
        '物流配送费': order.delivery_fee or 0,
        '平台佣金': order.commission or 0,
        '新客减免金额': order.new_customer_discount or 0,
        '企客后返': order.corporate_rebate or 0,
    })

df = pd.DataFrame(data)
df['日期'] = pd.to_datetime(df['日期'])

print(f"总数据: {len(df)} 条")
print(f"日期范围: {df['日期'].min().date()} 到 {df['日期'].max().date()}")
print(f"渠道: {df['渠道'].unique().tolist()}\n")

# 10月31日数据
current_date = datetime(2025, 10, 31)
current_data = df[df['日期'].dt.date == current_date.date()].copy()

# 10月30日数据
prev_date = datetime(2025, 10, 30)
prev_data = df[df['日期'].dt.date == prev_date.date()].copy()

print(f"当前期(10-31): {len(current_data)} 条")
print(f"上期(10-30): {len(prev_data)} 条\n")

# 聚合函数
def agg_by_channel(data):
    """按渠道聚合"""
    # 先按订单聚合
    agg_dict = {
        '商品实售价': 'sum',
        '利润额': 'sum',
        '物流配送费': 'first',
        '平台佣金': 'first',
        '新客减免金额': 'first',
        '企客后返': 'sum',
        '渠道': 'first',
    }
    
    order_level = data.groupby('订单ID').agg(agg_dict).reset_index()
    
    # 计算订单实际利润(新公式)
    order_level['订单实际利润'] = (
        order_level['利润额'] - 
        order_level['物流配送费'] - 
        order_level['平台佣金'] - 
        order_level['新客减免金额'] + 
        order_level['企客后返']
    )
    
    # 按渠道聚合
    channel_metrics = order_level.groupby('渠道').agg({
        '订单ID': 'count',
        '商品实售价': 'sum',
        '订单实际利润': 'sum'
    }).reset_index()
    
    channel_metrics.columns = ['渠道', '订单数', '销售额', '总利润']
    channel_metrics['客单价'] = channel_metrics['销售额'] / channel_metrics['订单数']
    
    return channel_metrics

current_metrics = agg_by_channel(current_data)
prev_metrics = agg_by_channel(prev_data)

print("当前期渠道指标:")
for _, row in current_metrics.iterrows():
    print(f"  {row['渠道']}: {int(row['订单数'])}单, 销售额¥{row['销售额']:,.2f}, 利润¥{row['总利润']:,.2f}")

print(f"\n上期渠道指标:")
for _, row in prev_metrics.iterrows():
    print(f"  {row['渠道']}: {int(row['订单数'])}单, 销售额¥{row['销售额']:,.2f}, 利润¥{row['总利润']:,.2f}")

print(f"\n环比计算:")
for _, current_row in current_metrics.iterrows():
    channel_name = current_row['渠道']
    prev_row = prev_metrics[prev_metrics['渠道'] == channel_name]
    
    if len(prev_row) == 0:
        print(f"  {channel_name}: 无上期数据")
        continue
    
    prev_row = prev_row.iloc[0]
    
    order_change = ((current_row['订单数'] - prev_row['订单数']) / prev_row['订单数'] * 100) if prev_row['订单数'] > 0 else 0
    sales_change = ((current_row['销售额'] - prev_row['销售额']) / prev_row['销售额'] * 100) if prev_row['销售额'] > 0 else 0
    profit_change = ((current_row['总利润'] - prev_row['总利润']) / prev_row['总利润'] * 100) if prev_row['总利润'] != 0 else 0
    
    print(f"  {channel_name}:")
    print(f"    订单数: {int(current_row['订单数'])} vs {int(prev_row['订单数'])} ({order_change:+.1f}%)")
    print(f"    销售额: ¥{current_row['销售额']:,.0f} vs ¥{prev_row['销售额']:,.0f} ({sales_change:+.1f}%)")
    print(f"    总利润: ¥{current_row['总利润']:,.0f} vs ¥{prev_row['总利润']:,.0f} ({profit_change:+.1f}%)")

db.close()
