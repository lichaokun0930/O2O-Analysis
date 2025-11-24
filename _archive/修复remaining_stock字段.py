"""
快速修复: 添加 remaining_stock 字段
解决错误: orders.remaining_stock 不存在
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db_connection
from sqlalchemy import text

def add_remaining_stock_field():
    """添加 remaining_stock 字段到 orders 表"""
    
    print("="*60)
    print("修复: 添加 remaining_stock 字段")
    print("="*60)
    
    sql = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'orders' 
            AND column_name = 'remaining_stock'
        ) THEN
            ALTER TABLE orders 
            ADD COLUMN remaining_stock FLOAT DEFAULT 0;
            
            COMMENT ON COLUMN orders.remaining_stock IS '剩余库存';
            
            RAISE NOTICE '✅ 已添加 remaining_stock 字段';
        ELSE
            RAISE NOTICE '✅ remaining_stock 字段已存在';
        END IF;
    END $$;
    """
    
    try:
        with get_db_connection() as session:
            session.execute(text(sql))
            session.commit()
            print("✅ 字段添加成功!")
            
            # 验证
            result = session.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'orders' 
                AND column_name = 'remaining_stock'
            """))
            
            row = result.fetchone()
            if row:
                print(f"\n验证成功:")
                print(f"  字段名: {row[0]}")
                print(f"  数据类型: {row[1]}")
                print(f"  默认值: {row[2]}")
            else:
                print("❌ 验证失败: 字段不存在")
                
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = add_remaining_stock_field()
    
    if success:
        print("\n" + "="*60)
        print("✅ 修复完成! 现在可以重新启动看板")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ 修复失败,请检查数据库连接")
        print("="*60)
