#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试数据库连接"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 60)
print("📊 数据库配置检查")
print("=" * 60)

# 检查环境变量
database_url = os.getenv('DATABASE_URL')
print(f"\n✅ DATABASE_URL: {database_url}")

# 测试数据库连接
try:
    from database.connection import engine
    from sqlalchemy import text
    
    print(f"\n✅ 数据库引擎创建成功")
    print(f"   URL: {engine.url}")
    
    # 测试连接
    with engine.connect() as conn:
        result = conn.execute(text('SELECT current_database(), version()'))
        db_name, version = result.fetchone()
        
        print(f"\n✅ 数据库连接成功！")
        print(f"   数据库名: {db_name}")
        print(f"   PostgreSQL版本: {version.split(',')[0]}")
        
        # 检查表
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result]
        print(f"\n✅ 数据库表列表 ({len(tables)}个):")
        for table in tables:
            print(f"   - {table}")
            
        # 检查订单数据
        result = conn.execute(text("SELECT COUNT(*) FROM orders"))
        order_count = result.scalar()
        print(f"\n✅ 订单数据: {order_count:,} 条记录")
        
except Exception as e:
    print(f"\n❌ 数据库连接失败！")
    print(f"   错误: {e}")
    print(f"\n💡 解决方案:")
    print(f"   1. 确保 PostgreSQL 正在运行")
    print(f"   2. 检查 .env 文件中的 DATABASE_URL 配置")
    print(f"   3. 运行: python create_database.py")

print("\n" + "=" * 60)
