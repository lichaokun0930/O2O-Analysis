# -*- coding: utf-8 -*-
"""
缓存键定义

统一管理所有Service的缓存键，避免键冲突
"""

import hashlib
from typing import Any, Optional


class CacheKeys:
    """缓存键管理器"""
    
    # 命名空间前缀，与O2O比价看板隔离
    NAMESPACE = "order_dashboard"
    
    # ==================== 订单分析缓存键 ====================
    class Order:
        PREFIX = "order"
        
        @classmethod
        def kpi(cls, store_name: Optional[str] = None, date_range: Optional[str] = None) -> str:
            """KPI指标缓存键"""
            parts = [CacheKeys.NAMESPACE, cls.PREFIX, "kpi"]
            if store_name:
                parts.append(f"store_{store_name}")
            if date_range:
                parts.append(f"range_{date_range}")
            return ":".join(parts)
        
        @classmethod
        def trend(cls, days: int, store_name: Optional[str] = None) -> str:
            """趋势数据缓存键"""
            parts = [CacheKeys.NAMESPACE, cls.PREFIX, "trend", f"days_{days}"]
            if store_name:
                parts.append(f"store_{store_name}")
            return ":".join(parts)
        
        @classmethod
        def by_channel(cls, store_name: Optional[str] = None) -> str:
            """渠道分析缓存键"""
            parts = [CacheKeys.NAMESPACE, cls.PREFIX, "by_channel"]
            if store_name:
                parts.append(f"store_{store_name}")
            return ":".join(parts)
    
    # ==================== 诊断分析缓存键 ====================
    class Diagnosis:
        PREFIX = "diagnosis"
        
        @classmethod
        def summary(cls, store_name: Optional[str] = None, date: Optional[str] = None) -> str:
            """诊断汇总缓存键"""
            parts = [CacheKeys.NAMESPACE, cls.PREFIX, "summary"]
            if store_name:
                parts.append(f"store_{store_name}")
            if date:
                parts.append(f"date_{date}")
            return ":".join(parts)
        
        @classmethod
        def overflow_orders(cls, threshold: float = 0) -> str:
            """穿底订单缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:overflow_orders:threshold_{threshold}"
        
        @classmethod
        def overflow_products(cls) -> str:
            """穿底商品缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:overflow_products"
        
        @classmethod
        def high_delivery(cls, threshold: float = 6.0) -> str:
            """高配送费缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:high_delivery:threshold_{threshold}"
        
        @classmethod
        def stockout(cls, threshold: int = 5) -> str:
            """缺货预警缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:stockout:threshold_{threshold}"
        
        @classmethod
        def traffic_drop(cls, drop_threshold: float = 0.3) -> str:
            """流量下滑缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:traffic_drop:threshold_{drop_threshold}"
        
        @classmethod
        def slow_moving(cls, days: int = 30) -> str:
            """滞销商品缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:slow_moving:days_{days}"
        
        @classmethod
        def price_abnormal(cls) -> str:
            """价格异常缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:price_abnormal"
        
        @classmethod
        def customer_churn(cls, lookback_days: int = 30) -> str:
            """客户流失缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:customer_churn:days_{lookback_days}"
        
        @classmethod
        def aov_anomaly(cls) -> str:
            """客单价异常缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:aov_anomaly"
    
    # ==================== 商品分析缓存键 ====================
    class Product:
        PREFIX = "product"
        
        @classmethod
        def ranking(cls, sort_by: str, top_n: int) -> str:
            """商品排行缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:ranking:{sort_by}:top_{top_n}"
        
        @classmethod
        def category_analysis(cls) -> str:
            """分类分析缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:category_analysis"
        
        @classmethod
        def inventory(cls) -> str:
            """库存分析缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:inventory"
        
        @classmethod
        def hot_products(cls, top_n: int = 10) -> str:
            """热销商品缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:hot:top_{top_n}"
        
        @classmethod
        def high_profit(cls, top_n: int = 10) -> str:
            """高利润商品缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:high_profit:top_{top_n}"
    
    # ==================== 营销分析缓存键 ====================
    class Marketing:
        PREFIX = "marketing"
        
        @classmethod
        def loss_analysis(cls) -> str:
            """营销损失分析缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:loss_analysis"
        
        @classmethod
        def activity_overlap(cls) -> str:
            """活动重叠分析缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:activity_overlap"
        
        @classmethod
        def discount_analysis(cls) -> str:
            """折扣分析缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:discount_analysis"
    
    # ==================== 配送分析缓存键 ====================
    class Delivery:
        PREFIX = "delivery"
        
        @classmethod
        def issues(cls, threshold: float = 6.0) -> str:
            """配送问题缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:issues:threshold_{threshold}"
        
        @classmethod
        def heatmap(cls) -> str:
            """配送热力图缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:heatmap"
        
        @classmethod
        def by_distance(cls) -> str:
            """按距离分析缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:by_distance"
    
    # ==================== 场景分析缓存键 ====================
    class Scene:
        PREFIX = "scene"
        
        @classmethod
        def analysis(cls) -> str:
            """场景分析缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:analysis"
        
        @classmethod
        def time_period(cls) -> str:
            """时段分析缓存键"""
            return f"{CacheKeys.NAMESPACE}:{cls.PREFIX}:time_period"
    
    # ==================== 工具方法 ====================
    
    @staticmethod
    def hash_params(*args, **kwargs) -> str:
        """将参数哈希为短字符串，用于构建缓存键"""
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()[:12]
    
    @staticmethod
    def build_key(prefix: str, *args, **kwargs) -> str:
        """构建通用缓存键"""
        parts = [CacheKeys.NAMESPACE, prefix]
        parts.extend([str(arg) for arg in args])
        if kwargs:
            parts.append(CacheKeys.hash_params(**kwargs))
        return ":".join(parts)

