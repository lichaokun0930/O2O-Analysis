-- ============================================
-- 表名: products
-- 行数: 6,377
-- 生成时间: 2025-12-09 18:48:56
-- ============================================

CREATE TABLE IF NOT EXISTS products (
    id INTEGER NOT NULL DEFAULT nextval('products_id_seq'::regclass),
    product_name VARCHAR(500) NOT NULL,
    barcode VARCHAR(100),
    store_code VARCHAR(100),
    category_level1 VARCHAR(100),
    category_level3 VARCHAR(100),
    current_price DOUBLE PRECISION,
    current_cost DOUBLE PRECISION,
    stock INTEGER,
    stock_status VARCHAR(20),
    product_role VARCHAR(20),
    lifecycle_stage VARCHAR(20),
    total_sales DOUBLE PRECISION,
    total_orders INTEGER,
    total_quantity INTEGER,
    avg_profit_margin DOUBLE PRECISION,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_sale_date TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_products_barcode ON products (barcode);
CREATE INDEX ix_products_category_level1 ON products (category_level1);
CREATE INDEX ix_products_category_level3 ON products (category_level3);
CREATE INDEX ix_products_product_name ON products (product_name);
CREATE INDEX ix_products_product_role ON products (product_role);

-- 列注释
COMMENT ON COLUMN products.product_name IS '商品名称';
COMMENT ON COLUMN products.barcode IS '条码';
COMMENT ON COLUMN products.store_code IS '店内码';
COMMENT ON COLUMN products.category_level1 IS '一级分类';
COMMENT ON COLUMN products.category_level3 IS '三级分类';
COMMENT ON COLUMN products.current_price IS '当前售价';
COMMENT ON COLUMN products.current_cost IS '当前成本';
COMMENT ON COLUMN products.stock IS '当前库存';
COMMENT ON COLUMN products.stock_status IS '库存状态：充足/紧张/售罄';
COMMENT ON COLUMN products.product_role IS '商品角色：流量品/利润品/形象品';
COMMENT ON COLUMN products.lifecycle_stage IS '生命周期：明星/金牛/引流/淘汰';
COMMENT ON COLUMN products.total_sales IS '总销售额';
COMMENT ON COLUMN products.total_orders IS '总订单数';
COMMENT ON COLUMN products.total_quantity IS '总销量';
COMMENT ON COLUMN products.avg_profit_margin IS '平均利润率';
COMMENT ON COLUMN products.is_active IS '是否在售';
COMMENT ON COLUMN products.created_at IS '创建时间';
COMMENT ON COLUMN products.updated_at IS '更新时间';
COMMENT ON COLUMN products.last_sale_date IS '最后销售日期';