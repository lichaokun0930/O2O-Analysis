"""检查并迁移数据库"""
from database.connection import SessionLocal, engine
from sqlalchemy import text, inspect

print("="*80)
print("🔍 检查数据库字段")
print("="*80)

session = SessionLocal()

try:
    # 检查当前字段
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('orders')]
    
    print(f"\n当前 orders 表字段数: {len(columns)}")
    
    # 检查新字段
    new_fields = ['gift_amount', 'other_merchant_discount', 'new_customer_discount', 'corporate_rebate']
    missing_fields = [f for f in new_fields if f not in columns]
    
    if not missing_fields:
        print("✅ 所有新字段已存在，无需迁移")
        for field in new_fields:
            print(f"   - {field}")
    else:
        print(f"\n⚠️  发现 {len(missing_fields)} 个缺失字段:")
        for field in missing_fields:
            print(f"   - {field}")
        
        print("\n🔧 开始执行数据库迁移...")
        
        # 执行迁移
        migration_sqls = [
            "ALTER TABLE orders ADD COLUMN gift_amount REAL DEFAULT 0",
            "ALTER TABLE orders ADD COLUMN other_merchant_discount REAL DEFAULT 0",
            "ALTER TABLE orders ADD COLUMN new_customer_discount REAL DEFAULT 0",
            "ALTER TABLE orders ADD COLUMN corporate_rebate REAL DEFAULT 0"
        ]
        
        for sql in migration_sqls:
            field_name = sql.split('ADD COLUMN ')[1].split(' ')[0]
            if field_name in missing_fields:
                try:
                    session.execute(text(sql))
                    print(f"   ✅ 添加字段: {field_name}")
                except Exception as e:
                    print(f"   ❌ 添加字段失败 {field_name}: {e}")
        
        session.commit()
        print("\n✅ 数据库迁移完成！")
        
        # 验证
        print("\n🔍 验证迁移结果...")
        inspector = inspect(engine)
        columns_after = [col['name'] for col in inspector.get_columns('orders')]
        
        for field in new_fields:
            if field in columns_after:
                print(f"   ✅ {field}")
            else:
                print(f"   ❌ {field} - 未找到")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    session.rollback()
finally:
    session.close()

print("\n" + "="*80)
print("📊 数据库状态检查完成")
print("="*80)
