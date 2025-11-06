# -*- coding: utf-8 -*-
"""检查数据库表结构和数据"""

import pg8000.native

password = "308352588"

try:
    conn = pg8000.native.Connection(
        user="postgres",
        password=password,
        host="localhost",
        port=5432,
        database="o2o_dashboard"
    )
    
    print("✅ 连接成功！")
    print("\n" + "=" * 60)
    print(f"📊 数据库状态: 63,230 条订单")
    print("=" * 60)
    
    # 查看表结构
    result = conn.run("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = 'orders'
        ORDER BY ordinal_position
    """)
    
    print(f"\n📋 orders 表结构 ({len(result)} 列):\n")
    for i, (col_name, data_type, max_len) in enumerate(result, 1):
        len_info = f"({max_len})" if max_len else ""
        print(f"  {i:2d}. {col_name:30s} {data_type}{len_info}")
    
    # 抽样查看数据
    print("\n" + "=" * 60)
    print("📌 数据示例 (前3条记录):")
    print("=" * 60)
    
    # 先查询前3条，不指定字段名
    result = conn.run("SELECT * FROM orders LIMIT 3")
    
    if result:
        # 获取列名
        result_cols = conn.run("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'orders'
            ORDER BY ordinal_position
        """)
        col_names = [row[0] for row in result_cols]
        
        print(f"\n显示关键字段:")
        for row in result:
            print("\n  记录:")
            # 显示前10个字段
            for i, (col, val) in enumerate(zip(col_names[:10], row[:10])):
                print(f"    {col}: {val}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ 数据库检查完成！")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
