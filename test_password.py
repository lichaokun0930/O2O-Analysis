# -*- coding: utf-8 -*-
"""交互式数据库密码测试"""

import getpass
import pg8000.native

print("=" * 60)
print("PostgreSQL 数据库密码测试")
print("=" * 60)
print("\n请输入您的 PostgreSQL 密码")
print("(如果不记得，可以通过 pgAdmin 或重置密码)")
print()

password = getpass.getpass("postgres 用户密码: ")

try:
    conn = pg8000.native.Connection(
        user="postgres",
        password=password,
        host="localhost",
        port=5432,
        database="o2o_dashboard"
    )
    
    print("\n✅✅✅ 密码正确！连接成功！ ✅✅✅\n")
    
    # 查询订单数
    result = conn.run("SELECT COUNT(*) FROM orders")
    count = result[0][0]
    
    print(f"订单总数: {count:,} 条\n")
    
    if count > 0:
        print("=" * 60)
        print("数据库有数据！")
        print("=" * 60)
        
        # 获取详细信息
        result = conn.run("""
            SELECT 
                MIN(order_date)::text,
                MAX(order_date)::text,
                COUNT(DISTINCT store_name),
                COUNT(DISTINCT product_name)
            FROM orders
        """)
        
        first, last, stores, products = result[0]
        print(f"\n数据范围: {first} ~ {last}")
        print(f"门店数: {stores}")
        print(f"商品数: {products}")
        
        # 保存正确的密码到.env
        print("\n" + "=" * 60)
        print("发现正确密码！")
        print("=" * 60)
        print(f"\n请手动更新 .env 文件中的密码:")
        print(f"DATABASE_URL=postgresql://postgres:{password}@localhost:5432/o2o_dashboard")
        
    conn.close()
    
except Exception as e:
    print(f"\n❌ 连接失败: {e}")
    if "28P01" in str(e) or "auth" in str(e).lower():
        print("\n密码错误！请重试或重置PostgreSQL密码")
    else:
        print("\n其他错误，请检查PostgreSQL是否正在运行")
