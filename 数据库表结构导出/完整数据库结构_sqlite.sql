-- ============================================
-- 完整数据库结构 (SQLITE)
-- 生成时间: 2025-12-09 18:48:56
-- 包含表: orders, products
-- ============================================

-- ============================================
-- 表名: orders
-- 行数: 19,477
-- 生成时间: 2025-12-09 18:48:56
-- ============================================

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER NOT NULL DEFAULT nextval('orders_id_seq'::regclass),
    order_id TEXT NOT NULL,
    date TEXT NOT NULL,
    store_name TEXT,
    product_id INTEGER,
    product_name TEXT NOT NULL,
    barcode TEXT,
    category_level1 TEXT,
    category_level3 TEXT,
    price REAL NOT NULL,
    original_price REAL,
    cost REAL,
    actual_price REAL,
    quantity INTEGER,
    amount REAL,
    profit REAL,
    profit_margin REAL,
    delivery_fee REAL,
    commission REAL,
    platform_service_fee REAL,
    user_paid_delivery_fee REAL,
    delivery_discount REAL,
    full_reduction REAL,
    product_discount REAL,
    merchant_voucher REAL,
    merchant_share REAL,
    packaging_fee REAL,
    gift_amount REAL,
    other_merchant_discount REAL,
    new_customer_discount REAL,
    corporate_rebate REAL,
    delivery_platform TEXT,
    store_franchise_type INTEGER,
    scene TEXT,
    time_period TEXT,
    address TEXT,
    channel TEXT,
    created_at TEXT,
    updated_at TEXT,
    remaining_stock REAL DEFAULT 0,
    stock INTEGER DEFAULT 0,
    delivery_distance REAL DEFAULT 0,
    store_id TEXT,
    city TEXT,
    store_code TEXT,
    order_number TEXT DEFAULT NULL::character varying,
    PRIMARY KEY (id)
);

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

