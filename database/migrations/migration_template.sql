-- 迁移模板
-- 日期: YYYY-MM-DD
-- 说明: 描述这次迁移的目的

-- ==================== 数据库结构变更 ====================

-- 示例: 添加新表
-- CREATE TABLE IF NOT EXISTS new_table (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(100) NOT NULL,
--     created_at TIMESTAMP DEFAULT NOW()
-- );

-- 示例: 添加字段
-- ALTER TABLE orders ADD COLUMN IF NOT EXISTS new_field VARCHAR(100);
-- COMMENT ON COLUMN orders.new_field IS '字段说明';

-- 示例: 修改字段类型
-- ALTER TABLE orders ALTER COLUMN existing_field TYPE VARCHAR(200);

-- 示例: 添加索引
-- CREATE INDEX IF NOT EXISTS idx_orders_new_field ON orders(new_field);

-- 示例: 添加约束
-- ALTER TABLE orders ADD CONSTRAINT check_new_field CHECK (new_field IS NOT NULL);

-- ==================== 数据迁移(可选) ====================

-- 示例: 更新现有数据
-- UPDATE orders SET new_field = 'default_value' WHERE new_field IS NULL;

-- ==================== 验证 ====================

-- 验证变更是否成功
DO $$
DECLARE
    result_count INTEGER;
BEGIN
    -- 检查字段是否存在
    SELECT COUNT(*) INTO result_count
    FROM information_schema.columns
    WHERE table_name = 'orders'
    AND column_name = 'new_field';
    
    IF result_count > 0 THEN
        RAISE NOTICE '✓ 迁移成功';
    ELSE
        RAISE WARNING '⚠ 迁移失败';
    END IF;
END $$;
