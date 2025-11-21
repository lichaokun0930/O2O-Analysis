#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加配送平台字段
在orders表中添加delivery_platform字段用于存储配送平台信息
"""

from connection import engine, SessionLocal
from sqlalchemy import text

def add_delivery_platform_field():
    """向orders表添加delivery_platform字段"""
    
    print("\n" + "="*70)
    print("🔧 数据库迁移：添加配送平台字段")
    print("="*70)
    
    session = SessionLocal()
    
    try:
        # 1. 检查字段是否已存在
        print("\n📋 Step 1: 检查字段是否存在...")
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='orders' AND column_name='delivery_platform'
        """))
        
        exists = result.fetchone() is not None
        
        if exists:
            print("✅ delivery_platform字段已存在，无需添加")
            return True
        
        print("⚠️  字段不存在，开始添加...")
        
        # 2. 添加字段
        print("\n📋 Step 2: 添加delivery_platform字段...")
        session.execute(text("""
            ALTER TABLE orders 
            ADD COLUMN delivery_platform VARCHAR(100)
        """))
        session.commit()
        print("✅ 字段添加成功")
        
        # 3. 添加注释
        print("\n📋 Step 3: 添加字段注释...")
        session.execute(text("""
            COMMENT ON COLUMN orders.delivery_platform IS '配送平台'
        """))
        session.commit()
        print("✅ 注释添加成功")
        
        # 4. 创建索引（提升查询性能）
        print("\n📋 Step 4: 创建索引...")
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_delivery_platform 
            ON orders(delivery_platform)
        """))
        session.commit()
        print("✅ 索引创建成功")
        
        # 5. 验证结果
        print("\n📋 Step 5: 验证迁移结果...")
        result = session.execute(text("""
            SELECT 
                column_name, 
                data_type, 
                character_maximum_length,
                is_nullable
            FROM information_schema.columns 
            WHERE table_name='orders' AND column_name='delivery_platform'
        """))
        
        field_info = result.fetchone()
        if field_info:
            print(f"✅ 验证成功:")
            print(f"   字段名: {field_info[0]}")
            print(f"   数据类型: {field_info[1]}")
            print(f"   最大长度: {field_info[2]}")
            print(f"   允许空值: {field_info[3]}")
        
        # 6. 检查索引
        result = session.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename='orders' AND indexname='idx_delivery_platform'
        """))
        
        if result.fetchone():
            print("✅ 索引验证成功")
        
        print("\n" + "="*70)
        print("✅ 数据库迁移完成！")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()


if __name__ == "__main__":
    success = add_delivery_platform_field()
    
    if success:
        print("\n✅ 可以开始使用配送平台字段了！")
        print("\n使用示例:")
        print("  - 上传包含'配送平台'列的Excel文件")
        print("  - 数据会自动导入到delivery_platform字段")
        print("  - 在看板分析中可以按配送平台维度分析")
    else:
        print("\n❌ 迁移失败，请检查错误信息")
