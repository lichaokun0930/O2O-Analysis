#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查数据库中的门店名称
"""

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func

db = SessionLocal()

print("="*80)
print("📊 数据库门店统计")
print("="*80)

# 查询所有门店
stores = db.query(
    Order.store_name,
    func.count(Order.id).label('count')
).group_by(Order.store_name).all()

print(f"\n共有 {len(stores)} 个门店:")
for store, count in stores:
    print(f"  {store}: {count:,} 条记录")

# 查询美团共橙
print(f"\n{'='*80}")
print("📊 渠道统计")
print("="*80)

channels = db.query(
    Order.channel,
    func.count(Order.id).label('count')
).group_by(Order.channel).all()

for channel, count in channels:
    print(f"  {channel}: {count:,} 条记录")

# 检查耗材
print(f"\n{'='*80}")
print("📊 耗材统计")
print("="*80)

haocai_count = db.query(Order).filter(Order.category_level1 == '耗材').count()
print(f"耗材记录数: {haocai_count:,}")

if haocai_count > 0:
    # 耗材利润
    from sqlalchemy import func as sql_func
    haocai_profit = db.query(
        sql_func.sum(Order.profit)
    ).filter(Order.category_level1 == '耗材').scalar()
    
    print(f"耗材总利润: {haocai_profit:.2f if haocai_profit else 0:.2f}")

db.close()
