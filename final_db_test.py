# -*- coding: utf-8 -*-
"""终极数据库测试 - 使用psycopg2二进制模式"""

import os
import sys

# 强制UTF-8
os.environ['PGCLIENTENCODING'] = 'UTF8'

try:
    # 尝试使用 psycopg2-binary
    import psycopg2
    import psycopg2.extensions
    
    print("Attempting connection with binary mode...")
    
    # 方法：直接使用DSN字符串，避免参数解析
    dsn = "host=localhost port=5432 dbname=o2o_dashboard user=postgres password=postgres client_encoding=UTF8"
    
    conn = psycopg2.connect(dsn)
    
    print("SUCCESS! Connected to database")
    
    # 设置自动提交
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    
    cur = conn.cursor()
    
    # 检查订单数
    cur.execute("SELECT COUNT(*) FROM orders")
    count = cur.fetchone()[0]
    
    print(f"\n订单总数: {count:,} 条")
    
    if count > 0:
        print("\n✅✅✅ 数据库有数据！100%可以恢复！ ✅✅✅\n")
        
        # 获取更多信息
        cur.execute("""
            SELECT 
                MIN(order_date) as first_order,
                MAX(order_date) as last_order,
                COUNT(DISTINCT store_name) as store_count
            FROM orders
        """)
        
        first, last, stores = cur.fetchone()
        print(f"数据时间范围: {first} ~ {last}")
        print(f"门店数量: {stores}")
        
        # 查看表结构
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'orders'
            ORDER BY ordinal_position
            LIMIT 10
        """)
        
        print("\n表结构 (前10列):")
        for col_name, col_type in cur.fetchall():
            print(f"  - {col_name}: {col_type}")
    else:
        print("\n数据库是空的，需要导入数据")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"\nError: {e}")
    print(f"Type: {type(e).__name__}")
    
    # 最后的尝试：检查是否是密码问题
    if "authentication" in str(e).lower():
        print("\n可能是密码错误！")
        print("请确认PostgreSQL密码是否为 'postgres'")
