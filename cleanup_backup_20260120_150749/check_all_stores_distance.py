# -*- coding: utf-8 -*-
"""检查所有门店的配送距离数据"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func, distinct, case
import pandas as pd

session = SessionLocal()
try:
    print("所有门店配送距离统计:")
    print("=" * 80)
    
    # 简化查询
    results = session.query(
        Order.store_name,
        func.count(Order.id).label('row_count'),
        func.count(distinct(Order.order_id)).label('order_count'),
        func.avg(Order.delivery_distance).label('avg_distance'),
        func.max(Order.delivery_distance).label('max_distance'),
    ).group_by(Order.store_name).all()
    
    for r in results:
        avg_dist = r.avg_distance if r.avg_distance else 0
        max_dist = r.max_distance if r.max_distance else 0
        print(f"\n{r.store_name}:")
        print(f"  数据行数: {r.row_count}")
        print(f"  订单数: {r.order_count}")
        print(f"  平均配送距离: {avg_dist:.2f} 米")
        print(f"  最大配送距离: {max_dist:.2f} 米")
        
        # 检查有多少订单有配送距离
        has_dist = session.query(func.count(distinct(Order.order_id))).filter(
            Order.store_name == r.store_name,
            Order.delivery_distance > 0
        ).scalar()
        print(f"  有配送距离的订单: {has_dist}")
        
finally:
    session.close()
