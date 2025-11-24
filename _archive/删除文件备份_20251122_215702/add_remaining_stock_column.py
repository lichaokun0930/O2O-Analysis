"""
添加remaining_stock字段到orders表
"""
from sqlalchemy import text
from database.connection import engine

print("=" * 80)
print("🔧 添加remaining_stock字段到orders表")
print("=" * 80)

try:
    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='orders' AND column_name='remaining_stock'
        """))
        
        if result.fetchone():
            print("✅ remaining_stock字段已存在，无需添加")
        else:
            # 添加字段 (PostgreSQL语法)
            conn.execute(text("""
                ALTER TABLE orders 
                ADD COLUMN remaining_stock FLOAT DEFAULT 0
            """))
            conn.execute(text("""
                COMMENT ON COLUMN orders.remaining_stock IS '剩余库存'
            """))
            conn.commit()
            print("✅ 成功添加remaining_stock字段")
            
        print("\n📊 验证字段:")
        result = conn.execute(text("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name='orders' 
            AND column_name IN ('quantity', 'remaining_stock', 'amount')
            ORDER BY ordinal_position
        """))
        
        for row in result:
            print(f"  {row[0]}: {row[1]} (默认值: {row[2]})")
            
except Exception as e:
    print(f"❌ 错误: {e}")
    
print("=" * 80)
