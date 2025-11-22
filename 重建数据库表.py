#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重建数据库表结构（移除order_id的unique约束）
"""

from database.connection import engine, SessionLocal
from database.models import Base, Order
from sqlalchemy import text

print("=" * 70)
print("🔧 重建数据库表结构")
print("=" * 70)

# 1. 删除旧表
print("\n1️⃣ 删除旧的orders表...")
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS orders CASCADE"))
print("   ✅ 删除成功")

# 2. 创建新表（没有unique约束）
print("\n2️⃣ 创建新的orders表（允许order_id重复）...")
Base.metadata.create_all(engine, tables=[Order.__table__])
print("   ✅ 创建成功")

# 3. 验证表结构
print("\n3️⃣ 验证表结构...")
session = SessionLocal()
try:
    with engine.begin() as conn:
        # 检查约束
        result = conn.execute(text("""
            SELECT conname, contype 
            FROM pg_constraint 
            WHERE conrelid = 'orders'::regclass
        """))
        constraints = result.fetchall()
        
        print("   当前约束:")
        for name, type_ in constraints:
            constraint_type = {
                'p': '主键(PRIMARY KEY)',
                'u': '唯一(UNIQUE)',
                'f': '外键(FOREIGN KEY)',
                'c': '检查(CHECK)'
            }.get(type_, type_)
            print(f"   - {name}: {constraint_type}")
        
        # 检查是否还有order_id的unique约束
        unique_on_order_id = any('order_id' in name.lower() and type_ == 'u' for name, type_ in constraints)
        
        if unique_on_order_id:
            print("\n   ❌ 警告: order_id仍有unique约束!")
        else:
            print("\n   ✅ order_id没有unique约束，可以存储同一订单的多个商品")
            
finally:
    session.close()

print("\n" + "=" * 70)
print("✅ 数据库表结构重建完成")
print("=" * 70)
print("\n现在可以重新导入数据了！")
