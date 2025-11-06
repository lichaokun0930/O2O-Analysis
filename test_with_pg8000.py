# -*- coding: utf-8 -*-
"""使用pg8000驱动测试数据库（纯Python，无C扩展）"""

try:
    import pg8000.native
    
    print("使用 pg8000 (纯Python驱动) 连接数据库...")
    
    conn = pg8000.native.Connection(
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432,
        database="o2o_dashboard"
    )
    
    print("✅ 连接成功！")
    
    # 查询订单数
    result = conn.run("SELECT COUNT(*) FROM orders")
    count = result[0][0]
    
    print(f"\n📊 订单总数: {count:,} 条")
    
    if count > 0:
        print("\n" + "=" * 60)
        print("✅✅✅ 数据库有数据！100%可以恢复！ ✅✅✅")
        print("=" * 60)
        
        # 获取数据范围
        result = conn.run("""
            SELECT 
                MIN(order_date)::text as first_order,
                MAX(order_date)::text as last_order,
                COUNT(DISTINCT store_name) as store_count,
                COUNT(DISTINCT product_name) as product_count
            FROM orders
        """)
        
        first, last, stores, products = result[0]
        print(f"\n📅 数据时间范围: {first} ~ {last}")
        print(f"🏪 门店数量: {stores}")
        print(f"📦 商品数量: {products}")
        
        # 查看表结构
        result = conn.run("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'orders'
            ORDER BY ordinal_position
        """)
        
        print(f"\n📋 表结构 ({len(result)} 列):")
        for i, (col_name, col_type) in enumerate(result[:15], 1):
            print(f"  {i:2d}. {col_name}: {col_type}")
        
        if len(result) > 15:
            print(f"  ... 还有 {len(result) - 15} 列")
        
        # 抽样查看几条数据
        result = conn.run("""
            SELECT order_id, store_name, product_name, order_date::text
            FROM orders 
            ORDER BY order_date DESC 
            LIMIT 3
        """)
        
        print(f"\n📌 最新3条订单示例:")
        for order_id, store, product, date in result:
            print(f"  - {order_id}: {store} | {product} | {date}")
    
    else:
        print("\n⚠️ 数据库表存在但是空的，需要导入数据")
    
    conn.close()
    print("\n✅ 数据库状态检查完成！")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
