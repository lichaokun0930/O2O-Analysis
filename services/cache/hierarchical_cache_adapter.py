# -*- coding: utf-8 -*-
"""
四级分层缓存管理器适配层

复用现有 hierarchical_cache_manager.py，增加命名空间隔离
与O2O比价看板共用Redis实例，通过DB和命名空间隔离

缓存层级:
- Level 1: 原始数据缓存（按门店分片）
- Level 2: 聚合指标缓存（按门店+日期）
- Level 3: 诊断结果缓存（按门店组合）
- Level 4: 热点数据缓存（LRU自动管理）

版本: v1.0
创建日期: 2026-01-05
"""

import sys
from pathlib import Path
from typing import Any, Optional

# 添加父目录到路径以导入hierarchical_cache_manager
APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

try:
    from hierarchical_cache_manager import HierarchicalCacheManager
    HIERARCHICAL_CACHE_AVAILABLE = True
except ImportError:
    HIERARCHICAL_CACHE_AVAILABLE = False
    print("⚠️ hierarchical_cache_manager 未找到，将使用简单缓存")


class OrderDashboardCacheManager:
    """
    订单数据看板专用缓存管理器
    
    继承四级分层缓存架构，增加命名空间隔离
    """
    
    # 命名空间前缀，与O2O比价看板隔离
    NAMESPACE = "order_dashboard"
    
    # 缓存层级定义
    LEVEL_RAW_DATA = 1      # 原始数据（按门店）
    LEVEL_METRICS = 2       # 聚合指标（按门店+日期）
    LEVEL_DIAGNOSIS = 3     # 诊断结果（按门店组合）
    LEVEL_HOTSPOT = 4       # 热点数据（LRU）
    
    # 默认TTL（秒）
    DEFAULT_TTL = {
        1: 3600,    # 原始数据: 1小时
        2: 1800,    # 聚合指标: 30分钟
        3: 600,     # 诊断结果: 10分钟
        4: 300,     # 热点数据: 5分钟
    }
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 1,  # 使用DB 1，与O2O(DB 0)隔离
        password: Optional[str] = None,
        max_memory_mb: int = 512,
        enable_compression: bool = True
    ):
        """
        初始化缓存管理器
        
        Args:
            host: Redis服务器地址
            port: Redis端口
            db: 数据库编号（默认1，与O2O的0隔离）
            password: 密码
            max_memory_mb: 最大内存限制（MB）
            enable_compression: 是否启用压缩
        """
        self.enabled = False
        self._cache = None
        
        if HIERARCHICAL_CACHE_AVAILABLE:
            try:
                self._cache = HierarchicalCacheManager(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    max_memory_mb=max_memory_mb,
                    enable_compression=enable_compression
                )
                self.enabled = self._cache.enabled
                if self.enabled:
                    print(f"✅ 订单看板四级缓存初始化成功 (DB={db}, 命名空间={self.NAMESPACE})")
            except Exception as e:
                print(f"⚠️ 四级缓存初始化失败: {e}")
        else:
            print("⚠️ 使用内存缓存作为后备")
            self._memory_cache = {}
    
    def _build_key(self, level: int, key: str) -> str:
        """构建带命名空间的缓存键"""
        return f"{self.NAMESPACE}:L{level}:{key}"
    
    # ==================== 基础操作 ====================
    
    def get(self, key: str, level: int = 4) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            level: 缓存层级
        
        Returns:
            缓存值，未命中返回None
        """
        full_key = self._build_key(level, key)
        
        if self._cache and self.enabled:
            return self._cache.get(full_key)
        elif hasattr(self, '_memory_cache'):
            return self._memory_cache.get(full_key)
        return None
    
    def set(self, key: str, value: Any, level: int = 4, ttl: Optional[int] = None) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            level: 缓存层级
            ttl: 过期时间（秒），默认根据层级自动设置
        
        Returns:
            是否成功
        """
        full_key = self._build_key(level, key)
        if ttl is None:
            ttl = self.DEFAULT_TTL.get(level, 300)
        
        if self._cache and self.enabled:
            return self._cache.set(full_key, value, expire=ttl)
        elif hasattr(self, '_memory_cache'):
            self._memory_cache[full_key] = value
            return True
        return False
    
    def delete(self, key: str, level: int = 4) -> bool:
        """删除缓存"""
        full_key = self._build_key(level, key)
        
        if self._cache and self.enabled:
            return self._cache.delete(full_key) > 0
        elif hasattr(self, '_memory_cache'):
            return self._memory_cache.pop(full_key, None) is not None
        return False
    
    def clear_level(self, level: int) -> int:
        """清空指定层级的所有缓存"""
        pattern = self._build_key(level, "*")
        
        if self._cache and self.enabled:
            return self._cache.delete(pattern)
        elif hasattr(self, '_memory_cache'):
            prefix = self._build_key(level, "")
            keys_to_delete = [k for k in self._memory_cache if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._memory_cache[k]
            return len(keys_to_delete)
        return 0
    
    def clear_all(self) -> bool:
        """清空订单看板所有缓存"""
        pattern = f"{self.NAMESPACE}:*"
        
        if self._cache and self.enabled:
            return self._cache.delete(pattern) > 0
        elif hasattr(self, '_memory_cache'):
            self._memory_cache.clear()
            return True
        return False
    
    # ==================== 分层便捷方法 ====================
    
    def get_raw_data(self, key: str) -> Optional[Any]:
        """获取原始数据缓存（Level 1）"""
        return self.get(key, level=self.LEVEL_RAW_DATA)
    
    def set_raw_data(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置原始数据缓存（Level 1）"""
        return self.set(key, value, level=self.LEVEL_RAW_DATA, ttl=ttl)
    
    def get_metrics(self, key: str) -> Optional[Any]:
        """获取聚合指标缓存（Level 2）"""
        return self.get(key, level=self.LEVEL_METRICS)
    
    def set_metrics(self, key: str, value: Any, ttl: int = 1800) -> bool:
        """设置聚合指标缓存（Level 2）"""
        return self.set(key, value, level=self.LEVEL_METRICS, ttl=ttl)
    
    def get_diagnosis(self, key: str) -> Optional[Any]:
        """获取诊断结果缓存（Level 3）"""
        return self.get(key, level=self.LEVEL_DIAGNOSIS)
    
    def set_diagnosis(self, key: str, value: Any, ttl: int = 600) -> bool:
        """设置诊断结果缓存（Level 3）"""
        return self.set(key, value, level=self.LEVEL_DIAGNOSIS, ttl=ttl)
    
    def get_hotspot(self, key: str) -> Optional[Any]:
        """获取热点数据缓存（Level 4）"""
        return self.get(key, level=self.LEVEL_HOTSPOT)
    
    def set_hotspot(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置热点数据缓存（Level 4）"""
        return self.set(key, value, level=self.LEVEL_HOTSPOT, ttl=ttl)
    
    # ==================== 统计信息 ====================
    
    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        if self._cache and self.enabled:
            stats = self._cache.get_stats() if hasattr(self._cache, 'get_stats') else {}
            stats['namespace'] = self.NAMESPACE
            stats['enabled'] = True
            return stats
        elif hasattr(self, '_memory_cache'):
            return {
                'namespace': self.NAMESPACE,
                'enabled': False,
                'type': 'memory',
                'keys': len(self._memory_cache)
            }
        return {'namespace': self.NAMESPACE, 'enabled': False}


# 全局缓存实例（懒加载）
_cache_instance: Optional[OrderDashboardCacheManager] = None


def get_cache_manager() -> OrderDashboardCacheManager:
    """获取全局缓存管理器实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = OrderDashboardCacheManager()
    return _cache_instance

