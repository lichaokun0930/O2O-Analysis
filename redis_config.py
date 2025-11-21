#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis缓存配置
用于加速数据查询，减轻数据库压力
"""

import redis
import json
import hashlib
from functools import wraps
from datetime import datetime, timedelta
import pandas as pd

class RedisCache:
    """Redis缓存管理器"""
    
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        """
        初始化Redis连接
        
        Args:
            host: Redis主机地址
            port: Redis端口
            db: 数据库编号（0-15）
            password: 密码（如果设置了）
        """
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,  # 自动解码为字符串
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # 测试连接
            self.redis_client.ping()
            self.available = True
            print(f"✅ Redis连接成功: {host}:{port}")
        except Exception as e:
            print(f"⚠️ Redis连接失败: {e}")
            print("   将使用数据库直接查询（无缓存）")
            self.redis_client = None
            self.available = False
    
    def _generate_key(self, prefix, *args, **kwargs):
        """生成缓存键"""
        # 将参数转换为字符串并哈希
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]
        return f"{prefix}:{key_hash}"
    
    def get(self, key):
        """获取缓存"""
        if not self.available:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Redis GET错误: {e}")
        return None
    
    def set(self, key, value, expire=3600):
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值（会自动转为JSON）
            expire: 过期时间（秒），默认1小时
        """
        if not self.available:
            return False
        
        try:
            data = json.dumps(value, ensure_ascii=False, default=str)
            self.redis_client.setex(key, expire, data)
            return True
        except Exception as e:
            print(f"Redis SET错误: {e}")
            return False
    
    def delete(self, pattern):
        """删除匹配的缓存"""
        if not self.available:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Redis DELETE错误: {e}")
        return 0
    
    def clear_all(self):
        """清空所有缓存"""
        if not self.available:
            return False
        
        try:
            self.redis_client.flushdb()
            print("✅ Redis缓存已清空")
            return True
        except Exception as e:
            print(f"Redis FLUSH错误: {e}")
            return False
    
    def get_stats(self):
        """获取Redis统计信息"""
        if not self.available:
            return {"status": "不可用"}
        
        try:
            info = self.redis_client.info()
            return {
                "状态": "运行中",
                "已用内存": f"{info['used_memory_human']}",
                "键数量": info['db0']['keys'] if 'db0' in info else 0,
                "命中率": f"{info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1), 1) * 100:.1f}%"
            }
        except Exception as e:
            return {"错误": str(e)}


def cache_dataframe(cache_manager, prefix, expire=3600):
    """
    装饰器：缓存DataFrame查询结果
    
    使用示例:
    @cache_dataframe(redis_cache, 'orders', expire=1800)
    def get_orders(date_range, store_id):
        return pd.read_sql(...)
    
    Args:
        cache_manager: RedisCache实例
        prefix: 缓存键前缀
        expire: 过期时间（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_data = cache_manager.get(cache_key)
            if cached_data is not None:
                print(f"🚀 从Redis缓存读取: {prefix}")
                return pd.DataFrame(cached_data)
            
            # 缓存未命中，执行函数
            print(f"💾 从数据库查询: {prefix}")
            result = func(*args, **kwargs)
            
            # 存入缓存（DataFrame转dict）
            if isinstance(result, pd.DataFrame):
                cache_manager.set(
                    cache_key,
                    result.to_dict('records'),
                    expire=expire
                )
            
            return result
        return wrapper
    return decorator


# 全局Redis实例
redis_cache = RedisCache(
    host='localhost',
    port=6379,
    db=0
)


# 使用示例
if __name__ == "__main__":
    # 测试连接
    print("\n=== Redis缓存测试 ===\n")
    
    # 测试基本操作
    test_data = {"name": "测试", "value": 123}
    redis_cache.set("test_key", test_data, expire=60)
    result = redis_cache.get("test_key")
    print(f"写入测试: {test_data}")
    print(f"读取测试: {result}")
    
    # 测试装饰器
    @cache_dataframe(redis_cache, 'test_df', expire=300)
    def get_test_data(param):
        print(f"  → 执行数据库查询（参数: {param}）")
        return pd.DataFrame({
            'A': [1, 2, 3],
            'B': ['a', 'b', 'c']
        })
    
    print("\n第一次调用（会查询数据库）:")
    df1 = get_test_data("test")
    print(df1)
    
    print("\n第二次调用（从缓存读取）:")
    df2 = get_test_data("test")
    print(df2)
    
    # 统计信息
    print("\n=== Redis统计信息 ===")
    stats = redis_cache.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
