# -*- coding: utf-8 -*-
"""
预聚合表配置驱动系统

设计目标：
- 新增预聚合表只需添加配置，无需修改代码
- 自动生成 SQL、自动同步、自动清除缓存
- 支持自定义聚合维度和计算字段

使用方法：
1. 在 AGGREGATION_CONFIGS 中添加新表配置
2. 运行数据库迁移创建表
3. 系统自动处理同步和缓存
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AggregationField:
    """聚合字段定义"""
    name: str                          # 目标字段名
    source: str                        # 源字段表达式（SQL）
    agg_func: str = "SUM"              # 聚合函数: SUM, COUNT, AVG, MAX, MIN, FIRST
    is_order_level: bool = False       # 是否订单级字段（需要先按订单聚合）
    default: Any = 0                   # 默认值


@dataclass
class DerivedField:
    """派生字段定义（基于聚合后的字段计算）"""
    name: str                          # 字段名
    formula: str                       # 计算公式（SQL CASE 表达式）


@dataclass
class AggregationConfig:
    """预聚合表配置"""
    table_name: str                    # 表名
    description: str                   # 描述
    group_by: List[str]                # 分组维度
    fields: List[AggregationField]     # 聚合字段
    derived_fields: List[DerivedField] = field(default_factory=list)  # 派生字段
    filter_condition: Optional[str] = None  # 过滤条件（SQL WHERE）
    order_level_first: bool = True     # 是否需要先按订单聚合


# ==================== 预聚合表配置 ====================
# 新增预聚合表只需在这里添加配置！

AGGREGATION_CONFIGS: Dict[str, AggregationConfig] = {
    
    # 门店日汇总表
    # 注意：total_profit 是原始利润额，actual_profit 是订单实际利润
    # 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    "store_daily_summary": AggregationConfig(
        table_name="store_daily_summary",
        description="门店日汇总（订单数、收入、利润等）",
        group_by=["store_name", "DATE(date) as summary_date", "channel"],
        fields=[
            AggregationField("order_count", "order_id", "COUNT_DISTINCT"),
            AggregationField("total_revenue", "COALESCE(actual_price, 0) * COALESCE(quantity, 1)", "SUM"),
            # 原始利润额（商品级字段，SUM聚合）
            AggregationField("total_profit", "COALESCE(profit, 0)", "SUM"),
            # 配送相关字段（订单级字段，MAX聚合）
            AggregationField("total_delivery_fee", "COALESCE(delivery_fee, 0)", "MAX", is_order_level=True),
            AggregationField("total_user_paid_delivery", "COALESCE(user_paid_delivery_fee, 0)", "MAX", is_order_level=True),
            AggregationField("total_delivery_discount", "COALESCE(delivery_discount, 0)", "MAX", is_order_level=True),
            AggregationField("total_corporate_rebate", "COALESCE(corporate_rebate, 0)", "SUM"),
            # 平台服务费（商品级字段，SUM聚合）
            AggregationField("total_platform_fee", "COALESCE(platform_service_fee, 0)", "SUM"),
            # 营销成本（订单级字段，MAX聚合）
            AggregationField("total_marketing_cost", 
                "COALESCE(full_reduction, 0) + COALESCE(product_discount, 0) + "
                "COALESCE(merchant_voucher, 0) + COALESCE(merchant_share, 0) + "
                "COALESCE(gift_amount, 0) + COALESCE(other_merchant_discount, 0) + "
                "COALESCE(new_customer_discount, 0)", "MAX", is_order_level=True),
            # GMV 相关字段
            AggregationField("gmv_original_price_sales", 
                "CASE WHEN COALESCE(original_price, 0) > 0 THEN COALESCE(original_price, 0) * COALESCE(quantity, 1) ELSE 0 END", "SUM"),
            AggregationField("gmv_packaging_fee", "COALESCE(packaging_fee, 0)", "MAX", is_order_level=True),
            AggregationField("gmv_user_delivery_fee", "COALESCE(user_paid_delivery_fee, 0)", "MAX", is_order_level=True),
        ],
        derived_fields=[
            DerivedField("avg_order_value", 
                "CASE WHEN order_count > 0 THEN total_revenue / order_count ELSE 0 END"),
            # 配送净成本 = 物流配送费 - 用户支付配送费 + 配送费减免金额 - 企客后返
            DerivedField("delivery_net_cost", 
                "total_delivery_fee - total_user_paid_delivery + total_delivery_discount - total_corporate_rebate"),
            # 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
            DerivedField("actual_profit",
                "total_profit - total_platform_fee - total_delivery_fee + total_corporate_rebate"),
            # 利润率（基于订单实际利润）
            DerivedField("profit_margin", 
                "CASE WHEN total_revenue > 0 THEN (total_profit - total_platform_fee - total_delivery_fee + total_corporate_rebate) / total_revenue * 100 ELSE 0 END"),
            # GMV = 商品原价销售额 + 打包袋金额 + 用户支付配送费
            DerivedField("gmv", 
                "gmv_original_price_sales + gmv_packaging_fee + gmv_user_delivery_fee"),
        ],
    ),
    
    # 门店小时汇总表
    "store_hourly_summary": AggregationConfig(
        table_name="store_hourly_summary",
        description="门店小时汇总（分时段分析）",
        group_by=["store_name", "DATE(date) as summary_date", "EXTRACT(HOUR FROM date)::INTEGER as hour_of_day", "channel"],
        fields=[
            AggregationField("order_count", "order_id", "COUNT_DISTINCT"),
            AggregationField("total_revenue", "COALESCE(actual_price, 0) * COALESCE(quantity, 1)", "SUM"),
            AggregationField("total_profit", "COALESCE(profit, 0)", "SUM"),
            AggregationField("total_delivery_fee", "COALESCE(delivery_fee, 0)", "MAX", is_order_level=True),
            AggregationField("delivery_net_cost", 
                "COALESCE(delivery_fee, 0) - COALESCE(user_paid_delivery_fee, 0) + COALESCE(delivery_discount, 0)", 
                "MAX", is_order_level=True),
            AggregationField("total_marketing_cost",
                "COALESCE(full_reduction, 0) + COALESCE(product_discount, 0) + "
                "COALESCE(merchant_voucher, 0) + COALESCE(merchant_share, 0) + "
                "COALESCE(gift_amount, 0) + COALESCE(other_merchant_discount, 0) + "
                "COALESCE(new_customer_discount, 0)", "MAX", is_order_level=True),
        ],
    ),
    
    # 品类日汇总表
    "category_daily_summary": AggregationConfig(
        table_name="category_daily_summary",
        description="品类日汇总（品类分析）",
        group_by=["store_name", "DATE(date) as summary_date", "category_level1", "category_level3", "channel"],
        fields=[
            AggregationField("order_count", "order_id", "COUNT_DISTINCT"),
            AggregationField("product_count", "product_name", "COUNT_DISTINCT"),
            AggregationField("total_quantity", "COALESCE(quantity, 1)", "SUM"),
            AggregationField("total_revenue", "COALESCE(actual_price, 0) * COALESCE(quantity, 1)", "SUM"),
            AggregationField("total_original_price", "COALESCE(original_price, 0) * COALESCE(quantity, 1)", "SUM"),
            AggregationField("total_cost", "COALESCE(cost, 0) * COALESCE(quantity, 1)", "SUM"),
            AggregationField("total_profit", "COALESCE(profit, 0)", "SUM"),
        ],
        derived_fields=[
            DerivedField("avg_discount",
                "CASE WHEN total_original_price > 0 THEN (1 - total_revenue / total_original_price) * 10 ELSE 0 END"),
            DerivedField("profit_margin",
                "CASE WHEN total_revenue > 0 THEN total_profit / total_revenue * 100 ELSE 0 END"),
        ],
        order_level_first=False,  # 品类分析不需要先按订单聚合
    ),
    
    # 配送分析汇总表
    "delivery_summary": AggregationConfig(
        table_name="delivery_summary",
        description="配送分析汇总（距离、时段分析）",
        group_by=[
            "store_name", 
            "DATE(date) as summary_date", 
            "EXTRACT(HOUR FROM date)::INTEGER as hour_of_day",
            """CASE 
                WHEN COALESCE(delivery_distance, 0) < 1 THEN '0-1km'
                WHEN COALESCE(delivery_distance, 0) < 2 THEN '1-2km'
                WHEN COALESCE(delivery_distance, 0) < 3 THEN '2-3km'
                WHEN COALESCE(delivery_distance, 0) < 4 THEN '3-4km'
                WHEN COALESCE(delivery_distance, 0) < 5 THEN '4-5km'
                ELSE '5km+'
            END as distance_band""",
            "channel"
        ],
        fields=[
            AggregationField("order_count", "order_id", "COUNT_DISTINCT"),
            AggregationField("total_revenue", "COALESCE(actual_price, 0) * COALESCE(quantity, 1)", "SUM"),
            AggregationField("delivery_net_cost",
                "COALESCE(delivery_fee, 0) - COALESCE(user_paid_delivery_fee, 0) + "
                "COALESCE(delivery_discount, 0) - COALESCE(corporate_rebate, 0)", "MAX", is_order_level=True),
            AggregationField("high_delivery_count",
                "CASE WHEN (COALESCE(delivery_fee, 0) - COALESCE(user_paid_delivery_fee, 0) + "
                "COALESCE(delivery_discount, 0) - COALESCE(corporate_rebate, 0)) > 5 THEN 1 ELSE 0 END", 
                "SUM", is_order_level=True),
        ],
        derived_fields=[
            DerivedField("avg_delivery_fee",
                "CASE WHEN order_count > 0 THEN delivery_net_cost / order_count ELSE 0 END"),
        ],
    ),
    
    # 商品日汇总表
    "product_daily_summary": AggregationConfig(
        table_name="product_daily_summary",
        description="商品日汇总（商品排行）",
        group_by=["store_name", "DATE(date) as summary_date", "product_name", "category_level1", "channel"],
        fields=[
            AggregationField("order_count", "order_id", "COUNT_DISTINCT"),
            AggregationField("total_quantity", "COALESCE(quantity, 1)", "SUM"),
            AggregationField("total_revenue", "COALESCE(actual_price, 0) * COALESCE(quantity, 1)", "SUM"),
            AggregationField("total_cost", "COALESCE(cost, 0) * COALESCE(quantity, 1)", "SUM"),
            AggregationField("total_profit", "COALESCE(profit, 0)", "SUM"),
        ],
        derived_fields=[
            DerivedField("avg_price",
                "CASE WHEN total_quantity > 0 THEN total_revenue / total_quantity ELSE 0 END"),
            DerivedField("profit_margin",
                "CASE WHEN total_revenue > 0 THEN total_profit / total_revenue * 100 ELSE 0 END"),
        ],
        order_level_first=False,
    ),
}


def get_all_table_names() -> List[str]:
    """获取所有预聚合表名"""
    return list(AGGREGATION_CONFIGS.keys())


def get_config(table_name: str) -> Optional[AggregationConfig]:
    """获取指定表的配置"""
    return AGGREGATION_CONFIGS.get(table_name)
