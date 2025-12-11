# 表: orders

**数据行数**: 19,477 行
**生成时间**: 2025-12-09 18:48:56

## 列定义

| 列名 | 类型 | 允许NULL | 默认值 | 说明 |
|------|------|----------|--------|------|
| id | INTEGER | ❌ | nextval('orders_id_seq'::regclass) | - |
| order_id | VARCHAR(100) | ❌ | - | 订单ID |
| date | TIMESTAMP | ❌ | - | 下单时间 |
| store_name | VARCHAR(200) | ✅ | - | 门店名称 |
| product_id | INTEGER | ✅ | - | 商品ID |
| product_name | VARCHAR(500) | ❌ | - | 商品名称 |
| barcode | VARCHAR(100) | ✅ | - | 条码 |
| category_level1 | VARCHAR(100) | ✅ | - | 一级分类 |
| category_level3 | VARCHAR(100) | ✅ | - | 三级分类 |
| price | DOUBLE PRECISION | ❌ | - | 商品实售价 |
| original_price | DOUBLE PRECISION | ✅ | - | 商品原价 |
| cost | DOUBLE PRECISION | ✅ | - | 商品采购成本 |
| actual_price | DOUBLE PRECISION | ✅ | - | 实收价格 |
| quantity | INTEGER | ✅ | - | 销量 |
| amount | DOUBLE PRECISION | ✅ | - | 销售额 |
| profit | DOUBLE PRECISION | ✅ | - | 利润 |
| profit_margin | DOUBLE PRECISION | ✅ | - | 利润率 |
| delivery_fee | DOUBLE PRECISION | ✅ | - | 物流配送费 |
| commission | DOUBLE PRECISION | ✅ | - | 平台佣金 |
| platform_service_fee | DOUBLE PRECISION | ✅ | - | 平台服务费 |
| user_paid_delivery_fee | DOUBLE PRECISION | ✅ | - | 用户支付配送费 |
| delivery_discount | DOUBLE PRECISION | ✅ | - | 配送费减免金额 |
| full_reduction | DOUBLE PRECISION | ✅ | - | 满减金额 |
| product_discount | DOUBLE PRECISION | ✅ | - | 商品减免金额 |
| merchant_voucher | DOUBLE PRECISION | ✅ | - | 商家代金券 |
| merchant_share | DOUBLE PRECISION | ✅ | - | 商家承担部分券 |
| packaging_fee | DOUBLE PRECISION | ✅ | - | 打包袋金额 |
| gift_amount | DOUBLE PRECISION | ✅ | - | 满赠金额 |
| other_merchant_discount | DOUBLE PRECISION | ✅ | - | 商家其他优惠 |
| new_customer_discount | DOUBLE PRECISION | ✅ | - | 新客减免金额 |
| corporate_rebate | DOUBLE PRECISION | ✅ | - | 企客后返 |
| delivery_platform | VARCHAR(100) | ✅ | - | 配送平台 |
| store_franchise_type | INTEGER | ✅ | - | 门店加盟类型(1=直营店,2=加盟店,3=托管店,4=买断,NULL=未分类) |
| scene | VARCHAR(50) | ✅ | - | 消费场景 |
| time_period | VARCHAR(50) | ✅ | - | 时段 |
| address | TEXT | ✅ | - | 收货地址 |
| channel | VARCHAR(100) | ✅ | - | 渠道 |
| created_at | TIMESTAMP | ✅ | - | 创建时间 |
| updated_at | TIMESTAMP | ✅ | - | 更新时间 |
| remaining_stock | DOUBLE PRECISION | ✅ | 0 | 剩余库存(精确到小数) |
| stock | INTEGER | ✅ | 0 | 库存数量 |
| delivery_distance | DOUBLE PRECISION | ✅ | 0 | 配送距离(公里) |
| store_id | VARCHAR(100) | ✅ | - | 门店ID |
| city | VARCHAR(100) | ✅ | - | 城市 |
| store_code | VARCHAR(100) | ✅ | - | - |
| order_number | VARCHAR(100) | ✅ | NULL::character varying | - |

## 主键

- `id`

## 外键

- `product_id` → `products(id)`

## 索引

| 索引名 | 列 | 唯一 |
|--------|----|----|
| idx_date_store | date, store_name | ❌ |
| idx_orders_order_number | order_number | ❌ |
| idx_orders_store_code | store_code | ❌ |
| idx_product_date | product_id, date | ❌ |
| idx_scene_time | scene, time_period | ❌ |
| ix_orders_barcode | barcode | ❌ |
| ix_orders_category_level1 | category_level1 | ❌ |
| ix_orders_category_level3 | category_level3 | ❌ |
| ix_orders_channel | channel | ❌ |
| ix_orders_city | city | ❌ |
| ix_orders_date | date | ❌ |
| ix_orders_delivery_platform | delivery_platform | ❌ |
| ix_orders_order_id | order_id | ❌ |
| ix_orders_order_number | order_number | ❌ |
| ix_orders_product_id | product_id | ❌ |
| ix_orders_scene | scene | ❌ |
| ix_orders_store_code | store_code | ❌ |
| ix_orders_store_franchise_type | store_franchise_type | ❌ |
| ix_orders_store_id | store_id | ❌ |
| ix_orders_time_period | time_period | ❌ |
