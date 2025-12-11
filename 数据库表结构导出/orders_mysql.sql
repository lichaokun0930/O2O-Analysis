-- ============================================
-- 表名: orders
-- 行数: 19,477
-- 生成时间: 2025-12-09 18:48:56
-- ============================================

CREATE TABLE IF NOT EXISTS `orders` (
    `id` INT NOT NULL DEFAULT nextval('orders_id_seq'::regclass),
    `order_id` VARCHAR(100) NOT NULL COMMENT '订单ID',
    `date` DATETIME NOT NULL COMMENT '下单时间',
    `store_name` VARCHAR(200) COMMENT '门店名称',
    `product_id` INT COMMENT '商品ID',
    `product_name` VARCHAR(500) NOT NULL COMMENT '商品名称',
    `barcode` VARCHAR(100) COMMENT '条码',
    `category_level1` VARCHAR(100) COMMENT '一级分类',
    `category_level3` VARCHAR(100) COMMENT '三级分类',
    `price` DOUBLE NOT NULL COMMENT '商品实售价',
    `original_price` DOUBLE COMMENT '商品原价',
    `cost` DOUBLE COMMENT '商品采购成本',
    `actual_price` DOUBLE COMMENT '实收价格',
    `quantity` INT COMMENT '销量',
    `amount` DOUBLE COMMENT '销售额',
    `profit` DOUBLE COMMENT '利润',
    `profit_margin` DOUBLE COMMENT '利润率',
    `delivery_fee` DOUBLE COMMENT '物流配送费',
    `commission` DOUBLE COMMENT '平台佣金',
    `platform_service_fee` DOUBLE COMMENT '平台服务费',
    `user_paid_delivery_fee` DOUBLE COMMENT '用户支付配送费',
    `delivery_discount` DOUBLE COMMENT '配送费减免金额',
    `full_reduction` DOUBLE COMMENT '满减金额',
    `product_discount` DOUBLE COMMENT '商品减免金额',
    `merchant_voucher` DOUBLE COMMENT '商家代金券',
    `merchant_share` DOUBLE COMMENT '商家承担部分券',
    `packaging_fee` DOUBLE COMMENT '打包袋金额',
    `gift_amount` DOUBLE COMMENT '满赠金额',
    `other_merchant_discount` DOUBLE COMMENT '商家其他优惠',
    `new_customer_discount` DOUBLE COMMENT '新客减免金额',
    `corporate_rebate` DOUBLE COMMENT '企客后返',
    `delivery_platform` VARCHAR(100) COMMENT '配送平台',
    `store_franchise_type` INT COMMENT '门店加盟类型(1=直营店,2=加盟店,3=托管店,4=买断,NULL=未分类)',
    `scene` VARCHAR(50) COMMENT '消费场景',
    `time_period` VARCHAR(50) COMMENT '时段',
    `address` TEXT COMMENT '收货地址',
    `channel` VARCHAR(100) COMMENT '渠道',
    `created_at` DATETIME COMMENT '创建时间',
    `updated_at` DATETIME COMMENT '更新时间',
    `remaining_stock` DOUBLE DEFAULT 0 COMMENT '剩余库存(精确到小数)',
    `stock` INT DEFAULT 0 COMMENT '库存数量',
    `delivery_distance` DOUBLE DEFAULT 0 COMMENT '配送距离(公里)',
    `store_id` VARCHAR(100) COMMENT '门店ID',
    `city` VARCHAR(100) COMMENT '城市',
    `store_code` VARCHAR(100),
    `order_number` VARCHAR(100) DEFAULT NULL::character varying,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX `idx_date_store` ON `orders` (`date`, `store_name`);
CREATE INDEX `idx_orders_order_number` ON `orders` (`order_number`);
CREATE INDEX `idx_orders_store_code` ON `orders` (`store_code`);
CREATE INDEX `idx_product_date` ON `orders` (`product_id`, `date`);
CREATE INDEX `idx_scene_time` ON `orders` (`scene`, `time_period`);
CREATE INDEX `ix_orders_barcode` ON `orders` (`barcode`);
CREATE INDEX `ix_orders_category_level1` ON `orders` (`category_level1`);
CREATE INDEX `ix_orders_category_level3` ON `orders` (`category_level3`);
CREATE INDEX `ix_orders_channel` ON `orders` (`channel`);
CREATE INDEX `ix_orders_city` ON `orders` (`city`);
CREATE INDEX `ix_orders_date` ON `orders` (`date`);
CREATE INDEX `ix_orders_delivery_platform` ON `orders` (`delivery_platform`);
CREATE INDEX `ix_orders_order_id` ON `orders` (`order_id`);
CREATE INDEX `ix_orders_order_number` ON `orders` (`order_number`);
CREATE INDEX `ix_orders_product_id` ON `orders` (`product_id`);
CREATE INDEX `ix_orders_scene` ON `orders` (`scene`);
CREATE INDEX `ix_orders_store_code` ON `orders` (`store_code`);
CREATE INDEX `ix_orders_store_franchise_type` ON `orders` (`store_franchise_type`);
CREATE INDEX `ix_orders_store_id` ON `orders` (`store_id`);
CREATE INDEX `ix_orders_time_period` ON `orders` (`time_period`);