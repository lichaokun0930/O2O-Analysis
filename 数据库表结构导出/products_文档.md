# 表: products

**数据行数**: 6,377 行
**生成时间**: 2025-12-09 18:48:56

## 列定义

| 列名 | 类型 | 允许NULL | 默认值 | 说明 |
|------|------|----------|--------|------|
| id | INTEGER | ❌ | nextval('products_id_seq'::regclass) | - |
| product_name | VARCHAR(500) | ❌ | - | 商品名称 |
| barcode | VARCHAR(100) | ✅ | - | 条码 |
| store_code | VARCHAR(100) | ✅ | - | 店内码 |
| category_level1 | VARCHAR(100) | ✅ | - | 一级分类 |
| category_level3 | VARCHAR(100) | ✅ | - | 三级分类 |
| current_price | DOUBLE PRECISION | ✅ | - | 当前售价 |
| current_cost | DOUBLE PRECISION | ✅ | - | 当前成本 |
| stock | INTEGER | ✅ | - | 当前库存 |
| stock_status | VARCHAR(20) | ✅ | - | 库存状态：充足/紧张/售罄 |
| product_role | VARCHAR(20) | ✅ | - | 商品角色：流量品/利润品/形象品 |
| lifecycle_stage | VARCHAR(20) | ✅ | - | 生命周期：明星/金牛/引流/淘汰 |
| total_sales | DOUBLE PRECISION | ✅ | - | 总销售额 |
| total_orders | INTEGER | ✅ | - | 总订单数 |
| total_quantity | INTEGER | ✅ | - | 总销量 |
| avg_profit_margin | DOUBLE PRECISION | ✅ | - | 平均利润率 |
| is_active | BOOLEAN | ✅ | - | 是否在售 |
| created_at | TIMESTAMP | ✅ | - | 创建时间 |
| updated_at | TIMESTAMP | ✅ | - | 更新时间 |
| last_sale_date | TIMESTAMP | ✅ | - | 最后销售日期 |

## 主键

- `id`

## 索引

| 索引名 | 列 | 唯一 |
|--------|----|----|
| ix_products_barcode | barcode | ✅ |
| ix_products_category_level1 | category_level1 | ❌ |
| ix_products_category_level3 | category_level3 | ❌ |
| ix_products_product_name | product_name | ❌ |
| ix_products_product_role | product_role | ❌ |
