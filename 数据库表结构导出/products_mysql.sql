-- ============================================
-- 表名: products
-- 行数: 6,377
-- 生成时间: 2025-12-09 18:48:56
-- ============================================

CREATE TABLE IF NOT EXISTS `products` (
    `id` INT NOT NULL DEFAULT nextval('products_id_seq'::regclass),
    `product_name` VARCHAR(500) NOT NULL COMMENT '商品名称',
    `barcode` VARCHAR(100) COMMENT '条码',
    `store_code` VARCHAR(100) COMMENT '店内码',
    `category_level1` VARCHAR(100) COMMENT '一级分类',
    `category_level3` VARCHAR(100) COMMENT '三级分类',
    `current_price` DOUBLE COMMENT '当前售价',
    `current_cost` DOUBLE COMMENT '当前成本',
    `stock` INT COMMENT '当前库存',
    `stock_status` VARCHAR(20) COMMENT '库存状态：充足/紧张/售罄',
    `product_role` VARCHAR(20) COMMENT '商品角色：流量品/利润品/形象品',
    `lifecycle_stage` VARCHAR(20) COMMENT '生命周期：明星/金牛/引流/淘汰',
    `total_sales` DOUBLE COMMENT '总销售额',
    `total_orders` INT COMMENT '总订单数',
    `total_quantity` INT COMMENT '总销量',
    `avg_profit_margin` DOUBLE COMMENT '平均利润率',
    `is_active` TINYINT(1) COMMENT '是否在售',
    `created_at` DATETIME COMMENT '创建时间',
    `updated_at` DATETIME COMMENT '更新时间',
    `last_sale_date` DATETIME COMMENT '最后销售日期',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE UNIQUE INDEX `ix_products_barcode` ON `products` (`barcode`);
CREATE INDEX `ix_products_category_level1` ON `products` (`category_level1`);
CREATE INDEX `ix_products_category_level3` ON `products` (`category_level3`);
CREATE INDEX `ix_products_product_name` ON `products` (`product_name`);
CREATE INDEX `ix_products_product_role` ON `products` (`product_role`);