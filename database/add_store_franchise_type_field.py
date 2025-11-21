#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加门店加盟类型字段
在orders表中添加store_franchise_type字段用于存储门店加盟类型信息

字段说明:
    store_franchise_type: SMALLINT
    - 1 = 直营店
    - 2 = 加盟店
    - 3 = 托管店
    - 4 = 买断
    - NULL = 未分类（历史数据）

创建日期: 2025-11-19
作者: 系统管理员
"""

from connection import engine, SessionLocal
from sqlalchemy import text
from datetime import datetime
import os

def generate_sql_script(output_dir='migrations'):
    """生成标准DDL SQL脚本,用于生产环境部署"""
    
    today = datetime.now().strftime('%Y%m%d')
    filename = f'pg_ddl_{today}.sql'
    
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = os.path.join(output_dir, filename)
    
    sql_content = f"""-- ============================================================================
-- 数据库迁移脚本 - 添加门店加盟类型字段
-- ============================================================================
-- 文件名: {filename}
-- 创建日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- 目标表: orders
-- 变更内容: 新增 store_franchise_type 字段
-- ============================================================================

-- 1. 添加字段
-- 说明: 添加门店加盟类型字段,用于区分直营店/加盟店/托管店/买断店
ALTER TABLE orders 
ADD COLUMN store_franchise_type SMALLINT DEFAULT NULL;

-- 2. 添加字段注释
-- 说明: 使用中文注释便于理解业务含义
COMMENT ON COLUMN orders.store_franchise_type IS '门店加盟类型(1=直营店,2=加盟店,3=托管店,4=买断,NULL=未分类)';

-- 3. 创建索引
-- 说明: 提升按加盟类型筛选查询的性能
CREATE INDEX IF NOT EXISTS idx_orders_franchise_type 
ON orders(store_franchise_type);

-- 4. 添加检查约束(可选,确保数据完整性)
-- 说明: 限制字段值只能是1-4或NULL
ALTER TABLE orders
ADD CONSTRAINT chk_franchise_type 
CHECK (store_franchise_type IS NULL OR store_franchise_type BETWEEN 1 AND 4);

-- ============================================================================
-- 验证脚本 (执行后运行以下SQL验证结果)
-- ============================================================================
-- SELECT 
--     column_name, 
--     data_type, 
--     is_nullable,
--     column_default
-- FROM information_schema.columns 
-- WHERE table_name='orders' AND column_name='store_franchise_type';

-- ============================================================================
-- 回滚脚本 (如需回滚,执行以下SQL)
-- ============================================================================
-- DROP INDEX IF EXISTS idx_orders_franchise_type;
-- ALTER TABLE orders DROP CONSTRAINT IF EXISTS chk_franchise_type;
-- ALTER TABLE orders DROP COLUMN IF EXISTS store_franchise_type;

-- ============================================================================
-- 数据回填示例 (如果需要为历史数据补充加盟类型)
-- ============================================================================
-- 示例1: 根据门店名称批量更新
-- UPDATE orders 
-- SET store_franchise_type = 1  -- 直营店
-- WHERE store_name IN ('总部直营店', '旗舰店', '形象店');

-- UPDATE orders 
-- SET store_franchise_type = 2  -- 加盟店
-- WHERE store_name LIKE '%加盟%';

-- 示例2: 根据其他业务规则更新
-- UPDATE orders 
-- SET store_franchise_type = CASE
--     WHEN store_name LIKE '%直营%' THEN 1
--     WHEN store_name LIKE '%加盟%' THEN 2
--     WHEN store_name LIKE '%托管%' THEN 3
--     WHEN store_name LIKE '%买断%' THEN 4
--     ELSE NULL
-- END
-- WHERE store_franchise_type IS NULL;

-- ============================================================================
-- 统计查询示例
-- ============================================================================
-- 按加盟类型统计订单数和销售额
-- SELECT 
--     CASE store_franchise_type
--         WHEN 1 THEN '直营店'
--         WHEN 2 THEN '加盟店'
--         WHEN 3 THEN '托管店'
--         WHEN 4 THEN '买断'
--         ELSE '未分类'
--     END AS 加盟类型,
--     COUNT(*) AS 订单数,
--     SUM(amount) AS 销售额,
--     AVG(profit_margin) AS 平均利润率
-- FROM orders
-- GROUP BY store_franchise_type
-- ORDER BY 订单数 DESC;

-- ============================================================================
-- 执行完成标记
-- ============================================================================
-- 执行日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- 执行人: _______________
-- 验证结果: [ ] 成功  [ ] 失败
-- 备注: _______________________________________________________________
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(sql_content)
    
    return filepath


def add_store_franchise_type_field():
    """向orders表添加store_franchise_type字段"""
    
    print("\n" + "="*80)
    print("🔧 数据库迁移：添加门店加盟类型字段")
    print("="*80)
    print(f"📅 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 目标表: orders")
    print(f"📝 字段名: store_franchise_type")
    print(f"📊 数据类型: SMALLINT")
    print(f"💡 编码规则: 1=直营店, 2=加盟店, 3=托管店, 4=买断")
    print("="*80)
    
    session = SessionLocal()
    
    try:
        # Step 1: 检查字段是否已存在
        print("\n📋 Step 1/6: 检查字段是否存在...")
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='orders' AND column_name='store_franchise_type'
        """))
        
        exists = result.fetchone() is not None
        
        if exists:
            print("✅ store_franchise_type 字段已存在，跳过添加")
            print("💡 提示: 如需重新创建,请先手动删除该字段")
            return True
        
        print("⚠️  字段不存在，开始添加...")
        
        # Step 2: 添加字段
        print("\n📋 Step 2/6: 添加 store_franchise_type 字段...")
        session.execute(text("""
            ALTER TABLE orders 
            ADD COLUMN store_franchise_type SMALLINT DEFAULT NULL
        """))
        session.commit()
        print("✅ 字段添加成功 (数据类型: SMALLINT, 默认值: NULL)")
        
        # Step 3: 添加中文注释
        print("\n📋 Step 3/6: 添加字段注释...")
        session.execute(text("""
            COMMENT ON COLUMN orders.store_franchise_type 
            IS '门店加盟类型(1=直营店,2=加盟店,3=托管店,4=买断,NULL=未分类)'
        """))
        session.commit()
        print("✅ 注释添加成功")
        
        # Step 4: 创建索引
        print("\n📋 Step 4/6: 创建索引 (提升查询性能)...")
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_orders_franchise_type 
            ON orders(store_franchise_type)
        """))
        session.commit()
        print("✅ 索引创建成功 (索引名: idx_orders_franchise_type)")
        
        # Step 5: 添加检查约束
        print("\n📋 Step 5/6: 添加数据约束 (确保数据完整性)...")
        try:
            session.execute(text("""
                ALTER TABLE orders
                ADD CONSTRAINT chk_franchise_type 
                CHECK (store_franchise_type IS NULL OR store_franchise_type BETWEEN 1 AND 4)
            """))
            session.commit()
            print("✅ 约束添加成功 (仅允许1-4或NULL)")
        except Exception as e:
            if 'already exists' in str(e).lower():
                print("✅ 约束已存在，跳过")
            else:
                raise
        
        # Step 6: 验证结果
        print("\n📋 Step 6/6: 验证迁移结果...")
        result = session.execute(text("""
            SELECT 
                column_name, 
                data_type, 
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name='orders' AND column_name='store_franchise_type'
        """))
        
        field_info = result.fetchone()
        if field_info:
            print(f"✅ 字段验证成功:")
            print(f"   📌 字段名: {field_info[0]}")
            print(f"   📌 数据类型: {field_info[1]}")
            print(f"   📌 允许空值: {field_info[3]}")
            print(f"   📌 默认值: {field_info[4]}")
        
        # 验证索引
        result = session.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes 
            WHERE tablename='orders' AND indexname='idx_orders_franchise_type'
        """))
        
        index_info = result.fetchone()
        if index_info:
            print(f"✅ 索引验证成功:")
            print(f"   📌 索引名: {index_info[0]}")
        
        # 统计当前数据
        result = session.execute(text("""
            SELECT COUNT(*) FROM orders
        """))
        total_count = result.fetchone()[0]
        
        result = session.execute(text("""
            SELECT COUNT(*) FROM orders WHERE store_franchise_type IS NULL
        """))
        null_count = result.fetchone()[0]
        
        print(f"\n📊 数据统计:")
        print(f"   📌 订单总数: {total_count:,}")
        print(f"   📌 未分类订单: {null_count:,} ({null_count/total_count*100:.1f}%)")
        print(f"   💡 提示: 历史数据默认为NULL,后续导入的新数据将自动填充")
        
        # 生成SQL脚本
        print("\n📋 生成生产环境SQL脚本...")
        sql_file = generate_sql_script()
        print(f"✅ SQL脚本已生成: {sql_file}")
        print(f"   💡 可在生产环境执行此脚本完成迁移")
        
        print("\n" + "="*80)
        print("✅ 数据库迁移完成！")
        print("="*80)
        
        print("\n📚 后续操作指南:")
        print("1️⃣  代码更新:")
        print("   - database/models.py: 添加 store_franchise_type 字段定义")
        print("   - 真实数据处理器.py: 添加字段映射逻辑")
        print("   - 智能门店看板: 添加按加盟类型筛选功能(可选)")
        
        print("\n2️⃣  数据导入:")
        print("   - Excel新增列: '门店类型' 或 '加盟类型'")
        print("   - 数值编码: 1=直营, 2=加盟, 3=托管, 4=买断")
        print("   - 系统将自动识别并映射到 store_franchise_type")
        
        print("\n3️⃣  生产部署:")
        print(f"   psql -h [生产数据库] -U [用户名] -d o2o_dashboard \\")
        print(f"        -f database/migrations/pg_ddl_{datetime.now().strftime('%Y%m%d')}.sql")
        
        print("\n4️⃣  数据回填(可选):")
        print("   - 如需为历史数据补充加盟类型")
        print("   - 可参考生成的SQL脚本中的示例")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
        
        print("\n💡 错误排查建议:")
        print("1. 检查数据库连接是否正常")
        print("2. 确认是否有足够的权限执行DDL操作")
        print("3. 检查orders表是否存在")
        print("4. 查看详细错误堆栈信息")
        
        return False
        
    finally:
        session.close()


if __name__ == "__main__":
    print("="*80)
    print("🚀 门店加盟类型字段迁移工具")
    print("="*80)
    
    confirm = input("\n⚠️  即将修改数据库结构，是否继续? (yes/no): ")
    
    if confirm.lower() in ['yes', 'y']:
        success = add_store_franchise_type_field()
        
        if success:
            print("\n" + "="*80)
            print("🎉 迁移成功! 系统已准备好处理门店加盟类型数据")
            print("="*80)
        else:
            print("\n" + "="*80)
            print("❌ 迁移失败，请检查错误信息并重试")
            print("="*80)
    else:
        print("\n❌ 操作已取消")
