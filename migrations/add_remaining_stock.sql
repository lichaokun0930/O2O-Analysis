-- 添加 remaining_stock 字段到 orders 表
-- 日期: 2025-11-22
-- 原因: 修复数据库查询错误 - 字段 remaining_stock 不存在

-- 检查字段是否已存在
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'orders' 
        AND column_name = 'remaining_stock'
    ) THEN
        -- 添加字段
        ALTER TABLE orders 
        ADD COLUMN remaining_stock FLOAT DEFAULT 0;
        
        -- 添加注释
        COMMENT ON COLUMN orders.remaining_stock IS '剩余库存';
        
        RAISE NOTICE '已添加 remaining_stock 字段';
    ELSE
        RAISE NOTICE 'remaining_stock 字段已存在';
    END IF;
END $$;
