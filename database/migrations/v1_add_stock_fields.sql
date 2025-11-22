-- 迁移: 添加库存相关字段
-- 日期: 2025-11-22
-- 说明: 支持滞销品统计和库存周转分析

-- 添加库存字段
ALTER TABLE orders ADD COLUMN IF NOT EXISTS stock INTEGER DEFAULT 0;
COMMENT ON COLUMN orders.stock IS '库存数量';

-- 添加剩余库存字段
ALTER TABLE orders ADD COLUMN IF NOT EXISTS remaining_stock FLOAT DEFAULT 0;
COMMENT ON COLUMN orders.remaining_stock IS '剩余库存(精确到小数)';

-- 添加配送距离字段
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_distance FLOAT DEFAULT 0;
COMMENT ON COLUMN orders.delivery_distance IS '配送距离(公里)';

-- 添加门店ID字段
ALTER TABLE orders ADD COLUMN IF NOT EXISTS store_id VARCHAR(100);
COMMENT ON COLUMN orders.store_id IS '门店ID';

-- 添加城市字段
ALTER TABLE orders ADD COLUMN IF NOT EXISTS city VARCHAR(100);
COMMENT ON COLUMN orders.city IS '城市';

-- 验证字段是否添加成功
DO $$
DECLARE
    field_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO field_count
    FROM information_schema.columns
    WHERE table_name = 'orders'
    AND column_name IN ('stock', 'remaining_stock', 'delivery_distance', 'store_id', 'city');
    
    RAISE NOTICE '已添加 % 个字段', field_count;
    
    IF field_count = 5 THEN
        RAISE NOTICE '✓ 迁移成功: 所有字段已添加';
    ELSE
        RAISE WARNING '⚠ 迁移不完整: 只添加了 % 个字段', field_count;
    END IF;
END $$;
