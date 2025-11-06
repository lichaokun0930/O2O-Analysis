#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""简单的数据库连接测试"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    # 直接使用 psycopg2 连接
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="o2o_dashboard",
        user="postgres",
        password="postgres"
    )
    
    print("✅ 数据库连接成功！")
    
    # 创建游标
    cur = conn.cursor()
    
    # 查询数据库版本
    cur.execute("SELECT version()")
    version = cur.fetchone()[0]
    print(f"PostgreSQL 版本: {version.split(',')[0]}")
    
    # 查询表列表
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    tables = cur.fetchall()
    print(f"\n数据库表 ({len(tables)}个):")
    for table in tables:
        # 查询每个表的记录数
        cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cur.fetchone()[0]
        print(f"  - {table[0]}: {count:,} 条记录")
    
    # 关闭连接
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ 连接失败: {e}")
    print("\n请检查:")
    print("  1. PostgreSQL 是否在运行")
    print("  2. 数据库 'o2o_dashboard' 是否存在")
    print("  3. 密码是否正确")
