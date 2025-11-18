# -*- coding: utf-8 -*-
"""测试单日环比计算"""
import pandas as pd
from datetime import datetime, date, timedelta
from database.models import Order
from database.connection import get_db

db = next(get_db())

store_name = '共橙超市-南通海安店'
target_date = date(2025, 10, 31)

print(f"门店: {store_name}")
print(f"目标日期: {target_date}\n")

# 查询所有数据
orders = db.query(Order).filter(Order.store_name == store_name).all()
data = []
for order in orders:
    data.append({
        '订单ID': order.order_id,
        '日期': order.date,
        '渠道': getattr(order, 'channel', None) or '未知',
    })

df = pd.DataFrame(data)
df['日期'] = pd.to_datetime(df['日期'])

print(f"总数据: {len(df)} 行")
print(f"日期范围: {df['日期'].min().date()} ~ {df['日期'].max().date()}\n")

# 模拟单日查询(用户选择10月31日)
actual_start = datetime(2025, 10, 31, 0, 0, 0)
actual_end = datetime(2025, 10, 31, 23, 59, 59)

print(f"用户查询范围: {actual_start.date()} ~ {actual_end.date()}")

# 计算周期长度
period_days = (actual_end - actual_start).days + 1
print(f"周期长度: {period_days} 天")

# 计算上期
prev_end_date = actual_start - timedelta(days=1)
prev_start_date = prev_end_date - timedelta(days=period_days - 1)

print(f"上期范围: {prev_start_date.date()} ~ {prev_end_date.date()}\n")

# 筛选数据
current_data = df[
    (df['日期'].dt.date >= actual_start.date()) & 
    (df['日期'].dt.date <= actual_end.date())
]

prev_data = df[
    (df['日期'].dt.date >= prev_start_date.date()) & 
    (df['日期'].dt.date <= prev_end_date.date())
]

print(f"当期数据: {len(current_data)} 行")
print(f"上期数据: {len(prev_data)} 行\n")

if len(prev_data) > 0:
    print("✅ 上期有数据,可以计算环比!")
    
    # 测试渠道环比
    excluded = ['收银机订单', '闪购小程序']
    current_filtered = current_data[~current_data['渠道'].isin(excluded)]
    prev_filtered = prev_data[~prev_data['渠道'].isin(excluded)]
    
    print(f"\n当期渠道分布:")
    for channel, count in current_filtered['渠道'].value_counts().items():
        print(f"  {channel}: {count}单")
    
    print(f"\n上期渠道分布:")
    for channel, count in prev_filtered['渠道'].value_counts().items():
        print(f"  {channel}: {count}单")
    
    print(f"\n✅ 渠道环比可以计算!")
else:
    print("❌ 上期无数据,无法计算环比!")

db.close()
