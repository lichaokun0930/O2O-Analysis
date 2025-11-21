# -*- coding: utf-8 -*-
"""诊断环比计算问题"""
import pandas as pd
from datetime import datetime, date
from database.models import Order
from database.connection import get_db

db = next(get_db())

store_name = '共橙超市-南通海安店'
print(f"门店: {store_name}")

# 查询数据
orders = db.query(Order).filter(Order.store_name == store_name).all()

if not orders:
    print("❌ 没有数据!")
    db.close()
    exit(1)

# 转换为DataFrame
data = []
for order in orders:
    data.append({
        '订单ID': order.order_id,
        '日期': order.date,
        '渠道': getattr(order, 'channel', None) or '未知',
    })

df = pd.DataFrame(data)
print(f"\n1. 数据量: {len(df)} 行")

# 检查日期字段
if '日期' in df.columns:
    print(f"✅ '日期' 字段存在")
    df['日期'] = pd.to_datetime(df['日期'])
    print(f"   日期范围: {df['日期'].min().date()} ~ {df['日期'].max().date()}")
else:
    print(f"❌ '日期' 字段不存在!")
    print(f"   列名: {df.columns.tolist()}")

# 检查渠道字段
if '渠道' in df.columns:
    print(f"\n2. ✅ '渠道' 字段存在")
    print(f"   渠道列表: {df['渠道'].unique().tolist()}")
    
    # 过滤特殊渠道
    excluded = ['收银机订单', '闪购小程序']
    df_filtered = df[~df['渠道'].isin(excluded)]
    print(f"   过滤后数据: {len(df_filtered)} 行")
    print(f"   过滤后渠道: {df_filtered['渠道'].unique().tolist()}")
else:
    print(f"\n2. ❌ '渠道' 字段不存在!")

# 模拟环比计算条件判断
print(f"\n3. 环比计算条件检查:")
GLOBAL_FULL_DATA = df  # 模拟全局数据
cache_valid = False  # 模拟缓存失效

condition1 = not cache_valid
condition2 = '日期' in df.columns
condition3 = GLOBAL_FULL_DATA is not None
condition4 = len(GLOBAL_FULL_DATA) > 0

print(f"   cache_valid = False: {condition1}")
print(f"   '日期' in df.columns: {condition2}")
print(f"   GLOBAL_FULL_DATA is not None: {condition3}")
print(f"   len(GLOBAL_FULL_DATA) > 0: {condition4}")

if condition1 and condition2 and condition3:
    print(f"\n✅ 环比计算条件满足,会执行计算!")
    
    # 测试日期范围获取
    df_dates = pd.to_datetime(df['日期'])
    actual_start = df_dates.min()
    actual_end = df_dates.max()
    print(f"   日期范围: {actual_start.date()} ~ {actual_end.date()}")
    
    # 计算上期日期
    from datetime import timedelta
    period_days = (actual_end - actual_start).days + 1
    prev_end_date = actual_start - timedelta(days=1)
    prev_start_date = prev_end_date - timedelta(days=period_days - 1)
    
    print(f"   当前周期: {actual_start.date()} ~ {actual_end.date()} ({period_days}天)")
    print(f"   上期周期: {prev_start_date.date()} ~ {prev_end_date.date()} ({period_days}天)")
    
    # 检查上期是否有数据
    prev_data = df[
        (df['日期'].dt.date >= prev_start_date.date()) & 
        (df['日期'].dt.date <= prev_end_date.date())
    ]
    print(f"   上期数据: {len(prev_data)} 行")
    
    if len(prev_data) > 0:
        print(f"   ✅ 上期有数据,可以计算环比")
    else:
        print(f"   ❌ 上期无数据,无法计算环比")
else:
    print(f"\n❌ 环比计算条件不满足,不会执行!")

db.close()
