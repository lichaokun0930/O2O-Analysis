# -*- coding: utf-8 -*-
"""
企业级健康监控服务

功能:
- 深度健康检查（数据库、Redis、DuckDB）
- 性能指标收集
- 服务依赖状态
- 告警阈值检测
"""

import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import deque
import threading


@dataclass
class HealthStatus:
    """健康状态"""
    status: str  # healthy, degraded, unhealthy
    message: str
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: datetime
    value: float


class HealthService:
    """企业级健康监控服务"""
    
    # 告警阈值
    THRESHOLDS = {
        "cpu_percent": 80,
        "memory_percent": 85,
        "disk_percent": 90,
        "api_latency_ms": 500,
        "db_latency_ms": 100,
        "redis_latency_ms": 50,
        "error_rate_percent": 5,
    }
    
    def __init__(self):
        # 指标历史（最近1小时，每分钟一个点）
        self._metrics_history: Dict[str, deque] = {
            "cpu_percent": deque(maxlen=60),
            "memory_percent": deque(maxlen=60),
            "api_requests": deque(maxlen=60),
            "api_errors": deque(maxlen=60),
            "api_latency_avg": deque(maxlen=60),
        }
        
        # 请求统计（用于计算QPS和错误率）
        self._request_count = 0
        self._error_count = 0
        self._latency_sum = 0.0
        self._last_reset = datetime.now()
        self._lock = threading.Lock()
    
    def record_request(self, latency_ms: float, is_error: bool = False):
        """记录请求指标"""
        with self._lock:
            self._request_count += 1
            self._latency_sum += latency_ms
            if is_error:
                self._error_count += 1
    
    def _collect_metrics(self):
        """收集当前指标"""
        now = datetime.now()
        
        # 系统指标
        self._metrics_history["cpu_percent"].append(
            MetricPoint(now, psutil.cpu_percent(interval=0.1))
        )
        self._metrics_history["memory_percent"].append(
            MetricPoint(now, psutil.virtual_memory().percent)
        )
        
        # 请求指标
        with self._lock:
            elapsed = (now - self._last_reset).total_seconds()
            if elapsed > 0:
                qps = self._request_count / elapsed
                error_rate = (self._error_count / self._request_count * 100) if self._request_count > 0 else 0
                avg_latency = (self._latency_sum / self._request_count) if self._request_count > 0 else 0
            else:
                qps = 0
                error_rate = 0
                avg_latency = 0
            
            self._metrics_history["api_requests"].append(MetricPoint(now, qps))
            self._metrics_history["api_errors"].append(MetricPoint(now, error_rate))
            self._metrics_history["api_latency_avg"].append(MetricPoint(now, avg_latency))
            
            # 重置计数器
            self._request_count = 0
            self._error_count = 0
            self._latency_sum = 0.0
            self._last_reset = now
    
    def check_database(self) -> HealthStatus:
        """检查数据库健康状态"""
        try:
            from sqlalchemy import text
            import sys
            from pathlib import Path
            
            # 添加路径
            app_dir = Path(__file__).resolve().parent.parent.parent.parent
            if str(app_dir) not in sys.path:
                sys.path.insert(0, str(app_dir))
            
            from database.connection import engine
            
            start = time.time()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            latency = (time.time() - start) * 1000
            
            if latency > self.THRESHOLDS["db_latency_ms"]:
                return HealthStatus(
                    status="degraded",
                    message=f"数据库响应慢: {latency:.0f}ms",
                    latency_ms=latency
                )
            
            return HealthStatus(
                status="healthy",
                message="数据库连接正常",
                latency_ms=latency
            )
        except Exception as e:
            return HealthStatus(
                status="unhealthy",
                message=f"数据库连接失败: {str(e)}"
            )
    
    def check_redis(self) -> HealthStatus:
        """检查Redis健康状态"""
        try:
            import redis
            from ..config import settings
            
            start = time.time()
            client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                socket_timeout=5
            )
            client.ping()
            latency = (time.time() - start) * 1000
            
            # 获取内存使用
            info = client.info("memory")
            used_memory_mb = info.get("used_memory", 0) / 1024 / 1024
            
            if latency > self.THRESHOLDS["redis_latency_ms"]:
                return HealthStatus(
                    status="degraded",
                    message=f"Redis响应慢: {latency:.0f}ms",
                    latency_ms=latency,
                    details={"used_memory_mb": round(used_memory_mb, 2)}
                )
            
            return HealthStatus(
                status="healthy",
                message="Redis连接正常",
                latency_ms=latency,
                details={"used_memory_mb": round(used_memory_mb, 2)}
            )
        except Exception as e:
            return HealthStatus(
                status="unavailable",
                message=f"Redis不可用: {str(e)}"
            )
    
    def check_duckdb(self) -> HealthStatus:
        """检查DuckDB健康状态"""
        try:
            from . import duckdb_service
            
            start = time.time()
            status = duckdb_service.get_status()
            latency = (time.time() - start) * 1000
            
            if not status.get("has_data"):
                return HealthStatus(
                    status="degraded",
                    message="DuckDB无数据",
                    latency_ms=latency,
                    details=status
                )
            
            return HealthStatus(
                status="healthy",
                message=f"DuckDB正常: {status.get('raw_parquet_count', 0)}个文件",
                latency_ms=latency,
                details=status
            )
        except Exception as e:
            return HealthStatus(
                status="unavailable",
                message=f"DuckDB不可用: {str(e)}"
            )
    
    def check_system(self) -> HealthStatus:
        """检查系统资源"""
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        issues = []
        if cpu > self.THRESHOLDS["cpu_percent"]:
            issues.append(f"CPU过高: {cpu}%")
        if memory.percent > self.THRESHOLDS["memory_percent"]:
            issues.append(f"内存过高: {memory.percent}%")
        if disk.percent > self.THRESHOLDS["disk_percent"]:
            issues.append(f"磁盘过高: {disk.percent}%")
        
        details = {
            "cpu_percent": cpu,
            "memory_percent": memory.percent,
            "memory_used_gb": round(memory.used / 1024 / 1024 / 1024, 2),
            "memory_total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
            "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
        }
        
        if issues:
            return HealthStatus(
                status="degraded",
                message="; ".join(issues),
                details=details
            )
        
        return HealthStatus(
            status="healthy",
            message="系统资源正常",
            details=details
        )
    
    def get_full_health_check(self) -> Dict[str, Any]:
        """执行完整健康检查"""
        checks = {
            "database": self.check_database(),
            "redis": self.check_redis(),
            "duckdb": self.check_duckdb(),
            "system": self.check_system(),
        }
        
        # 计算总体状态
        statuses = [c.status for c in checks.values()]
        if "unhealthy" in statuses:
            overall = "unhealthy"
        elif "degraded" in statuses or "unavailable" in statuses:
            overall = "degraded"
        else:
            overall = "healthy"
        
        return {
            "status": overall,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                name: {
                    "status": check.status,
                    "message": check.message,
                    "latency_ms": check.latency_ms,
                    "details": check.details
                }
                for name, check in checks.items()
            }
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        self._collect_metrics()
        
        def get_latest(metric_name: str) -> Optional[float]:
            history = self._metrics_history.get(metric_name)
            if history and len(history) > 0:
                return history[-1].value
            return None
        
        def get_avg(metric_name: str) -> Optional[float]:
            history = self._metrics_history.get(metric_name)
            if history and len(history) > 0:
                values = [p.value for p in history]
                return round(sum(values) / len(values), 2)
            return None
        
        return {
            "timestamp": datetime.now().isoformat(),
            "current": {
                "cpu_percent": get_latest("cpu_percent"),
                "memory_percent": get_latest("memory_percent"),
                "api_qps": get_latest("api_requests"),
                "api_error_rate": get_latest("api_errors"),
                "api_latency_avg_ms": get_latest("api_latency_avg"),
            },
            "avg_1h": {
                "cpu_percent": get_avg("cpu_percent"),
                "memory_percent": get_avg("memory_percent"),
                "api_qps": get_avg("api_requests"),
                "api_error_rate": get_avg("api_errors"),
                "api_latency_avg_ms": get_avg("api_latency_avg"),
            },
            "thresholds": self.THRESHOLDS
        }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """获取当前告警"""
        alerts = []
        
        # 检查系统资源
        system = self.check_system()
        if system.status != "healthy":
            alerts.append({
                "level": "warning" if system.status == "degraded" else "critical",
                "source": "system",
                "message": system.message,
                "timestamp": datetime.now().isoformat()
            })
        
        # 检查数据库
        db = self.check_database()
        if db.status != "healthy":
            alerts.append({
                "level": "warning" if db.status == "degraded" else "critical",
                "source": "database",
                "message": db.message,
                "timestamp": datetime.now().isoformat()
            })
        
        # 检查Redis
        redis_status = self.check_redis()
        if redis_status.status == "unhealthy":
            alerts.append({
                "level": "critical",
                "source": "redis",
                "message": redis_status.message,
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts


# 全局健康服务实例
health_service = HealthService()
