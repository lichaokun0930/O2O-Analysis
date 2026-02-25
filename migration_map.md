# 函数迁移映射清单

> 记录每个函数从 `orders.py` 迁移到新模块的位置

## orders.py → orders_marketing.py

| 函数名 | 原行范围 | 迁移状态 | 验证状态 | 源码已删 |
|--------|----------|----------|----------|----------|
| `get_marketing_structure()` | 4105-4256 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `get_marketing_trend()` | 4261-4410 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |

## orders.py → orders_analysis.py

| 函数名 | 原行范围 | 迁移状态 | 验证状态 | 源码已删 |
|--------|----------|----------|----------|----------|
| `get_profit_distribution()` | 1411-1467 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `get_price_distribution()` | 1470-1568 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `get_price_range_color()` | 1571-1580 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `get_category_trend()` | 1583-1662 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `get_anomaly_detection()` | 2091-2202 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `get_category_hourly_trend()` | 2377-2624 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `get_top_products_by_date()` | 2627-2818 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |

## orders.py → orders_delivery.py

| 函数名 | 原行范围 | 迁移状态 | 验证状态 | 源码已删 |
|--------|----------|----------|----------|----------|
| `identify_peak_periods()` | 2823-2893 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `get_hourly_profit()` | 2896-3246 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `get_cost_structure()` | 3251-3427 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `DISTANCE_BANDS` 常量 | 3428-3443 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `get_distance_band()` | 3444-3462 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `get_distance_band_index()` | 3465-3482 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `get_distance_analysis()` | 3485-3901 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |
| `get_delivery_radar_data()` | 3906-4100 | ⬜ 待迁移 | ⬜ 待验证 | ⬜ |

## 保留在 orders.py 的函数（不迁移）

| 函数名 | 行范围 | 类型 |
|--------|--------|------|
| 缓存配置 + Redis | 1-140 | 公共 |
| `get_order_data()` | 141-286 | 公共 |
| `invalidate_cache()` / `clear_cache()` | 289-351 | 公共 |
| `calculate_order_metrics()` | 354-473 | 公共 |
| `calculate_gmv()` | 476-592 | 公共 |
| `get_order_overview()` | 595-738 | 接口 |
| `get_all_stores_overview()` | 741-972 | 接口 |
| `get_channel_stats()` | 975-1055 | 接口 |
| `get_order_trend()` | 1058-1261 | 接口 |
| `get_order_list()` | 1264-1338 | 接口 |
| `get_store_list()` / `get_channel_list()` | 1341-1408 | 接口 |
| `get_order_comparison()` | 1665-1765 | 接口 |
| `calculate_period_metrics()` | 1768-1802 | 公共 |
| `get_channel_comparison()` | 1805-1931 | 接口 |
| `calculate_channel_metrics()` / `get_channel_rating()` | 1934-2088 | 公共 |
| `export_orders()` | 2210-2313 | 接口 |
| `get_date_range()` | 2317-2372 | 接口 |
