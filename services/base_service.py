# -*- coding: utf-8 -*-
"""
基础服务类

提供所有Service的公共功能：
- 缓存集成
- 日志记录
- 错误处理
- 数据验证

版本: v1.0
创建日期: 2026-01-05
"""

import logging
import hashlib
import pandas as pd
import numpy as np
from typing import Any, Optional, Dict, List, Tuple, Callable
from datetime import datetime, date
from functools import wraps

from .cache.hierarchical_cache_adapter import OrderDashboardCacheManager, get_cache_manager
from .cache.cache_keys import CacheKeys

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cache_result(cache_key_func: Callable, ttl: int = 300, level: int = 4):
    """
    缓存装饰器
    
    Args:
        cache_key_func: 生成缓存键的函数，接收与被装饰函数相同的参数
        ttl: 缓存过期时间（秒）
        level: 缓存层级
    
    Usage:
        @cache_result(lambda self, df, top_n: f"hot_products:{top_n}", ttl=600)
        def get_hot_products(self, df, top_n=10):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 检查缓存是否可用
            if not hasattr(self, 'cache') or self.cache is None:
                return func(self, *args, **kwargs)
            
            # 生成缓存键
            try:
                cache_key = cache_key_func(self, *args, **kwargs)
            except Exception:
                return func(self, *args, **kwargs)
            
            # 尝试从缓存获取
            cached = self.cache.get(cache_key, level=level)
            if cached is not None:
                logger.debug(f"🚀 缓存命中: {cache_key}")
                return cached
            
            # 执行函数
            result = func(self, *args, **kwargs)
            
            # 写入缓存
            if result is not None:
                self.cache.set(cache_key, result, level=level, ttl=ttl)
                logger.debug(f"💾 写入缓存: {cache_key}")
            
            return result
        return wrapper
    return decorator


class BaseService:
    """
    基础服务类
    
    所有Service的基类，提供公共功能
    """
    
    # ==================== 字段级别定义（与主看板保持一致）====================
    # 订单级字段 - 使用 first() 聚合
    ORDER_LEVEL_FIELDS = [
        '物流配送费',
        '满减金额',
        '商品减免金额',
        '商家代金券',
        '商家承担部分券',
        '满赠金额',
        '商家其他优惠',
        '新客减免金额',
        '用户支付配送费',
        '配送费减免金额',
        '渠道',
        '平台',
        '门店',
        '下单时间',
        '日期',
    ]
    
    # 商品级字段 - 使用 sum() 聚合
    ITEM_LEVEL_FIELDS = [
        '利润额',
        '平台服务费',
        '企客后返',
        '实收价格',
        '商品实售价',
        '商品采购成本',
        '成本',
        '月售',
        '销量',
    ]
    
    def __init__(self, cache_manager: Optional[OrderDashboardCacheManager] = None):
        """
        初始化基础服务
        
        Args:
            cache_manager: 缓存管理器实例，为None时使用全局实例
        """
        self.cache = cache_manager or get_cache_manager()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    # ==================== 缓存相关方法 ====================
    
    def cache_get(self, key: str, level: int = 4) -> Optional[Any]:
        """获取缓存"""
        if self.cache:
            return self.cache.get(key, level=level)
        return None
    
    def cache_set(self, key: str, value: Any, level: int = 4, ttl: int = 300) -> bool:
        """设置缓存"""
        if self.cache:
            return self.cache.set(key, value, level=level, ttl=ttl)
        return False
    
    def cache_delete(self, key: str, level: int = 4) -> bool:
        """删除缓存"""
        if self.cache:
            return self.cache.delete(key, level=level)
        return False
    
    def _build_cache_key(self, prefix: str, df: pd.DataFrame = None, *args, **kwargs) -> str:
        """
        构建缓存键
        
        Args:
            prefix: 键前缀
            df: DataFrame（用于计算数据哈希）
            *args, **kwargs: 其他参数
        
        Returns:
            缓存键字符串
        """
        parts = [prefix]
        
        # 添加DataFrame哈希
        if df is not None and len(df) > 0:
            data_hash = hashlib.md5(
                pd.util.hash_pandas_object(df.head(100)).values.tobytes()
            ).hexdigest()[:8]
            parts.append(f"data_{data_hash}")
            parts.append(f"rows_{len(df)}")
        
        # 添加其他参数
        for arg in args:
            if arg is not None:
                parts.append(str(arg))
        
        for key, value in sorted(kwargs.items()):
            if value is not None:
                parts.append(f"{key}_{value}")
        
        return ":".join(parts)
    
    # ==================== 数据处理工具方法 ====================
    
    def get_date_column(self, df: pd.DataFrame) -> Optional[str]:
        """获取日期列名"""
        for col in ['日期', '下单时间', 'date', 'order_date']:
            if col in df.columns:
                return col
        return None
    
    def get_base_date(self, df: pd.DataFrame) -> Optional[pd.Timestamp]:
        """获取基准日期（昨日 = 数据最后一天）"""
        date_col = self.get_date_column(df)
        if date_col is None:
            return None
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        return df[date_col].max().normalize()
    
    def get_sales_column(self, df: pd.DataFrame) -> str:
        """获取销量列名"""
        return '月售' if '月售' in df.columns else '销量'
    
    def get_product_group_key(self, df: pd.DataFrame) -> str:
        """
        获取商品聚合的key字段名
        
        优先级：店内码 > 条码 > 商品名称
        使用店内码可以区分同名但不同规格的商品
        """
        if '店内码' in df.columns and df['店内码'].notna().any():
            return '店内码'
        elif '条码' in df.columns and df['条码'].notna().any():
            return '条码'
        else:
            return '商品名称'
    
    def calculate_order_profit(self, order_agg: pd.DataFrame) -> pd.Series:
        """
        计算订单实际利润（与主看板公式完全一致）
        
        公式: 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
        
        Args:
            order_agg: 订单级聚合后的DataFrame
        
        Returns:
            Series: 订单实际利润
        """
        # 获取必需字段
        profit = order_agg.get('利润额', pd.Series(0, index=order_agg.index))
        delivery_fee = order_agg.get('物流配送费', pd.Series(0, index=order_agg.index))
        
        # 获取可选字段
        service_fee = order_agg.get('平台服务费', pd.Series(0, index=order_agg.index))
        enterprise_rebate = order_agg.get('企客后返', pd.Series(0, index=order_agg.index))
        
        # 处理NaN
        profit = profit.fillna(0)
        delivery_fee = delivery_fee.fillna(0)
        service_fee = service_fee.fillna(0)
        enterprise_rebate = enterprise_rebate.fillna(0)
        
        # 计算订单实际利润
        result = profit - service_fee - delivery_fee + enterprise_rebate
        
        return result
    
    def aggregate_to_order_level(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        将商品级数据聚合到订单级
        
        使用正确的聚合方式：
        - 订单级字段用 first()
        - 商品级字段用 sum()
        
        Args:
            df: 商品级明细数据
        
        Returns:
            订单级聚合数据
        """
        if '订单ID' not in df.columns:
            self.logger.warning("缺少订单ID字段，无法聚合")
            return df
        
        agg_dict = {}
        
        # 订单级字段
        for field in self.ORDER_LEVEL_FIELDS:
            if field in df.columns:
                agg_dict[field] = 'first'
        
        # 商品级字段
        for field in self.ITEM_LEVEL_FIELDS:
            if field in df.columns:
                agg_dict[field] = 'sum'
        
        # 保留商品名称（用于展示）
        if '商品名称' in df.columns:
            agg_dict['商品名称'] = lambda x: ', '.join(x.head(3).astype(str))
        
        # 商品数量
        agg_dict['商品数量'] = ('商品名称', 'count') if '商品名称' in df.columns else ('订单ID', 'count')
        
        # 执行聚合
        result = df.groupby('订单ID').agg(agg_dict).reset_index()
        
        # 计算订单实际利润
        result['订单实际利润'] = self.calculate_order_profit(result)
        
        return result
    
    def get_channel_distribution(self, df: pd.DataFrame, mask: pd.Series = None) -> Dict[str, int]:
        """获取渠道分布"""
        channel_col = next((c for c in ['平台', '渠道', 'platform', 'channel'] if c in df.columns), None)
        if channel_col is None:
            return {}
        
        if mask is not None:
            df = df[mask]
        
        return df[channel_col].value_counts().to_dict()
    
    def clean_for_json(self, obj: Any) -> Any:
        """
        清理数据以便JSON序列化
        
        处理NaN、Inf、numpy类型等
        """
        if isinstance(obj, dict):
            return {k: self.clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.clean_for_json(item) for item in obj]
        elif isinstance(obj, pd.DataFrame):
            return obj.replace([np.inf, -np.inf], np.nan).fillna(0).to_dict('records')
        elif isinstance(obj, pd.Series):
            return obj.replace([np.inf, -np.inf], np.nan).fillna(0).to_list()
        elif isinstance(obj, (np.integer, np.floating)):
            if np.isnan(obj) or np.isinf(obj):
                return 0
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return self.clean_for_json(obj.tolist())
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    # ==================== 错误处理 ====================
    
    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        统一错误处理
        
        Args:
            error: 异常对象
            context: 错误上下文描述
        
        Returns:
            错误信息字典
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(error_msg)
        
        return {
            'error': error_msg,
            'success': False,
            'data': None
        }
    
    def validate_dataframe(self, df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, str]:
        """
        验证DataFrame是否包含必需列
        
        Args:
            df: 待验证的DataFrame
            required_columns: 必需列列表
        
        Returns:
            (是否有效, 错误消息)
        """
        if df is None or df.empty:
            return False, "数据为空"
        
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            return False, f"缺少必需列: {', '.join(missing)}"
        
        return True, ""

