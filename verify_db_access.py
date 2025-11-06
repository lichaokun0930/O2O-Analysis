# -*- coding: utf-8 -*-
"""使用正确密码测试数据库连接"""

import pg8000.native

password = "308352588"

try:
    print("正在连接数据库...")
    
    conn = pg8000.native.Connection(
        user="postgres",
        password=password,
        host="localhost",
        port=5432,
        database="o2o_dashboard"
    )
    
    print("\n" + "=" * 60)
    print("✅✅✅ 连接成功！数据库可以访问！ ✅✅✅")
    print("=" * 60)
    
    # 查询订单数
    result = conn.run("SELECT COUNT(*) FROM orders")
    count = result[0][0]
    
    print(f"\n📊 订单总数: {count:,} 条")
    
    if count > 0:
        print("\n🎉🎉🎉 数据库有数据！100%可以恢复！ 🎉🎉🎉\n")
        
        # 获取详细信息
        result = conn.run("""
            SELECT 
                MIN(order_date)::text as first_date,
                MAX(order_date)::text as last_date,
                COUNT(DISTINCT store_name) as stores,
                COUNT(DISTINCT product_name) as products
            FROM orders
        """)
        
        first, last, stores, products = result[0]
        
        print("数据详情:")
        print(f"  📅 时间范围: {first} ~ {last}")
        print(f"  🏪 门店数量: {stores}")
        print(f"  📦 商品种类: {products}")
        
        # 查看最新订单
        result = conn.run("""
            SELECT order_id, store_name, product_name, 
                   order_date::text, total_amount
            FROM orders 
            ORDER BY order_date DESC 
            LIMIT 5
        """)
        
        print(f"\n📌 最新5条订单:")
        for order_id, store, product, date, amount in result:
            print(f"  - {order_id}: {store} | {product} | {date} | ¥{amount}")
        
        print("\n" + "=" * 60)
        print("下一步：更新 .env 文件中的密码配置")
        print("=" * 60)
        
    else:
        print("\n⚠️  数据库表存在但是空的")
        print("需要运行数据导入脚本")
    
    conn.close()
    
except Exception as e:
    print(f"\n❌ 连接失败: {e}")
    import traceback
    traceback.print_exc()
