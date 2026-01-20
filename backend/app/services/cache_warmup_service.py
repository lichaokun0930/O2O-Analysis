# -*- coding: utf-8 -*-
"""
缓存预热服务
应用启动时预加载热点数据，首次访问秒开

功能：
- 启动时自动预热核心数据
- 支持手动触发预热
- 预热进度监控
- 智能预热（根据访问频率）
"""

import asyncio
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading

from .logging_service import logging_service


@dataclass
class WarmupTask:
    """预热任务"""
    name: str
    loader: Callable
    cache_key: str
    ttl: int = 3600  # 缓存时间（秒）
    priority: int = 1  # 优先级（1最高）
    enabled: bool = True
    last_warmup: Optional[datetime] = None
    warmup_count: int = 0
    avg_duration_ms: float = 0


class CacheWarmupService:
    """
    缓存预热服务
    
    使用示例：
    ```python
    warmup_service.register_task(
        name="kpi_data",
        loader=lambda: orders_service.get_kpi_summary(),
        cache_key="orders:kpi:summary",
        ttl=1800,
        priority=1
    )
    
    # 启动时预热
    await warmup_service.warmup_all()
    ```
    """
    
    def __init__(self, max_workers: int = 4):
        self._tasks: Dict[str, WarmupTask] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self._warmup_in_progress = False
        self._last_full_warmup: Optional[datetime] = None
        
        # 预热统计
        self._stats = {
            "total_warmups": 0,
            "successful_warmups": 0,
            "failed_warmups": 0,
            "total_duration_ms": 0
        }
        
        # 注册默认预热任务
        self._register_default_tasks()
    
    def _register_default_tasks(self):
        """注册默认预热任务"""
        # 这些任务会在应用启动时自动预热
        default_tasks = [
            {
                "name": "stores_list",
                "cache_key": "warmup:stores:list",
                "ttl": 3600,
                "priority": 1,
                "description": "门店列表"
            },
            {
                "name": "channels_list",
                "cache_key": "warmup:channels:list",
                "ttl": 3600,
                "priority": 1,
                "description": "渠道列表"
            },
            {
                "name": "date_range",
                "cache_key": "warmup:date:range",
                "ttl": 3600,
                "priority": 1,
                "description": "数据日期范围"
            },
            {
                "name": "kpi_summary",
                "cache_key": "warmup:kpi:summary",
                "ttl": 1800,
                "priority": 2,
                "description": "KPI汇总"
            },
            {
                "name": "category_list",
                "cache_key": "warmup:category:list",
                "ttl": 3600,
                "priority": 2,
                "description": "商品分类列表"
            }
        ]
        
        for task in default_tasks:
            self._tasks[task["name"]] = WarmupTask(
                name=task["name"],
                loader=None,  # 稍后由具体服务注册
                cache_key=task["cache_key"],
                ttl=task["ttl"],
                priority=task["priority"],
                enabled=False  # 默认禁用，等待注册loader
            )
    
    def register_task(
        self,
        name: str,
        loader: Callable,
        cache_key: str,
        ttl: int = 3600,
        priority: int = 5
    ):
        """
        注册预热任务
        
        Args:
            name: 任务名称
            loader: 数据加载函数
            cache_key: 缓存键
            ttl: 缓存时间（秒）
            priority: 优先级（1-10，1最高）
        """
        with self._lock:
            if name in self._tasks:
                # 更新已有任务
                self._tasks[name].loader = loader
                self._tasks[name].cache_key = cache_key
                self._tasks[name].ttl = ttl
                self._tasks[name].priority = priority
                self._tasks[name].enabled = True
            else:
                self._tasks[name] = WarmupTask(
                    name=name,
                    loader=loader,
                    cache_key=cache_key,
                    ttl=ttl,
                    priority=priority,
                    enabled=True
                )
            
            logging_service.debug(f"📦 预热任务已注册: {name}")
    
    def unregister_task(self, name: str):
        """注销预热任务"""
        with self._lock:
            if name in self._tasks:
                del self._tasks[name]
    
    async def warmup_task(self, name: str) -> Dict:
        """
        执行单个预热任务
        
        Returns:
            {"success": bool, "duration_ms": float, "error": str}
        """
        if name not in self._tasks:
            return {"success": False, "error": f"任务不存在: {name}"}
        
        task = self._tasks[name]
        if not task.enabled or task.loader is None:
            return {"success": False, "error": f"任务未启用或未注册loader: {name}"}
        
        start_time = time.time()
        
        try:
            # 执行加载
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(self._executor, task.loader)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # 缓存数据
            await self._cache_data(task.cache_key, data, task.ttl)
            
            # 更新统计
            with self._lock:
                task.last_warmup = datetime.now()
                task.warmup_count += 1
                task.avg_duration_ms = (
                    (task.avg_duration_ms * (task.warmup_count - 1) + duration_ms)
                    / task.warmup_count
                )
                self._stats["successful_warmups"] += 1
                self._stats["total_duration_ms"] += duration_ms
            
            logging_service.info(f"✅ 预热完成: {name} ({duration_ms:.0f}ms)")
            
            return {
                "success": True,
                "duration_ms": duration_ms,
                "cache_key": task.cache_key
            }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            with self._lock:
                self._stats["failed_warmups"] += 1
            
            logging_service.error(f"❌ 预热失败: {name} - {e}")
            
            return {
                "success": False,
                "duration_ms": duration_ms,
                "error": str(e)
            }
    
    async def warmup_all(self, force: bool = False) -> Dict:
        """
        执行所有预热任务
        
        Args:
            force: 是否强制预热（忽略已缓存的数据）
            
        Returns:
            预热结果汇总
        """
        if self._warmup_in_progress:
            return {"success": False, "error": "预热正在进行中"}
        
        self._warmup_in_progress = True
        start_time = time.time()
        
        try:
            # 按优先级排序
            sorted_tasks = sorted(
                [t for t in self._tasks.values() if t.enabled and t.loader],
                key=lambda x: x.priority
            )
            
            if not sorted_tasks:
                return {
                    "success": True,
                    "message": "没有可执行的预热任务",
                    "tasks_count": 0
                }
            
            logging_service.info(f"🔥 开始缓存预热 ({len(sorted_tasks)} 个任务)...")
            
            results = {}
            success_count = 0
            
            for task in sorted_tasks:
                result = await self.warmup_task(task.name)
                results[task.name] = result
                if result["success"]:
                    success_count += 1
            
            total_duration = (time.time() - start_time) * 1000
            self._last_full_warmup = datetime.now()
            self._stats["total_warmups"] += 1
            
            logging_service.info(
                f"🔥 缓存预热完成: {success_count}/{len(sorted_tasks)} 成功 "
                f"({total_duration:.0f}ms)"
            )
            
            return {
                "success": True,
                "total_tasks": len(sorted_tasks),
                "successful": success_count,
                "failed": len(sorted_tasks) - success_count,
                "duration_ms": total_duration,
                "results": results
            }
            
        finally:
            self._warmup_in_progress = False
    
    async def _cache_data(self, key: str, data: Any, ttl: int):
        """缓存数据到Redis"""
        try:
            # 尝试使用Redis缓存
            from redis_cache_manager import get_cache_manager
            cache = get_cache_manager()
            if cache and cache.enabled:
                cache.set(key, data, ttl=ttl)
        except Exception as e:
            logging_service.warning(f"⚠️ 缓存写入失败: {key} - {e}")
    
    def get_status(self) -> Dict:
        """获取预热服务状态"""
        with self._lock:
            enabled_tasks = [t for t in self._tasks.values() if t.enabled and t.loader]
            
            return {
                "warmup_in_progress": self._warmup_in_progress,
                "last_full_warmup": (
                    self._last_full_warmup.isoformat()
                    if self._last_full_warmup else None
                ),
                "registered_tasks": len(self._tasks),
                "enabled_tasks": len(enabled_tasks),
                "stats": self._stats.copy(),
                "tasks": [
                    {
                        "name": t.name,
                        "enabled": t.enabled,
                        "priority": t.priority,
                        "last_warmup": t.last_warmup.isoformat() if t.last_warmup else None,
                        "warmup_count": t.warmup_count,
                        "avg_duration_ms": round(t.avg_duration_ms, 1)
                    }
                    for t in sorted(self._tasks.values(), key=lambda x: x.priority)
                ]
            }


# 全局实例
cache_warmup_service = CacheWarmupService()
