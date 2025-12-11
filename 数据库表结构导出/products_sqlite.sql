-- ============================================
-- 表名: products
-- 行数: 6,377
-- 生成时间: 2025-12-09 18:48:56
-- ============================================

CREATE TABLE IF NOT EXISTS products (
    id INTEGER NOT NULL DEFAULT nextval('products_id_seq'::regclass),
    product_name TEXT NOT NULL,
    barcode TEXT,
    store_code TEXT,
    category_level1 TEXT,
    category_level3 TEXT,
    current_price REAL,
    current_cost REAL,
    stock INTEGER,
    stock_status TEXT,
    product_role TEXT,
    lifecycle_stage TEXT,
    total_sales REAL,
    total_orders INTEGER,
    total_quantity INTEGER,
    avg_profit_margin REAL,
    is_active INTEGER,
    created_at TEXT,
    updated_at TEXT,
    last_sale_date TEXT,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_products_barcode ON products (barcode);
CREATE INDEX ix_products_category_level1 ON products (category_level1);
CREATE INDEX ix_products_category_level3 ON products (category_level3);
CREATE INDEX ix_products_product_name ON products (product_name);
CREATE INDEX ix_products_product_role ON products (product_role);