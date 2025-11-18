# -*- coding: utf-8 -*-
"""数据库数据诊断脚本 - 检查门店数据范围"""

import sys
sys.path.insert(0, '.')

from database.models import Order, Product, Base
from database.connection import get_db
from sqlalchemy import func
import pandas as pd

print("="*80)
print("📊 数据库数据诊断")
print("="*80)

db = next(get_db())

try:
    # 1. 检查所有门店
    print("\n1️⃣ 数据库中的所有门店:")
    print("-"*60)
    stores = db.query(Order.store_name, func.count(Order.id)).group_by(Order.store_name).all()
    for store_name, count in stores:
        print(f"   {store_name}: {count:,} 条订单")
    
    # 2. 检查每个门店的日期范围
    print("\n2️⃣ 每个门店的日期范围:")
    print("-"*60)
    for store_name, _ in stores:
        date_range = db.query(
            func.min(Order.date).label('min_date'),
            func.max(Order.date).label('max_date'),
            func.count(func.distinct(func.date(Order.date))).label('days_count')
        ).filter(Order.store_name == store_name).first()
        
        print(f"\n   📍 {store_name}:")
        print(f"      最早日期: {date_range.min_date}")
        print(f"      最晚日期: {date_range.max_date}")
        print(f"      天数统计: {date_range.days_count} 天")
        
        # 检查每天的订单数
        daily_counts = db.query(
            func.date(Order.date).label('date'),
            func.count(Order.id).label('count')
        ).filter(Order.store_name == store_name).group_by(func.date(Order.date)).order_by(func.date(Order.date)).all()
        
        print(f"      每日订单数:")
        for date, count in daily_counts[:10]:  # 只显示前10天
            print(f"        {date}: {count:,} 条")
        if len(daily_counts) > 10:
            print(f"        ... (还有 {len(daily_counts)-10} 天)")
    
    # 3. 测试查询特定门店
    print("\n3️⃣ 测试查询'祥和路店':")
    print("-"*60)
    
    test_query = db.query(Order).filter(Order.store_name == '祥和路店')
    test_count = test_query.count()
    print(f"   匹配到 {test_count:,} 条记录")
    
    if test_count > 0:
        # 显示前5条
        print(f"   前5条记录:")
        for order in test_query.limit(5).all():
            print(f"      {order.date} - {order.product_name} - {order.quantity}件")
        
        # 日期分布
        dates = db.query(
            func.date(Order.date).label('date'),
            func.count(Order.id).label('count')
        ).filter(Order.store_name == '祥和路店').group_by(func.date(Order.date)).all()
        
        print(f"\n   日期分布 ({len(dates)} 天):")
        for date, count in dates:
            print(f"      {date}: {count:,} 条")
    
    # 4. 检查门店名称中的特殊字符
    print("\n4️⃣ 门店名称详细信息:")
    print("-"*60)
    for store_name, _ in stores:
        print(f"   名称: '{store_name}'")
        print(f"   长度: {len(store_name)} 字符")
        print(f"   repr: {repr(store_name)}")
        print(f"   编码: {store_name.encode('utf-8')}")
        print()

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

print("\n" + "="*80)
print("诊断完成")
print("="*80)
