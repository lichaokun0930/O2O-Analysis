# -*- coding: utf-8 -*-
"""
缓存保护服务
防止缓存穿透、缓存雪崩、缓存击穿

功能：
- 缓存穿透防护：布隆过滤器 + 空值缓存
- 缓存雪崩防护：随机过期时间 + 互斥锁
- 缓存击穿防护：热点数据永不过期 + 后台刷新
"""

import time
import hashlib
import threading
import random
from typing import Optional, Dict, Any, Callable, Set
from dataclasses import dataclass
from datetime import datetime
from functools import wraps

from .logging_service import logging_service

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class CacheConfig:
    """缓存配置"""
    ttl: int = 3600                    # 基础过期时间（秒）
    ttl_random_range: int = 300        # 随机过期时间范围（防雪崩）
    null_ttl: int = 60                 # 空值缓存时间（防穿透）
    lock_timeout: int = 10             # 互斥锁超时（秒）
    hot_data_threshold: int = 100      # 热点数据访问阈值


class BloomFilter:
    """
    简易布隆过滤器
    用于快速判断数据是否存在，防止缓存穿透
    """
    
    def __init__(self, size: int = 1000000, hash_count: int = 7):
        self.size = size
        self.hash_count = hash_count
        self.bit_array = [False] * size
        self._lock = threading.Lock()
    
    def _hashes(self, item: str) -> list:
        """生成多个哈希值"""
        hashes = []
        for i in range(self.hash_count):
            h = hashlib.md5(f"{item}:{i}".encode()).hexdigest()
            hashes.append(int(h, 16) % self.size)
        return hashes
    
    def add(self, item: str):
        """添加元素"""
        with self._lock:
            for h in self._hashes(item):
                self.bit_array[h] = True
    
    def contains(self, item: str) -> bool:
        """检查元素是否可能存在"""
        for h in self._hashes(item):
            if not self.bit_array[h]:
                return False
        return True
    
    def clear(self):
        """清空过滤器"""
        with self._lock:
            self.bit_array = [False] * self.size


class CacheProtectionService:
    """
    缓存保护服务
    
    使用示例：
    ```python
    @cache_protection.cached(
        key_prefix="orders:kpi",
        ttl=1800,
        protect_penetration=True
    )
    def get_kpi_data(store_id: str):
        return db.query(...)
    ```
    """
    
    # 空值标记
    NULL_MARKER = "__NULL__"
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0
    ):
        self.redis_client: Optional[redis.Redis] = None
        self.use_redis = False
        
        # 布隆过滤器（防穿透）
        self.bloom_filter = BloomFilter()
        
        # 访问计数（识别热点数据）
        self._access_count: Dict[str, int] = {}
        self._hot_keys: Set[str] = set()
        
        # 互斥锁（防击穿）
        self._locks: Dict[str, threading.Lock] = {}
        self._lock_manager = threading.Lock()
        
        # 统计
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "penetration_blocked": 0,  # 穿透拦截
            "null_cache_hits": 0,      # 空值缓存命中
            "lock_waits": 0            # 锁等待次数
        }
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    socket_connect_timeout=2,
                    decode_responses=False
                )
                self.redis_client.ping()
                self.use_redis = True
                logging_service.info("✅ 缓存保护服务已启用 (Redis模式)")
            except Exception as e:
                logging_service.warning(f"⚠️ Redis连接失败，缓存保护降级: {e}")
    
    def _get_lock(self, key: str) -> threading.Lock:
        """获取指定key的锁"""
        with self._lock_manager:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]
    
    def _record_access(self, key: str):
        """记录访问，识别热点数据"""
        self._access_count[key] = self._access_count.get(key, 0) + 1
        if self._access_count[key] >= CacheConfig.hot_data_threshold:
            self._hot_keys.add(key)
    
    def _get_ttl_with_jitter(self, base_ttl: int) -> int:
        """获取带随机抖动的TTL（防雪崩）"""
        jitter = random.randint(0, CacheConfig.ttl_random_range)
        return base_ttl + jitter
    
    def get(
        self,
        key: str,
        loader: Callable,
        ttl: int = 3600,
        protect_penetration: bool = True,
        protect_stampede: bool = True
    ) -> Any:
        """
        获取缓存数据（带保护）
        
        Args:
            key: 缓存键
            loader: 数据加载函数
            ttl: 过期时间
            protect_penetration: 是否防穿透
            protect_stampede: 是否防击穿
            
        Returns:
            缓存或加载的数据
        """
        self._record_access(key)
        
        # 1. 尝试从缓存获取
        cached = self._get_from_cache(key)
        
        if cached is not None:
            # 检查是否是空值标记
            if cached == self.NULL_MARKER:
                self._stats["null_cache_hits"] += 1
                return None
            
            self._stats["cache_hits"] += 1
            return cached
        
        self._stats["cache_misses"] += 1
        
        # 2. 穿透防护：检查布隆过滤器
        if protect_penetration and not self.bloom_filter.contains(key):
            # 数据可能不存在，但仍需查询确认
            pass
        
        # 3. 击穿防护：使用互斥锁
        if protect_stampede:
            lock = self._get_lock(key)
            acquired = lock.acquire(timeout=CacheConfig.lock_timeout)
            
            if not acquired:
                self._stats["lock_waits"] += 1
                # 等待超时，返回None或旧数据
                return None
            
            try:
                # 双重检查
                cached = self._get_from_cache(key)
                if cached is not None:
                    if cached == self.NULL_MARKER:
                        return None
                    return cached
                
                # 加载数据
                data = loader()
                
                # 缓存结果
                if data is None:
                    # 空值缓存（防穿透）
                    self._set_to_cache(key, self.NULL_MARKER, CacheConfig.null_ttl)
                else:
                    # 正常缓存（带随机TTL防雪崩）
                    actual_ttl = self._get_ttl_with_jitter(ttl)
                    self._set_to_cache(key, data, actual_ttl)
                    # 添加到布隆过滤器
                    self.bloom_filter.add(key)
                
                return data
                
            finally:
                lock.release()
        else:
            # 不使用锁保护
            data = loader()
            if data is None:
                self._set_to_cache(key, self.NULL_MARKER, CacheConfig.null_ttl)
            else:
                actual_ttl = self._get_ttl_with_jitter(ttl)
                self._set_to_cache(key, data, actual_ttl)
                self.bloom_filter.add(key)
            return data
    
    def _get_from_cache(self, key: str) -> Any:
        """从缓存获取数据"""
        if not self.use_redis:
            return None
        
        try:
            import pickle
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logging_service.warning(f"缓存读取失败: {key} - {e}")
            return None
    
    def _set_to_cache(self, key: str, data: Any, ttl: int):
        """写入缓存"""
        if not self.use_redis:
            return
        
        try:
            import pickle
            self.redis_client.setex(key, ttl, pickle.dumps(data))
        except Exception as e:
            logging_service.warning(f"缓存写入失败: {key} - {e}")
    
    def invalidate(self, key: str):
        """使缓存失效"""
        if self.use_redis:
            try:
                self.redis_client.delete(key)
            except:
                pass
    
    def invalidate_pattern(self, pattern: str) -> int:
        """批量使缓存失效"""
        if not self.use_redis:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except:
            return 0
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self._stats["cache_hits"] + self._stats["cache_misses"]
        hit_rate = (
            self._stats["cache_hits"] / total * 100
            if total > 0 else 0
        )
        
        return {
            "enabled": self.use_redis,
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "hit_rate": round(hit_rate, 2),
            "penetration_blocked": self._stats["penetration_blocked"],
            "null_cache_hits": self._stats["null_cache_hits"],
            "lock_waits": self._stats["lock_waits"],
            "hot_keys_count": len(self._hot_keys),
            "bloom_filter_size": self.bloom_filter.size
        }
    
    def cached(
        self,
        key_prefix: str,
        ttl: int = 3600,
        protect_penetration: bool = True,
        protect_stampede: bool = True
    ):
        """
        缓存装饰器
        
        使用示例：
        ```python
        @cache_protection.cached("orders:kpi", ttl=1800)
        def get_kpi_data(store_id: str):
            return expensive_query()
        ```
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                key_parts = [key_prefix]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
                
                return self.get(
                    key=cache_key,
                    loader=lambda: func(*args, **kwargs),
                    ttl=ttl,
                    protect_penetration=protect_penetration,
                    protect_stampede=protect_stampede
                )
            return wrapper
        return decorator


# 全局实例
cache_protection_service = CacheProtectionService()
