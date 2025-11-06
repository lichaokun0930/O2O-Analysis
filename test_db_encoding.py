#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""使用不同方法测试数据库连接"""

import os

print("=" * 60)
print("方法1: 使用环境变量设置编码")
print("=" * 60)

# 方法1: 设置环境变量
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['LANG'] = 'en_US.UTF-8'

try:
    import psycopg2
    
    # 使用参数明确指定编码
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="o2o_dashboard",
        user="postgres",
        password="postgres",
        client_encoding='UTF8'
    )
    
    print("✅ 连接成功！")
    
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM orders")
    count = cur.fetchone()[0]
    print(f"订单数据: {count:,} 条")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ 方法1失败: {e}")
    print(f"错误类型: {type(e).__name__}")
    
    # 方法2: 使用连接URI
    print("\n" + "=" * 60)
    print("方法2: 使用URI连接字符串")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/o2o_dashboard")
        print("✅ URI方式连接成功！")
        
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM orders")
        count = cur.fetchone()[0]
        print(f"订单数据: {count:,} 条")
        
        cur.close()
        conn.close()
        
    except Exception as e2:
        print(f"❌ 方法2也失败: {e2}")
        
        # 方法3: 使用SQLAlchemy
        print("\n" + "=" * 60)
        print("方法3: 使用SQLAlchemy")
        print("=" * 60)
        
        try:
            from sqlalchemy import create_engine, text
            
            # 创建引擎时明确指定编码
            engine = create_engine(
                "postgresql://postgres:postgres@localhost:5432/o2o_dashboard",
                connect_args={
                    'client_encoding': 'utf8',
                    'options': '-c client_encoding=utf8'
                },
                echo=False
            )
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM orders"))
                count = result.scalar()
                print(f"✅ SQLAlchemy连接成功！")
                print(f"订单数据: {count:,} 条")
                
        except Exception as e3:
            print(f"❌ 方法3也失败: {e3}")
            import traceback
            traceback.print_exc()
