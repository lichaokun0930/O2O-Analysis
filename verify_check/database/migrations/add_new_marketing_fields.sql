-- =====================================================
-- 数据库迁移脚本：新增4个营销和利润字段
-- 执行日期: 2025-01-12
-- 用途: 支持更精确的利润和营销成本计算
-- =====================================================

-- 为 orders 表新增4个字段
ALTER TABLE orders 
ADD COLUMN gift_amount REAL DEFAULT 0 COMMENT '满赠金额',
ADD COLUMN other_merchant_discount REAL DEFAULT 0 COMMENT '商家其他优惠',
ADD COLUMN new_customer_discount REAL DEFAULT 0 COMMENT '新客减免金额',
ADD COLUMN corporate_rebate REAL DEFAULT 0 COMMENT '企客后返';

-- 验证字段添加成功
SELECT 
    gift_amount,
    other_merchant_discount,
    new_customer_discount,
    corporate_rebate
FROM orders
LIMIT 1;

-- 备注：
-- 1. 这4个字段默认值为0，不影响现有数据
-- 2. 新上传的数据会自动填充这些字段
-- 3. 旧数据保持为0，计算逻辑向后兼容
