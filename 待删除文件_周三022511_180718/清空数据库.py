# -*- coding: utf-8 -*-
"""清空数据库表"""
from database.connection import SessionLocal
from database.models import Order, Product

print("="*80)
print("清空数据库表")
print("="*80)

session = SessionLocal()

try:
    # 删除所有Order记录
    order_count = session.query(Order).delete()
    print(f"\n删除Order表记录: {order_count:,}条")
    
    # 删除所有Product记录
    product_count = session.query(Product).delete()
    print(f"删除Product表记录: {product_count:,}条")
    
    session.commit()
    print("\n✅ 数据库清空完成")
    
except Exception as e:
    session.rollback()
    print(f"\n❌ 清空失败: {e}")
    
finally:
    session.close()

print("="*80)
