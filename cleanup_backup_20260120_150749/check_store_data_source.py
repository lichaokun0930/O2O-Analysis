# -*- coding: utf-8 -*-
"""检查门店数据来源和配送距离字段"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func, distinct
import pandas as pd

STORE_NAME = "厉臣便利（镇江平昌路店）"

session = SessionLocal()
try:
    # 1. 检查该门店的数据
    print(f"🏪 门店: {STORE_NAME}")
    print("=" * 60)
    
    # 查询该门店的订单样本
    orders = session.query(Order).filter(
        Order.store_name == STORE_NAME
    ).limit(5).all()
    
    print(f"\n订单样本（前5条）:")
    for o in orders:
        print(f"  订单ID: {o.order_id}")
        print(f"    配送距离: {o.delivery_distance}")
        print(f"    渠道: {o.channel}")
        print(f"    日期: {o.date}")
        print()
    
    # 2. 检查所有门店的配送距离情况
    print("\n所有门店配送距离统计:")
    print("-" * 60)
    
    store_stats = session.query(
        Order.store_name,
        func.count(distinct(Order.order_id)).label('order_count'),
        func.avg(Order.delivery_distance).label('avg_distance'),
        func.sum(func.cast(Order.delivery_distance > 0, type_=int)).label('has_distance')
    ).group_by(Order.store_name).all()
    
    for s in store_stats:
        print(f"{s.store_name}:")
        print(f"  订单数: {s.order_count}, 平均距离: {s.avg_distance:.2f if s.avg_distance else 0}, 有距离数据: {s.has_distance}")
        
finally:
    session.close()
