-- ============================================
-- 表名: orders
-- 行数: 19,477
-- 生成时间: 2025-12-09 18:48:56
-- ============================================

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER NOT NULL DEFAULT nextval('orders_id_seq'::regclass),
    order_id VARCHAR(100) NOT NULL,
    date TIMESTAMP NOT NULL,
    store_name VARCHAR(200),
    product_id INTEGER,
    product_name VARCHAR(500) NOT NULL,
    barcode VARCHAR(100),
    category_level1 VARCHAR(100),
    category_level3 VARCHAR(100),
    price DOUBLE PRECISION NOT NULL,
    original_price DOUBLE PRECISION,
    cost DOUBLE PRECISION,
    actual_price DOUBLE PRECISION,
    quantity INTEGER,
    amount DOUBLE PRECISION,
    profit DOUBLE PRECISION,
    profit_margin DOUBLE PRECISION,
    delivery_fee DOUBLE PRECISION,
    commission DOUBLE PRECISION,
    platform_service_fee DOUBLE PRECISION,
    user_paid_delivery_fee DOUBLE PRECISION,
    delivery_discount DOUBLE PRECISION,
    full_reduction DOUBLE PRECISION,
    product_discount DOUBLE PRECISION,
    merchant_voucher DOUBLE PRECISION,
    merchant_share DOUBLE PRECISION,
    packaging_fee DOUBLE PRECISION,
    gift_amount DOUBLE PRECISION,
    other_merchant_discount DOUBLE PRECISION,
    new_customer_discount DOUBLE PRECISION,
    corporate_rebate DOUBLE PRECISION,
    delivery_platform VARCHAR(100),
    store_franchise_type INTEGER,
    scene VARCHAR(50),
    time_period VARCHAR(50),
    address TEXT,
    channel VARCHAR(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    remaining_stock DOUBLE PRECISION DEFAULT 0,
    stock INTEGER DEFAULT 0,
    delivery_distance DOUBLE PRECISION DEFAULT 0,
    store_id VARCHAR(100),
    city VARCHAR(100),
    store_code VARCHAR(100),
    order_number VARCHAR(100) DEFAULT NULL::character varying,
    PRIMARY KEY (id)
);

ALTER TABLE orders ADD FOREIGN KEY (product_id) REFERENCES products(id);
CREATE INDEX idx_date_store ON orders (date, store_name);
CREATE INDEX idx_orders_order_number ON orders (order_number);
CREATE INDEX idx_orders_store_code ON orders (store_code);
CREATE INDEX idx_product_date ON orders (product_id, date);
CREATE INDEX idx_scene_time ON orders (scene, time_period);
CREATE INDEX ix_orders_barcode ON orders (barcode);
CREATE INDEX ix_orders_category_level1 ON orders (category_level1);
CREATE INDEX ix_orders_category_level3 ON orders (category_level3);
CREATE INDEX ix_orders_channel ON orders (channel);
CREATE INDEX ix_orders_city ON orders (city);
CREATE INDEX ix_orders_date ON orders (date);
CREATE INDEX ix_orders_delivery_platform ON orders (delivery_platform);
CREATE INDEX ix_orders_order_id ON orders (order_id);
CREATE INDEX ix_orders_order_number ON orders (order_number);
CREATE INDEX ix_orders_product_id ON orders (product_id);
CREATE INDEX ix_orders_scene ON orders (scene);
CREATE INDEX ix_orders_store_code ON orders (store_code);
CREATE INDEX ix_orders_store_franchise_type ON orders (store_franchise_type);
CREATE INDEX ix_orders_store_id ON orders (store_id);
CREATE INDEX ix_orders_time_period ON orders (time_period);

-- 列注释
COMMENT ON COLUMN orders.order_id IS '订单ID';
COMMENT ON COLUMN orders.date IS '下单时间';
COMMENT ON COLUMN orders.store_name IS '门店名称';
COMMENT ON COLUMN orders.product_id IS '商品ID';
COMMENT ON COLUMN orders.product_name IS '商品名称';
COMMENT ON COLUMN orders.barcode IS '条码';
COMMENT ON COLUMN orders.category_level1 IS '一级分类';
COMMENT ON COLUMN orders.category_level3 IS '三级分类';
COMMENT ON COLUMN orders.price IS '商品实售价';
COMMENT ON COLUMN orders.original_price IS '商品原价';
COMMENT ON COLUMN orders.cost IS '商品采购成本';
COMMENT ON COLUMN orders.actual_price IS '实收价格';
COMMENT ON COLUMN orders.quantity IS '销量';
COMMENT ON COLUMN orders.amount IS '销售额';
COMMENT ON COLUMN orders.profit IS '利润';
COMMENT ON COLUMN orders.profit_margin IS '利润率';
COMMENT ON COLUMN orders.delivery_fee IS '物流配送费';
COMMENT ON COLUMN orders.commission IS '平台佣金';
COMMENT ON COLUMN orders.platform_service_fee IS '平台服务费';
COMMENT ON COLUMN orders.user_paid_delivery_fee IS '用户支付配送费';
COMMENT ON COLUMN orders.delivery_discount IS '配送费减免金额';
COMMENT ON COLUMN orders.full_reduction IS '满减金额';
COMMENT ON COLUMN orders.product_discount IS '商品减免金额';
COMMENT ON COLUMN orders.merchant_voucher IS '商家代金券';
COMMENT ON COLUMN orders.merchant_share IS '商家承担部分券';
COMMENT ON COLUMN orders.packaging_fee IS '打包袋金额';
COMMENT ON COLUMN orders.gift_amount IS '满赠金额';
COMMENT ON COLUMN orders.other_merchant_discount IS '商家其他优惠';
COMMENT ON COLUMN orders.new_customer_discount IS '新客减免金额';
COMMENT ON COLUMN orders.corporate_rebate IS '企客后返';
COMMENT ON COLUMN orders.delivery_platform IS '配送平台';
COMMENT ON COLUMN orders.store_franchise_type IS '门店加盟类型(1=直营店,2=加盟店,3=托管店,4=买断,NULL=未分类)';
COMMENT ON COLUMN orders.scene IS '消费场景';
COMMENT ON COLUMN orders.time_period IS '时段';
COMMENT ON COLUMN orders.address IS '收货地址';
COMMENT ON COLUMN orders.channel IS '渠道';
COMMENT ON COLUMN orders.created_at IS '创建时间';
COMMENT ON COLUMN orders.updated_at IS '更新时间';
COMMENT ON COLUMN orders.remaining_stock IS '剩余库存(精确到小数)';
COMMENT ON COLUMN orders.stock IS '库存数量';
COMMENT ON COLUMN orders.delivery_distance IS '配送距离(公里)';
COMMENT ON COLUMN orders.store_id IS '门店ID';
COMMENT ON COLUMN orders.city IS '城市';