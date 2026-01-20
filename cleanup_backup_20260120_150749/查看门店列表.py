# -*- coding: utf-8 -*-
"""查看数据库中的门店列表"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import distinct

session = SessionLocal()
try:
    stores = session.query(distinct(Order.store_name)).all()
    print("数据库中的门店列表:")
    for i, (store,) in enumerate(sorted(stores), 1):
        print(f"  {i}. {store}")
finally:
    session.close()
