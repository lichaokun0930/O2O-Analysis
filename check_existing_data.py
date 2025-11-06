#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查数据库现有数据"""

import psycopg2
from psycopg2 import sql

try:
    # 使用连接字符串方式，避免读取配置文件
    import os
    os.environ['PGCLIENTENCODING'] = 'UTF8'
    
    conn = psycopg2.connect(
        "dbname=o2o_dashboard user=postgres password=postgres host=localhost port=5432",
        options='-c client_encoding=UTF8'
    )
    
    print("=" * 70)
    print("📊 数据库现有数据检查")
    print("=" * 70)
    
    cur = conn.cursor()
    
    # 1. 检查数据库编码
    cur.execute("SHOW SERVER_ENCODING")
    encoding = cur.fetchone()[0]
    print(f"\n✅ 数据库编码: {encoding}")
    
    # 2. 查询所有表
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    tables = cur.fetchall()
    
    if not tables:
        print("\n⚠️  数据库中没有表！需要运行迁移脚本创建表结构。")
    else:
        print(f"\n✅ 找到 {len(tables)} 个表:")
        
        total_records = 0
        for table in tables:
            table_name = table[0]
            
            # 查询表结构
            cur.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            columns = cur.fetchall()
            
            # 查询记录数
            cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(table_name)
            ))
            count = cur.fetchone()[0]
            total_records += count
            
            print(f"\n  📋 {table_name}: {count:,} 条记录")
            print(f"     字段 ({len(columns)}个): {', '.join([c[0] for c in columns[:8]])}")
            if len(columns) > 8:
                print(f"     ... 还有 {len(columns)-8} 个字段")
            
            # 如果有数据，显示样例
            if count > 0:
                cur.execute(sql.SQL("SELECT * FROM {} LIMIT 3").format(
                    sql.Identifier(table_name)
                ))
                samples = cur.fetchall()
                print(f"     样例数据 (前3条):")
                for i, row in enumerate(samples, 1):
                    print(f"       {i}. {row[:5]}...")  # 只显示前5个字段
        
        print("\n" + "=" * 70)
        print(f"📊 总计: {total_records:,} 条记录")
        print("=" * 70)
        
        if total_records > 0:
            print("\n✅ 数据库中有数据！可以直接使用，无需重新导入。")
            print("\n💡 下一步:")
            print("   1. 测试 Dash 看板能否连接数据库")
            print("   2. 如果看板能正常显示数据，说明恢复成功")
        else:
            print("\n⚠️  表结构存在，但没有数据！")
            print("\n💡 下一步:")
            print("   1. 运行: python quick_migrate.py")
            print("   2. 或使用 Excel 数据导入")
    
    cur.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"\n❌ 数据库连接失败: {e}")
    print("\n💡 可能原因:")
    print("   1. 数据库 'o2o_dashboard' 不存在")
    print("   2. PostgreSQL 密码不正确")
    print("   3. PostgreSQL 服务未启动")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
