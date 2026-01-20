# -*- coding: utf-8 -*-
"""查看数据库中的日期范围"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func

session = SessionLocal()
try:
    result = session.query(
        func.min(Order.date),
        func.max(Order.date),
        func.count(Order.id)
    ).first()
    
    min_date, max_date, count = result
    print(f"数据日期范围: {min_date} ~ {max_date}")
    print(f"总记录数: {count:,}")
    
    # 查看沛县店的日期范围
    result2 = session.query(
        func.min(Order.date),
        func.max(Order.date),
        func.count(Order.id)
    ).filter(Order.store_name == "惠宜选-徐州沛县店").first()
    
    min_date2, max_date2, count2 = result2
    print(f"\n沛县店数据日期范围: {min_date2} ~ {max_date2}")
    print(f"沛县店记录数: {count2:,}")
    
finally:
    session.close()
