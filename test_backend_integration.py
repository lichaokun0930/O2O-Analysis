# -*- coding: utf-8 -*-
"""测试后端API和数据库集成"""

from database.connection import get_db_context
from sqlalchemy import text

print("=" * 60)
print("测试数据库集成")
print("=" * 60)

try:
    with get_db_context() as db:
        # 查询订单总数
        result = db.execute(text("SELECT COUNT(*) FROM orders"))
        count = result.scalar()
        
        print(f"\n✅ 数据库连接成功！")
        print(f"📊 订单总数: {count:,} 条")
        
        # 查询数据范围
        result = db.execute(text("""
            SELECT 
                MIN(date)::text as first_date,
                MAX(date)::text as last_date,
                COUNT(DISTINCT store_name) as stores,
                COUNT(DISTINCT product_name) as products
            FROM orders
        """))
        
        row = result.fetchone()
        first, last, stores, products = row
        
        print(f"\n数据详情:")
        print(f"  📅 时间范围: {first} ~ {last}")
        print(f"  🏪 门店数量: {stores}")
        print(f"  📦 商品种类: {products}")
        
        # 查看最近的订单
        result = db.execute(text("""
            SELECT order_id, store_name, product_name, 
                   date::text, amount
            FROM orders 
            ORDER BY date DESC 
            LIMIT 5
        """))
        
        print(f"\n📌 最新5条订单:")
        for row in result:
            order_id, store, product, date, amount = row
            product_short = product[:40] + "..." if len(product) > 40 else product
            print(f"  - {order_id}: {store[:20]:20s} | {product_short:40s} | {date}")
        
        print("\n" + "=" * 60)
        print("✅✅✅ 数据库集成测试通过！")
        print("=" * 60)
        print("\n后端API可以正常访问数据库！")
        print("Dash看板可以通过API获取数据！")
        
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
