# -*- coding: utf-8 -*-
"""
分层缓存管理器 - V8.4 企业级扩展

四级缓存架构:
Level 1: 原始数据缓存（按门店分片）
Level 2: 聚合指标缓存（按门店+日期）
Level 3: 诊断结果缓存（按门店组合）
Level 4: 热点数据缓存（LRU自动管理）

设计理念:
- 分层存储，增量计算
- 智能预热，按需加载
- 压缩存储，节省内存
- 热点优先，LRU淘汰

作者: AI Assistant
版本: V8.4
日期: 2025-12-11
"""

import redis
import pickle
import gzip
import hashlib
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Tuple
import logging
from collections import defaultdict

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HierarchicalCacheManager:
    """分层缓存管理器 - 支持100+门店、百万级数据"""
    
    # 缓存层级定义
    LEVEL_RAW_DATA = 1      # 原始数据（按门店）
    LEVEL_METRICS = 2       # 聚合指标（按门店+日期）
    LEVEL_DIAGNOSIS = 3     # 诊断结果（按门店组合）
    LEVEL_HOTSPOT = 4       # 热点数据（LRU）
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_memory_mb: int = 1024,  # 默认1GB，适合100家门店
        enable_compression: bool = True
    ):
        """
        初始化分层缓存管理器
        
        Args:
            host: Redis服务器地址
            port: Redis端口
            db: 数据库编号
            password: 密码
            max_memory_mb: 最大内存限制（MB）
            enable_compression: 是否启用压缩
        """
        self.enable_compression = enable_compression
        self.enabled = False
        self.access_log = []  # 访问日志（用于热点分析）
        
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # 测试连接
            self.client.ping()
            self.enabled = True
            
            # 配置内存限制和淘汰策略
            try:
                self.client.config_set('maxmemory', f'{max_memory_mb}mb')
                self.client.config_set('maxmemory-policy', 'allkeys-lru')
                logger.info(f"✅ Redis配置成功: maxmemory={max_memory_mb}MB, policy=allkeys-lru")
            except Exception as e:
                logger.warning(f"⚠️ Redis配置失败（可能需要管理员权限）: {e}")
            
            logger.info(f"✅ 分层缓存管理器初始化成功: {host}:{port}/{db}")
            
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}")
            self.client = None
            self.enabled = False
    
    def _generate_key(self, level: int, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            level: 缓存层级
            **kwargs: 键参数
            
        Returns:
            格式化的缓存键
        """
        # 对参数排序并序列化
        params_str = json.dumps(kwargs, sort_keys=True, default=str)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:12]
        
        level_names = {
            1: 'raw',
            2: 'metrics',
            3: 'diagnosis',
            4: 'hotspot'
        }
        level_name = level_names.get(level, 'unknown')
        
        return f"o2o:v8.4:{level_name}:{params_hash}"
    
    def _compress(self, data: bytes) -> bytes:
        """压缩数据"""
        if not self.enable_compression:
            return data
        return gzip.compress(data, compresslevel=6)
    
    def _decompress(self, data: bytes) -> bytes:
        """解压数据"""
        if not self.enable_compression:
            return data
        try:
            return gzip.decompress(data)
        except:
            # 可能是未压缩的旧数据
            return data
    
    def _serialize(self, value: Any) -> bytes:
        """序列化数据"""
        if isinstance(value, pd.DataFrame):
            # DataFrame特殊处理（更紧凑）
            return pickle.dumps({
                'type': 'dataframe',
                'data': value.to_dict('tight'),  # tight格式更紧凑
            }, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            return pickle.dumps({
                'type': 'generic',
                'data': value
            }, protocol=pickle.HIGHEST_PROTOCOL)
    
    def _deserialize(self, data: bytes) -> Any:
        """反序列化数据"""
        obj = pickle.loads(data)
        if obj['type'] == 'dataframe':
            return pd.DataFrame.from_dict(obj['data'], orient='tight')
        else:
            return obj['data']
    
    # ========== Level 1: 原始数据缓存 ==========
    
    def cache_raw_data(
        self,
        store_id: str,
        date_range: Tuple[str, str],
        data: pd.DataFrame,
        ttl: int = 86400  # 24小时
    ) -> bool:
        """
        缓存原始数据（按门店分片）
        
        Args:
            store_id: 门店ID
            date_range: 日期范围 (start, end)
            data: 原始数据
            ttl: 过期时间（秒）
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_key(
                self.LEVEL_RAW_DATA,
                store_id=store_id,
                date_range=date_range
            )
            
            # 序列化并压缩
            serialized = self._serialize(data)
            compressed = self._compress(serialized)
            
            # 存储
            self.client.setex(key, ttl, compressed)
            
            compression_ratio = len(compressed) / len(serialized) * 100
            logger.info(
                f"✅ [L1] 原始数据已缓存: store={store_id}, "
                f"size={len(compressed)/1024:.1f}KB, "
                f"compression={compression_ratio:.1f}%"
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ [L1] 缓存失败: {e}")
            return False
    
    def get_raw_data(
        self,
        store_id: str,
        date_range: Tuple[str, str]
    ) -> Optional[pd.DataFrame]:
        """获取原始数据"""
        if not self.enabled:
            return None
        
        try:
            key = self._generate_key(
                self.LEVEL_RAW_DATA,
                store_id=store_id,
                date_range=date_range
            )
            
            compressed = self.client.get(key)
            if compressed is None:
                return None
            
            # 解压并反序列化
            serialized = self._decompress(compressed)
            data = self._deserialize(serialized)
            
            logger.info(f"✅ [L1] 原始数据命中: store={store_id}")
            return data
            
        except Exception as e:
            logger.error(f"❌ [L1] 读取失败: {e}")
            return None
    
    # ========== Level 2: 聚合指标缓存 ==========
    
    def cache_metrics(
        self,
        store_id: str,
        date: str,
        metrics: Dict[str, Any],
        ttl: int = 21600  # 6小时
    ) -> bool:
        """
        缓存聚合指标（按门店+日期）
        
        Args:
            store_id: 门店ID
            date: 日期
            metrics: 聚合指标字典
            ttl: 过期时间（秒）
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_key(
                self.LEVEL_METRICS,
                store_id=store_id,
                date=date
            )
            
            # 序列化并压缩
            serialized = self._serialize(metrics)
            compressed = self._compress(serialized)
            
            # 存储
            self.client.setex(key, ttl, compressed)
            
            logger.info(f"✅ [L2] 指标已缓存: store={store_id}, date={date}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [L2] 缓存失败: {e}")
            return False
    
    def get_metrics(
        self,
        store_id: str,
        date: str
    ) -> Optional[Dict[str, Any]]:
        """获取聚合指标"""
        if not self.enabled:
            return None
        
        try:
            key = self._generate_key(
                self.LEVEL_METRICS,
                store_id=store_id,
                date=date
            )
            
            compressed = self.client.get(key)
            if compressed is None:
                return None
            
            # 解压并反序列化
            serialized = self._decompress(compressed)
            metrics = self._deserialize(serialized)
            
            logger.info(f"✅ [L2] 指标命中: store={store_id}, date={date}")
            return metrics
            
        except Exception as e:
            logger.error(f"❌ [L2] 读取失败: {e}")
            return None
    
    def get_metrics_batch(
        self,
        store_ids: List[str],
        date: str
    ) -> Dict[str, Dict[str, Any]]:
        """批量获取多个门店的指标"""
        if not self.enabled:
            return {}
        
        results = {}
        for store_id in store_ids:
            metrics = self.get_metrics(store_id, date)
            if metrics:
                results[store_id] = metrics
        
        return results
    
    # ========== Level 3: 诊断结果缓存 ==========
    
    def cache_diagnosis(
        self,
        store_ids: List[str],
        date_range: Tuple[str, str],
        diagnosis: Dict[str, Any],
        ttl: int = 3600  # 1小时
    ) -> bool:
        """
        缓存诊断结果（按门店组合）
        
        Args:
            store_ids: 门店ID列表
            date_range: 日期范围
            diagnosis: 诊断结果
            ttl: 过期时间（秒）
        """
        if not self.enabled:
            return False
        
        try:
            # 门店ID排序，确保相同组合生成相同键
            sorted_stores = sorted(store_ids) if store_ids else ['all']
            
            key = self._generate_key(
                self.LEVEL_DIAGNOSIS,
                stores='_'.join(sorted_stores),
                date_range=date_range
            )
            
            # 序列化并压缩
            serialized = self._serialize(diagnosis)
            compressed = self._compress(serialized)
            
            # 存储
            self.client.setex(key, ttl, compressed)
            
            logger.info(
                f"✅ [L3] 诊断结果已缓存: stores={len(sorted_stores)}, "
                f"size={len(compressed)/1024:.1f}KB"
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ [L3] 缓存失败: {e}")
            return False
    
    def get_diagnosis(
        self,
        store_ids: List[str],
        date_range: Tuple[str, str]
    ) -> Optional[Dict[str, Any]]:
        """获取诊断结果"""
        if not self.enabled:
            return None
        
        try:
            # 记录访问日志（用于热点分析）
            self._log_access(store_ids, date_range)
            
            sorted_stores = sorted(store_ids) if store_ids else ['all']
            
            key = self._generate_key(
                self.LEVEL_DIAGNOSIS,
                stores='_'.join(sorted_stores),
                date_range=date_range
            )
            
            compressed = self.client.get(key)
            if compressed is None:
                logger.debug(f"⏭️ [L3] 诊断结果未命中: stores={len(sorted_stores)}")
                return None
            
            # 解压并反序列化
            serialized = self._decompress(compressed)
            diagnosis = self._deserialize(serialized)
            
            logger.info(f"✅ [L3] 诊断结果命中: stores={len(sorted_stores)}")
            return diagnosis
            
        except Exception as e:
            logger.error(f"❌ [L3] 读取失败: {e}")
            return None
    
    # ========== 访问日志和热点分析 ==========
    
    def _log_access(self, store_ids: List[str], date_range: Tuple[str, str]):
        """记录访问日志"""
        self.access_log.append({
            'timestamp': datetime.now(),
            'store_ids': store_ids,
            'date_range': date_range
        })
        
        # 只保留最近1000条
        if len(self.access_log) > 1000:
            self.access_log = self.access_log[-1000:]
    
    def analyze_hot_stores(self, top_n: int = 20) -> List[str]:
        """
        分析热点门店
        
        Args:
            top_n: 返回TOP N个热点门店
            
        Returns:
            热点门店ID列表
        """
        if not self.access_log:
            return []
        
        # 统计门店访问频率
        store_count = defaultdict(int)
        for log in self.access_log:
            for store_id in log['store_ids']:
                store_count[store_id] += 1
        
        # 按访问频率排序
        sorted_stores = sorted(
            store_count.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        hot_stores = [store_id for store_id, _ in sorted_stores[:top_n]]
        
        logger.info(f"📊 热点分析: TOP{top_n}门店 = {hot_stores[:5]}...")
        return hot_stores
    
    # ========== 缓存管理 ==========
    
    def clear_level(self, level: int) -> int:
        """清空指定层级的缓存"""
        if not self.enabled:
            return 0
        
        try:
            level_names = {1: 'raw', 2: 'metrics', 3: 'diagnosis', 4: 'hotspot'}
            level_name = level_names.get(level, 'unknown')
            pattern = f"o2o:v8.4:{level_name}:*"
            
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"🗑️ 清空Level {level}缓存: {deleted}个键")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"❌ 清空缓存失败: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """清空所有缓存"""
        if not self.enabled:
            return False
        
        try:
            pattern = "o2o:v8.4:*"
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"🗑️ 清空所有缓存: {deleted}个键")
            return True
            
        except Exception as e:
            logger.error(f"❌ 清空缓存失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.enabled:
            return {'enabled': False}
        
        try:
            info = self.client.info('stats')
            memory = self.client.info('memory')
            
            # 统计各层级键数量
            level_counts = {}
            for level, name in {1: 'raw', 2: 'metrics', 3: 'diagnosis', 4: 'hotspot'}.items():
                pattern = f"o2o:v8.4:{name}:*"
                keys = self.client.keys(pattern)
                level_counts[f'level_{level}'] = len(keys)
            
            return {
                'enabled': True,
                'total_keys': self.client.dbsize(),
                'used_memory_mb': round(memory.get('used_memory', 0) / 1024 / 1024, 2),
                'max_memory_mb': round(memory.get('maxmemory', 0) / 1024 / 1024, 2),
                'memory_usage_pct': round(
                    memory.get('used_memory', 0) / max(memory.get('maxmemory', 1), 1) * 100, 2
                ),
                'total_commands': info.get('total_commands_processed', 0),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'hit_rate': round(
                    info.get('keyspace_hits', 0) / 
                    max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100,
                    2
                ),
                **level_counts
            }
            
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {'enabled': False, 'error': str(e)}


# 全局实例（单例）
_global_hierarchical_cache = None


def get_hierarchical_cache(**kwargs) -> HierarchicalCacheManager:
    """获取全局分层缓存管理器实例"""
    global _global_hierarchical_cache
    
    if _global_hierarchical_cache is None:
        _global_hierarchical_cache = HierarchicalCacheManager(**kwargs)
    
    return _global_hierarchical_cache


# 导出
__all__ = [
    'HierarchicalCacheManager',
    'get_hierarchical_cache'
]


if __name__ == "__main__":
    print("=" * 80)
    print(" 分层缓存管理器测试")
    print("=" * 80)
    
    # 初始化
    cache = HierarchicalCacheManager(
        host='localhost',
        port=6379,
        max_memory_mb=512,
        enable_compression=True
    )
    
    if cache.enabled:
        print("\n✅ 缓存管理器初始化成功")
        
        # 测试Level 3缓存
        print("\n测试Level 3（诊断结果缓存）:")
        test_diagnosis = {
            'overflow': {'count': 5, 'loss': 123.45},
            'delivery': {'count': 3, 'extra_cost': 67.89}
        }
        
        cache.cache_diagnosis(
            store_ids=['store_001', 'store_002'],
            date_range=('2025-12-01', '2025-12-11'),
            diagnosis=test_diagnosis
        )
        
        result = cache.get_diagnosis(
            store_ids=['store_001', 'store_002'],
            date_range=('2025-12-01', '2025-12-11')
        )
        
        print(f"缓存结果: {result}")
        
        # 统计信息
        print("\n缓存统计:")
        stats = cache.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("\n⚠️ Redis未启用，跳过测试")
