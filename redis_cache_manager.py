#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Redis缓存管理模块
用于多用户场景下的数据缓存共享
"""

import redis
import pickle
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
import pandas as pd
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedisCacheManager:
    """Redis缓存管理器 - 支持多用户数据共享"""
    
    def __init__(
        self, 
        host: str = 'localhost', 
        port: int = 6379, 
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: int = 3600  # 默认1小时过期
    ):
        """
        初始化Redis连接
        
        Args:
            host: Redis服务器地址
            port: Redis端口
            db: 数据库编号
            password: 密码（如有）
            default_ttl: 默认过期时间（秒）
        """
        self.default_ttl = default_ttl
        self.enabled = False
        
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False,  # 保持二进制模式，用于pickle
                socket_connect_timeout=5,  # 增加超时时间到5秒
                socket_timeout=5,
                retry_on_timeout=True  # 超时自动重试
            )
            
            # 测试连接（增加重试逻辑）
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.client.ping()
                    self.enabled = True
                    logger.info(f"✅ Redis连接成功: {host}:{port}/{db}")
                    break
                except redis.TimeoutError:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ Redis连接超时，重试 {attempt + 1}/{max_retries}...")
                        import time
                        time.sleep(1)
                    else:
                        raise
            
        except redis.ConnectionError as e:
            logger.warning(f"⚠️  Redis连接失败，缓存功能已禁用: {e}")
            self.client = None
            self.enabled = False
        except Exception as e:
            logger.error(f"❌ Redis初始化错误: {e}")
            self.client = None
            self.enabled = False
    
    def _generate_key(self, prefix: str, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            prefix: 键前缀（如 'store_data', 'analysis_result'）
            **kwargs: 用于生成键的参数
            
        Returns:
            格式化的缓存键
        """
        # 对参数排序并序列化
        params_str = json.dumps(kwargs, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        
        return f"o2o_dashboard:{prefix}:{params_hash}"
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        compress: bool = True
    ) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值（支持DataFrame、dict等）
            ttl: 过期时间（秒），None使用默认值
            compress: 是否压缩（推荐DataFrame使用）
            
        Returns:
            是否成功
        """
        if not self.enabled:
            return False
        
        try:
            # 序列化数据
            if isinstance(value, pd.DataFrame):
                # DataFrame特殊处理
                serialized = pickle.dumps({
                    'type': 'dataframe',
                    'data': value.to_dict('records'),
                    'columns': value.columns.tolist(),
                    'index': value.index.tolist()
                })
            else:
                serialized = pickle.dumps({
                    'type': 'generic',
                    'data': value
                })
            
            # 设置缓存
            ttl = ttl or self.default_ttl
            self.client.setex(
                name=key,
                time=ttl,
                value=serialized
            )
            
            logger.info(f"✅ 缓存已保存: {key} (TTL={ttl}秒, 大小={len(serialized)/1024:.1f}KB)")
            return True
            
        except Exception as e:
            logger.error(f"❌ 缓存保存失败 {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在返回None
        """
        if not self.enabled:
            return None
        
        try:
            serialized = self.client.get(key)
            if serialized is None:
                logger.debug(f"⏭️  缓存未命中: {key}")
                return None
            
            # 反序列化
            data_obj = pickle.loads(serialized)
            
            if data_obj['type'] == 'dataframe':
                # 重建DataFrame
                df = pd.DataFrame(data_obj['data'], columns=data_obj['columns'])
                df.index = data_obj['index']
                logger.info(f"✅ 缓存命中: {key} (DataFrame {df.shape})")
                return df
            else:
                logger.info(f"✅ 缓存命中: {key}")
                return data_obj['data']
                
        except Exception as e:
            logger.error(f"❌ 缓存读取失败 {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.enabled:
            return False
        
        try:
            result = self.client.delete(key)
            logger.info(f"🗑️  缓存已删除: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"❌ 缓存删除失败 {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.enabled:
            return False
        
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"❌ 缓存检查失败 {key}: {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """获取缓存剩余时间（秒）"""
        if not self.enabled:
            return -1
        
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"❌ TTL查询失败 {key}: {e}")
            return -1
    
    def clear_pattern(self, pattern: str) -> int:
        """
        批量删除匹配的缓存
        
        Args:
            pattern: 键模式（支持通配符*）
            
        Returns:
            删除的键数量
        """
        if not self.enabled:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"🗑️  批量删除缓存: {pattern} ({deleted}个)")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"❌ 批量删除失败 {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.enabled:
            return {
                'enabled': False,
                'message': 'Redis未启用'
            }
        
        try:
            info = self.client.info('stats')
            memory = self.client.info('memory')
            
            return {
                'enabled': True,
                'total_keys': self.client.dbsize(),
                'used_memory_mb': round(memory.get('used_memory', 0) / 1024 / 1024, 2),
                'total_commands': info.get('total_commands_processed', 0),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'hit_rate': round(
                    info.get('keyspace_hits', 0) / 
                    max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100,
                    2
                )
            }
        except Exception as e:
            logger.error(f"❌ 统计信息获取失败: {e}")
            return {'enabled': False, 'error': str(e)}


# =============================================================================
# 缓存装饰器 - 自动缓存函数结果
# =============================================================================

def redis_cache(
    cache_manager: RedisCacheManager,
    key_prefix: str,
    ttl: Optional[int] = None,
    key_params: Optional[List[str]] = None
):
    """
    Redis缓存装饰器
    
    Args:
        cache_manager: Redis缓存管理器实例
        key_prefix: 缓存键前缀
        ttl: 过期时间（秒）
        key_params: 用于生成缓存键的参数名列表
        
    Example:
        @redis_cache(redis_manager, 'store_analysis', ttl=1800, key_params=['store_name', 'date'])
        def analyze_store(store_name, date):
            # 耗时计算...
            return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 如果Redis未启用，直接执行函数
            if not cache_manager.enabled:
                return func(*args, **kwargs)
            
            # 生成缓存键
            cache_params = {}
            if key_params:
                # 使用指定参数
                func_args = inspect.signature(func).parameters
                arg_names = list(func_args.keys())
                
                for i, param_name in enumerate(key_params):
                    if i < len(args):
                        cache_params[param_name] = args[i]
                    elif param_name in kwargs:
                        cache_params[param_name] = kwargs[param_name]
            else:
                # 使用所有参数
                cache_params = {
                    'args': str(args),
                    'kwargs': str(kwargs)
                }
            
            cache_key = cache_manager._generate_key(key_prefix, **cache_params)
            
            # 尝试从缓存读取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.info(f"🎯 缓存命中: {func.__name__}")
                return cached_result
            
            # 执行函数
            logger.info(f"⚙️  缓存未命中，执行计算: {func.__name__}")
            result = func(*args, **kwargs)
            
            # 保存到缓存
            cache_manager.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


# =============================================================================
# 预定义缓存管理器实例（单例模式）
# =============================================================================

# 全局缓存管理器实例
_global_cache_manager: Optional[RedisCacheManager] = None


def get_cache_manager(
    host: str = 'localhost',
    port: int = 6379,
    **kwargs
) -> RedisCacheManager:
    """
    获取全局缓存管理器实例（单例）
    
    Args:
        host: Redis服务器地址
        port: Redis端口
        **kwargs: 其他配置参数
        
    Returns:
        RedisCacheManager实例
    """
    global _global_cache_manager
    
    if _global_cache_manager is None:
        _global_cache_manager = RedisCacheManager(host=host, port=port, **kwargs)
    
    return _global_cache_manager


# =============================================================================
# 快捷函数 - 简化使用
# =============================================================================

def cache_dataframe(
    key: str,
    df: pd.DataFrame,
    ttl: int = 3600,
    cache_manager: Optional[RedisCacheManager] = None
) -> bool:
    """
    快捷缓存DataFrame
    
    Args:
        key: 缓存键
        df: DataFrame
        ttl: 过期时间（秒）
        cache_manager: 缓存管理器（可选）
        
    Returns:
        是否成功
    """
    manager = cache_manager or get_cache_manager()
    return manager.set(key, df, ttl=ttl)


def get_cached_dataframe(
    key: str,
    cache_manager: Optional[RedisCacheManager] = None
) -> Optional[pd.DataFrame]:
    """
    快捷获取缓存的DataFrame
    
    Args:
        key: 缓存键
        cache_manager: 缓存管理器（可选）
        
    Returns:
        DataFrame或None
    """
    manager = cache_manager or get_cache_manager()
    return manager.get(key)


def clear_store_cache(
    store_name: str,
    cache_manager: Optional[RedisCacheManager] = None
) -> int:
    """
    清除指定门店的所有缓存
    
    Args:
        store_name: 门店名称
        cache_manager: 缓存管理器（可选）
        
    Returns:
        删除的缓存数量
    """
    manager = cache_manager or get_cache_manager()
    pattern = f"o2o_dashboard:*:{store_name}*"
    return manager.clear_pattern(pattern)


# =============================================================================
# 测试和调试
# =============================================================================

if __name__ == "__main__":
    import inspect
    
    print("=" * 70)
    print(" Redis缓存管理器测试")
    print("=" * 70)
    
    # 初始化
    cache = RedisCacheManager(host='localhost', port=6379)
    
    if cache.enabled:
        print("\n1️⃣ 测试基本操作")
        
        # 设置缓存
        cache.set('test_key', {'data': 'test_value'}, ttl=60)
        
        # 获取缓存
        value = cache.get('test_key')
        print(f"   读取缓存: {value}")
        
        # TTL
        ttl = cache.get_ttl('test_key')
        print(f"   剩余时间: {ttl}秒")
        
        print("\n2️⃣ 测试DataFrame缓存")
        
        # 创建测试DataFrame
        test_df = pd.DataFrame({
            '商品': ['苹果', '香蕉', '橙子'],
            '销量': [100, 200, 150],
            '金额': [500, 600, 450]
        })
        
        # 缓存DataFrame
        cache_dataframe('test_df', test_df, ttl=300)
        
        # 读取DataFrame
        cached_df = get_cached_dataframe('test_df')
        print(f"\n   缓存的DataFrame:")
        print(cached_df)
        
        print("\n3️⃣ 缓存统计")
        stats = cache.get_stats()
        print(f"   总键数: {stats['total_keys']}")
        print(f"   内存使用: {stats['used_memory_mb']} MB")
        print(f"   命中率: {stats['hit_rate']}%")
        
        print("\n4️⃣ 清理测试缓存")
        cache.delete('test_key')
        cache.delete('test_df')
        print("   测试缓存已清理")
        
    else:
        print("\n⚠️  Redis未启用，跳过测试")
    
    print("\n" + "=" * 70)


# =============================================================================
# 🔧 导出全局缓存管理器实例（用于其他模块导入）
# =============================================================================
# 注意：实际的实例会在智能门店看板_Dash版.py中初始化
# 这里只是提供一个占位符，避免导入错误
REDIS_CACHE_MANAGER = None
