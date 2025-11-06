# -*- coding: utf-8 -*-
import os
import sys

# 强制设置编码
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['PYTHONIOENCODING'] = 'utf-8'

print("Testing database connection...")

try:
    from sqlalchemy import create_engine, text
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # 使用SQLAlchemy绕过psycopg2的编码问题
    database_url = "postgresql+psycopg2://postgres:postgres@localhost:5432/o2o_dashboard"
    
    engine = create_engine(
        database_url,
        connect_args={'client_encoding': 'utf8'},
        pool_pre_ping=True
    )
    
    print("Engine created successfully")
    
    with engine.connect() as conn:
        # 测试查询
        result = conn.execute(text("SELECT current_database(), version()"))
        db_name, version = result.fetchone()
        
        print(f"Database: {db_name}")
        print(f"Version: {version[:50]}")
        
        # 查询订单数
        result = conn.execute(text("SELECT COUNT(*) FROM orders"))
        count = result.scalar()
        
        print(f"Orders count: {count}")
        
        if count > 0:
            print("\n**YES! Database has data!**")
            
            # 查看最新的几条记录
            result = conn.execute(text("""
                SELECT order_id, product_name, order_date 
                FROM orders 
                ORDER BY order_date DESC 
                LIMIT 5
            """))
            
            print("\nLatest 5 orders:")
            for row in result:
                print(f"  - {row[0]}: {row[1]} ({row[2]})")
        else:
            print("\nDatabase is empty - needs migration")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
