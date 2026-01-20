# -*- coding: utf-8 -*-
"""检查预聚合表结构"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from sqlalchemy import text

session = SessionLocal()
try:
    # 查看store_daily_summary表结构
    sql = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'store_daily_summary'
        ORDER BY ordinal_position
    """
    result = session.execute(text(sql))
    rows = result.fetchall()
    
    print("store_daily_summary 表结构:")
    print("-" * 40)
    for col_name, data_type in rows:
        print(f"  {col_name}: {data_type}")
        
finally:
    session.close()
