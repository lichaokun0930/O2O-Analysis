# 今日必做功能模块
# 版本: V2.0
# 创建日期: 2025-11-26
# 更新日期: 2025-11-27 - V2.0 完全重写
"""
今日必做功能模块
提供商品侧、运力侧、营销侧的智能分析和提醒

功能概述:
1. 商品侧: 波动预警(昨日vs前日)、滞销品监控(7/15/30天分级)
2. 运力侧: 配送异常订单、距离×时段热力图
3. 营销侧: 满减穿底订单、营销×配送交叉分析
"""

from .callbacks import (
    register_today_must_do_callbacks,
    create_today_must_do_layout
)

from .product_analysis import (
    analyze_product_fluctuation,
    analyze_slow_moving_products,
    get_product_insight,
    get_declining_products, 
    identify_slow_moving_products
)

from .delivery_analysis import (
    analyze_delivery_issues,
    create_delivery_heatmap_data,
    identify_delivery_issues, 
    get_delivery_summary_by_distance
)

from .marketing_analysis import (
    analyze_marketing_loss,
    analyze_activity_overlap,
    create_marketing_delivery_matrix,
    identify_discount_overflow_orders, 
    get_discount_analysis_by_range
)

__all__ = [
    # 回调注册
    'register_today_must_do_callbacks',
    'create_today_must_do_layout',
    
    # 商品分析 V2.0
    'analyze_product_fluctuation',
    'analyze_slow_moving_products',
    'get_product_insight',
    'get_declining_products',
    'identify_slow_moving_products',
    
    # 运力分析 V2.0
    'analyze_delivery_issues',
    'create_delivery_heatmap_data',
    'identify_delivery_issues',
    'get_delivery_summary_by_distance',
    
    # 营销分析 V2.0
    'analyze_marketing_loss',
    'analyze_activity_overlap',
    'create_marketing_delivery_matrix',
    'identify_discount_overflow_orders',
    'get_discount_analysis_by_range'
]
