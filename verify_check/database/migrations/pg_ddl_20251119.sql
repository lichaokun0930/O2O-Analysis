-- ============================================================================
-- 数据库迁移脚本 - 添加门店加盟类型字段
-- ============================================================================
-- 文件名: pg_ddl_20251119.sql
-- 创建日期: 2025-11-19
-- 目标表: orders
-- 变更内容: 新增 store_franchise_type 字段
-- ============================================================================

-- 1. 添加字段
-- 说明: 添加门店加盟类型字段,用于区分直营店/加盟店/托管店/买断店
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS store_franchise_type SMALLINT DEFAULT NULL;

-- 2. 添加字段注释
-- 说明: 使用中文注释便于理解业务含义
COMMENT ON COLUMN orders.store_franchise_type IS '门店加盟类型(1=直营店,2=加盟店,3=托管店,4=买断,NULL=未分类)';

-- 3. 创建索引
-- 说明: 提升按加盟类型筛选查询的性能
CREATE INDEX IF NOT EXISTS idx_orders_franchise_type 
ON orders(store_franchise_type);

-- 4. 添加检查约束(确保数据完整性)
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
-- WHERE store_name IN ('总部直营店', '旗舰店', '形象店')
--   AND store_franchise_type IS NULL;

-- UPDATE orders 
-- SET store_franchise_type = 2  -- 加盟店
-- WHERE store_name LIKE '%加盟%'
--   AND store_franchise_type IS NULL;

-- UPDATE orders 
-- SET store_franchise_type = 3  -- 托管店
-- WHERE store_name LIKE '%托管%'
--   AND store_franchise_type IS NULL;

-- UPDATE orders 
-- SET store_franchise_type = 4  -- 买断
-- WHERE store_name LIKE '%买断%'
--   AND store_franchise_type IS NULL;

-- 示例2: 根据其他业务规则更新
-- UPDATE orders 
-- SET store_franchise_type = CASE
--     WHEN store_name LIKE '%直营%' OR store_name LIKE '%总部%' THEN 1
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
-- 执行日期: _______________
-- 执行人: _______________
-- 验证结果: [ ] 成功  [ ] 失败
-- 备注: _______________________________________________________________
