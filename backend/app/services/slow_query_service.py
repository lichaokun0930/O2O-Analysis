# -*- coding: utf-8 -*-
"""
慢查询监控服务
监控数据库慢查询，自动告警和分析

功能：
- 自动捕获慢查询
- 查询耗时统计
- 慢查询告警
- 查询优化建议
"""

import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
import hashlib
import re

from .logging_service import logging_service


@dataclass
class SlowQueryRecord:
    """慢查询记录"""
    query_hash: str
    query_template: str  # 参数化后的查询模板
    duration_ms: float
    timestamp: datetime
    params: Optional[Dict] = None
    stack_trace: Optional[str] = None
    
    # 统计
    occurrence_count: int = 1
    total_duration_ms: float = 0
    max_duration_ms: float = 0
    min_duration_ms: float = float('inf')


@dataclass
class QueryStats:
    """查询统计"""
    query_hash: str
    query_template: str
    call_count: int = 0
    total_duration_ms: float = 0
    avg_duration_ms: float = 0
    max_duration_ms: float = 0
    min_duration_ms: float = float('inf')
    slow_count: int = 0  # 慢查询次数
    last_called: Optional[datetime] = None


class SlowQueryService:
    """
    慢查询监控服务
    
    使用示例：
    ```python
    # 装饰器方式
    @slow_query_service.monitor("get_orders")
    def get_orders(store_id: str):
        return db.query(...)
    
    # 上下文管理器方式
    with slow_query_service.track("complex_query"):
        result = db.execute(sql)
    ```
    """
    
    # 慢查询阈值（毫秒）
    SLOW_THRESHOLD_MS = 100  # 100ms以上视为慢查询
    VERY_SLOW_THRESHOLD_MS = 500  # 500ms以上视为非常慢
    
    # 保留的慢查询记录数
    MAX_SLOW_QUERIES = 100
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # 慢查询记录
        self._slow_queries: List[SlowQueryRecord] = []
        
        # 查询统计（按查询模板分组）
        self._query_stats: Dict[str, QueryStats] = {}
        
        # 告警回调
        self._alert_callbacks: List[callable] = []
        
        # 全局统计
        self._global_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "very_slow_queries": 0,
            "total_duration_ms": 0
        }
        
        logging_service.info("✅ 慢查询监控服务已启动")
    
    def _normalize_query(self, query: str) -> str:
        """
        标准化查询（移除具体参数值）
        用于聚合相同模式的查询
        """
        # 移除数字
        normalized = re.sub(r'\b\d+\b', '?', query)
        # 移除字符串值
        normalized = re.sub(r"'[^']*'", "'?'", normalized)
        # 移除多余空格
        normalized = ' '.join(normalized.split())
        return normalized
    
    def _get_query_hash(self, query: str) -> str:
        """生成查询哈希"""
        normalized = self._normalize_query(query)
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def record_query(
        self,
        query: str,
        duration_ms: float,
        params: Optional[Dict] = None,
        source: str = "unknown"
    ):
        """
        记录查询执行
        
        Args:
            query: 查询语句或标识
            duration_ms: 执行时间（毫秒）
            params: 查询参数
            source: 来源标识
        """
        with self._lock:
            self._global_stats["total_queries"] += 1
            self._global_stats["total_duration_ms"] += duration_ms
            
            query_hash = self._get_query_hash(query)
            query_template = self._normalize_query(query)
            
            # 更新查询统计
            if query_hash not in self._query_stats:
                self._query_stats[query_hash] = QueryStats(
                    query_hash=query_hash,
                    query_template=query_template
                )
            
            stats = self._query_stats[query_hash]
            stats.call_count += 1
            stats.total_duration_ms += duration_ms
            stats.avg_duration_ms = stats.total_duration_ms / stats.call_count
            stats.max_duration_ms = max(stats.max_duration_ms, duration_ms)
            stats.min_duration_ms = min(stats.min_duration_ms, duration_ms)
            stats.last_called = datetime.now()
            
            # 检查是否为慢查询
            is_slow = duration_ms >= self.SLOW_THRESHOLD_MS
            is_very_slow = duration_ms >= self.VERY_SLOW_THRESHOLD_MS
            
            if is_slow:
                self._global_stats["slow_queries"] += 1
                stats.slow_count += 1
                
                # 记录慢查询
                record = SlowQueryRecord(
                    query_hash=query_hash,
                    query_template=query_template,
                    duration_ms=duration_ms,
                    timestamp=datetime.now(),
                    params=params
                )
                
                self._slow_queries.append(record)
                
                # 限制记录数量
                if len(self._slow_queries) > self.MAX_SLOW_QUERIES:
                    self._slow_queries = self._slow_queries[-self.MAX_SLOW_QUERIES:]
                
                # 日志记录
                if is_very_slow:
                    self._global_stats["very_slow_queries"] += 1
                    logging_service.warning(
                        f"🐢 非常慢的查询 ({duration_ms:.0f}ms): {query_template[:100]}..."
                    )
                    # 触发告警
                    self._trigger_alert(record)
                else:
                    logging_service.debug(
                        f"🐢 慢查询 ({duration_ms:.0f}ms): {query_template[:80]}..."
                    )
    
    def _trigger_alert(self, record: SlowQueryRecord):
        """触发慢查询告警"""
        for callback in self._alert_callbacks:
            try:
                callback(record)
            except Exception as e:
                logging_service.error(f"慢查询告警回调失败: {e}")
    
    def add_alert_callback(self, callback: callable):
        """添加告警回调"""
        self._alert_callbacks.append(callback)
    
    def monitor(self, name: str = None):
        """
        查询监控装饰器
        
        使用示例：
        ```python
        @slow_query_service.monitor("get_orders")
        def get_orders():
            return db.query(...)
        ```
        """
        def decorator(func):
            query_name = name or func.__name__
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    self.record_query(
                        query=query_name,
                        duration_ms=duration_ms,
                        params={"args": str(args)[:100], "kwargs": str(kwargs)[:100]}
                    )
            return wrapper
        return decorator
    
    class QueryTracker:
        """查询追踪上下文管理器"""
        
        def __init__(self, service: 'SlowQueryService', name: str):
            self.service = service
            self.name = name
            self.start_time = None
        
        def __enter__(self):
            self.start_time = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration_ms = (time.time() - self.start_time) * 1000
            self.service.record_query(
                query=self.name,
                duration_ms=duration_ms
            )
    
    def track(self, name: str) -> 'QueryTracker':
        """
        查询追踪上下文管理器
        
        使用示例：
        ```python
        with slow_query_service.track("complex_aggregation"):
            result = db.execute(complex_sql)
        ```
        """
        return self.QueryTracker(self, name)
    
    def get_slow_queries(
        self,
        limit: int = 20,
        min_duration_ms: Optional[float] = None
    ) -> List[Dict]:
        """获取慢查询列表"""
        with self._lock:
            queries = self._slow_queries.copy()
        
        if min_duration_ms:
            queries = [q for q in queries if q.duration_ms >= min_duration_ms]
        
        # 按时间倒序
        queries.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [
            {
                "query_hash": q.query_hash,
                "query_template": q.query_template[:200],
                "duration_ms": round(q.duration_ms, 1),
                "timestamp": q.timestamp.isoformat(),
                "params": q.params
            }
            for q in queries[:limit]
        ]
    
    def get_query_stats(
        self,
        order_by: str = "avg_duration_ms",
        limit: int = 20
    ) -> List[Dict]:
        """获取查询统计"""
        with self._lock:
            stats_list = list(self._query_stats.values())
        
        # 排序
        if order_by == "avg_duration_ms":
            stats_list.sort(key=lambda x: x.avg_duration_ms, reverse=True)
        elif order_by == "total_duration_ms":
            stats_list.sort(key=lambda x: x.total_duration_ms, reverse=True)
        elif order_by == "call_count":
            stats_list.sort(key=lambda x: x.call_count, reverse=True)
        elif order_by == "slow_count":
            stats_list.sort(key=lambda x: x.slow_count, reverse=True)
        
        return [
            {
                "query_hash": s.query_hash,
                "query_template": s.query_template[:150],
                "call_count": s.call_count,
                "avg_duration_ms": round(s.avg_duration_ms, 1),
                "max_duration_ms": round(s.max_duration_ms, 1),
                "min_duration_ms": round(s.min_duration_ms, 1) if s.min_duration_ms != float('inf') else 0,
                "total_duration_ms": round(s.total_duration_ms, 1),
                "slow_count": s.slow_count,
                "slow_rate": round(s.slow_count / max(s.call_count, 1) * 100, 1),
                "last_called": s.last_called.isoformat() if s.last_called else None
            }
            for s in stats_list[:limit]
        ]
    
    def get_summary(self) -> Dict:
        """获取汇总统计"""
        with self._lock:
            total = self._global_stats["total_queries"]
            slow = self._global_stats["slow_queries"]
            very_slow = self._global_stats["very_slow_queries"]
            
            return {
                "total_queries": total,
                "slow_queries": slow,
                "very_slow_queries": very_slow,
                "slow_rate": round(slow / max(total, 1) * 100, 2),
                "avg_duration_ms": round(
                    self._global_stats["total_duration_ms"] / max(total, 1), 1
                ),
                "unique_queries": len(self._query_stats),
                "thresholds": {
                    "slow_ms": self.SLOW_THRESHOLD_MS,
                    "very_slow_ms": self.VERY_SLOW_THRESHOLD_MS
                }
            }
    
    def clear_stats(self):
        """清空统计"""
        with self._lock:
            self._slow_queries.clear()
            self._query_stats.clear()
            self._global_stats = {
                "total_queries": 0,
                "slow_queries": 0,
                "very_slow_queries": 0,
                "total_duration_ms": 0
            }


# 全局实例
slow_query_service = SlowQueryService()
