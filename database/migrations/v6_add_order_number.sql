-- 迁移: add_order_number
-- 日期: 2025-12-09
-- 描述: 优化

-- 添加 order_number 字段
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_number VARCHAR(100);
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
