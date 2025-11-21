# -*- coding: utf-8 -*-
"""检查数据库表数据"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database.connection import SessionLocal
from database.models import Product, Order

session = SessionLocal()

print("="*80)
print("检查数据库表")
print("="*80)

# 检查Product表
product_count = session.query(Product).count()
print(f"\nProduct表记录数: {product_count:,}")

if product_count > 0:
    # 检查库存字段
    products_with_stock = session.query(Product).filter(Product.stock > 0).count()
    print(f"有库存的商品: {products_with_stock:,}/{product_count:,}")
    
    # 检查成本字段
    products_with_cost = session.query(Product).filter(Product.current_cost > 0).count()
    print(f"有成本的商品: {products_with_cost:,}/{product_count:,}")
    
    # 显示前10个商品
    products = session.query(Product).limit(10).all()
    print(f"\n前10个商品:")
    for p in products:
        print(f"  {p.product_name[:30]}: 库存={p.stock}, 成本={p.current_cost:.2f}, 售价={p.current_price:.2f}")
else:
    print("❌ Product表为空")

# 检查Order表中的cost
print("\n" + "="*80)
print("检查Order表")
print("="*80)

order_count = session.query(Order).count()
print(f"\nOrder表记录数: {order_count:,}")

if order_count > 0:
    # 检查成本字段
    orders_with_cost = session.query(Order).filter(Order.cost > 0).count()
    print(f"有成本的订单: {orders_with_cost:,}/{order_count:,}")
    
    # 显示前5个订单的成本
    orders = session.query(Order).limit(5).all()
    print(f"\n前5个订单:")
    for o in orders:
        print(f"  订单{o.order_id}: 成本={o.cost:.2f}, 商品={o.product_name[:30]}")

session.close()
print("\n" + "="*80)
print("✅ 检查完成")
print("="*80)
