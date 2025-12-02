-- 迁移: add_store_code
-- 日期: 2025-12-02
-- 描述: 优化迭代

-- 添加 store_code 字段
ALTER TABLE orders ADD COLUMN IF NOT EXISTS store_code VARCHAR(100);
CREATE INDEX IF NOT EXISTS idx_orders_store_code ON orders(store_code);

