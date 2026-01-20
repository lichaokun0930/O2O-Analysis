# -*- coding: utf-8 -*-
"""
请求限流服务
防止API被单用户/IP刷爆，保护系统稳定性

实现：
- 滑动窗口限流算法
- 支持IP级别和用户级别限流
- Redis存储（高性能）+ 内存降级（Redis不可用时）
"""

import time
import hashlib
from typing import Optional, Dict, Tuple
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import threading

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class RateLimitConfig:
    """限流配置"""
    requests_per_minute: int = 60      # 每分钟请求数
    requests_per_second: int = 10      # 每秒请求数（突发限制）
    burst_size: int = 20               # 突发容量
    block_duration: int = 60           # 超限后封禁时长（秒）


class RateLimiterService:
    """
    请求限流服务
    
    特性：
    - 滑动窗口算法，精确限流
    - Redis存储，支持分布式
    - 内存降级，Redis不可用时自动切换
    - IP和用户双重限流
    """
    
    # 默认限流配置（按路径分组）
    DEFAULT_LIMITS = {
        # 高频API（数据查询）
        "high_freq": RateLimitConfig(
            requests_per_minute=120,
            requests_per_second=20,
            burst_size=30
        ),
        # 普通API
        "normal": RateLimitConfig(
            requests_per_minute=60,
            requests_per_second=10,
            burst_size=20
        ),
        # 重型API（报表导出等）
        "heavy": RateLimitConfig(
            requests_per_minute=10,
            requests_per_second=2,
            burst_size=5
        ),
        # 认证API（防暴力破解）
        "auth": RateLimitConfig(
            requests_per_minute=10,
            requests_per_second=2,
            burst_size=5,
            block_duration=300  # 超限封禁5分钟
        )
    }
    
    # 路径到限流组的映射
    PATH_GROUPS = {
        "/api/v1/auth": "auth",
        "/api/v1/orders/kpi": "high_freq",
        "/api/v1/orders/trend": "high_freq",
        "/api/v1/diagnosis": "high_freq",
        "/api/v1/reports/export": "heavy",
        "/api/v1/data/upload": "heavy",
    }
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 1,  # 使用独立的db
        enabled: bool = True
    ):
        self.enabled = enabled
        self.redis_client: Optional[redis.Redis] = None
        self.use_redis = False
        
        # 内存存储（降级方案）
        self._memory_store: Dict[str, list] = defaultdict(list)
        self._blocked_keys: Dict[str, float] = {}
        self._lock = threading.Lock()
        
        # 统计
        self._stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "redis_errors": 0
        }
        
        if enabled and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    socket_connect_timeout=2,
                    socket_timeout=1
                )
                self.redis_client.ping()
                self.use_redis = True
                print("✅ 限流服务已启用 (Redis模式)")
            except Exception as e:
                print(f"⚠️ Redis连接失败，限流服务降级为内存模式: {e}")
                self.use_redis = False
        
        if enabled and not self.use_redis:
            print("✅ 限流服务已启用 (内存模式)")
    
    def _get_limit_config(self, path: str) -> RateLimitConfig:
        """根据路径获取限流配置"""
        for prefix, group in self.PATH_GROUPS.items():
            if path.startswith(prefix):
                return self.DEFAULT_LIMITS[group]
        return self.DEFAULT_LIMITS["normal"]
    
    def _generate_key(self, identifier: str, window: str) -> str:
        """生成限流键"""
        return f"ratelimit:{window}:{hashlib.md5(identifier.encode()).hexdigest()[:16]}"
    
    def check_rate_limit(
        self,
        client_ip: str,
        path: str,
        user_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        检查请求是否超过限流
        
        Args:
            client_ip: 客户端IP
            path: 请求路径
            user_id: 用户ID（可选）
            
        Returns:
            (allowed, info): 是否允许, 限流信息
        """
        if not self.enabled:
            return True, None
        
        self._stats["total_requests"] += 1
        
        # 使用IP或用户ID作为标识
        identifier = user_id or client_ip
        config = self._get_limit_config(path)
        
        now = time.time()
        
        # 检查是否在封禁期
        if self._is_blocked(identifier):
            self._stats["blocked_requests"] += 1
            return False, {
                "error": "rate_limit_exceeded",
                "message": "请求过于频繁，请稍后再试",
                "retry_after": self._get_block_remaining(identifier)
            }
        
        # 检查每秒限制（突发控制）
        second_key = self._generate_key(identifier, f"s:{int(now)}")
        second_count = self._increment(second_key, ttl=2)
        
        if second_count > config.requests_per_second:
            self._stats["blocked_requests"] += 1
            return False, {
                "error": "rate_limit_exceeded",
                "message": "请求过于频繁",
                "limit": config.requests_per_second,
                "window": "1s",
                "retry_after": 1
            }
        
        # 检查每分钟限制
        minute_key = self._generate_key(identifier, f"m:{int(now // 60)}")
        minute_count = self._increment(minute_key, ttl=120)
        
        if minute_count > config.requests_per_minute:
            # 超限，加入封禁
            self._block(identifier, config.block_duration)
            self._stats["blocked_requests"] += 1
            return False, {
                "error": "rate_limit_exceeded",
                "message": "请求过于频繁，已被临时限制",
                "limit": config.requests_per_minute,
                "window": "1m",
                "retry_after": config.block_duration
            }
        
        return True, {
            "remaining": config.requests_per_minute - minute_count,
            "limit": config.requests_per_minute,
            "reset": 60 - (int(now) % 60)
        }
    
    def _increment(self, key: str, ttl: int) -> int:
        """增加计数"""
        if self.use_redis:
            try:
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, ttl)
                result = pipe.execute()
                return result[0]
            except Exception as e:
                self._stats["redis_errors"] += 1
                # 降级到内存
                return self._memory_increment(key, ttl)
        else:
            return self._memory_increment(key, ttl)
    
    def _memory_increment(self, key: str, ttl: int) -> int:
        """内存计数（降级方案）"""
        now = time.time()
        with self._lock:
            # 清理过期记录
            self._memory_store[key] = [
                t for t in self._memory_store[key]
                if now - t < ttl
            ]
            self._memory_store[key].append(now)
            return len(self._memory_store[key])
    
    def _is_blocked(self, identifier: str) -> bool:
        """检查是否被封禁"""
        block_key = f"block:{identifier}"
        
        if self.use_redis:
            try:
                return self.redis_client.exists(block_key) > 0
            except:
                pass
        
        with self._lock:
            if block_key in self._blocked_keys:
                if time.time() < self._blocked_keys[block_key]:
                    return True
                del self._blocked_keys[block_key]
            return False
    
    def _block(self, identifier: str, duration: int):
        """封禁标识"""
        block_key = f"block:{identifier}"
        
        if self.use_redis:
            try:
                self.redis_client.setex(block_key, duration, "1")
                return
            except:
                pass
        
        with self._lock:
            self._blocked_keys[block_key] = time.time() + duration
    
    def _get_block_remaining(self, identifier: str) -> int:
        """获取封禁剩余时间"""
        block_key = f"block:{identifier}"
        
        if self.use_redis:
            try:
                ttl = self.redis_client.ttl(block_key)
                return max(0, ttl)
            except:
                pass
        
        with self._lock:
            if block_key in self._blocked_keys:
                remaining = self._blocked_keys[block_key] - time.time()
                return max(0, int(remaining))
            return 0
    
    def get_stats(self) -> Dict:
        """获取限流统计"""
        return {
            "enabled": self.enabled,
            "mode": "redis" if self.use_redis else "memory",
            "total_requests": self._stats["total_requests"],
            "blocked_requests": self._stats["blocked_requests"],
            "block_rate": round(
                self._stats["blocked_requests"] / max(self._stats["total_requests"], 1) * 100, 2
            ),
            "redis_errors": self._stats["redis_errors"]
        }
    
    def reset_stats(self):
        """重置统计"""
        self._stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "redis_errors": 0
        }


# 全局实例
rate_limiter_service = RateLimiterService()
