# -*- coding: utf-8 -*-
"""
错误追踪服务

功能:
- 异常捕获和记录
- 错误聚合和去重
- 错误趋势分析
- 告警通知（可扩展）
"""

import traceback
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import threading
import json
from pathlib import Path


@dataclass
class ErrorRecord:
    """错误记录"""
    error_id: str
    error_type: str
    message: str
    traceback: str
    context: Dict[str, Any]
    timestamp: datetime
    trace_id: str
    count: int = 1
    first_seen: datetime = None
    last_seen: datetime = None
    
    def __post_init__(self):
        if self.first_seen is None:
            self.first_seen = self.timestamp
        if self.last_seen is None:
            self.last_seen = self.timestamp


class ErrorTrackingService:
    """错误追踪服务"""
    
    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self._errors: Dict[str, ErrorRecord] = {}  # error_id -> ErrorRecord
        self._error_timeline: List[Dict] = []  # 时间线
        self._lock = threading.Lock()
        
        # 错误存储目录
        self.error_dir = Path(__file__).resolve().parent.parent.parent.parent / "logs" / "errors"
        self.error_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_error_id(self, error_type: str, message: str, traceback_str: str) -> str:
        """生成错误ID（用于去重）"""
        # 基于错误类型和堆栈生成唯一ID
        content = f"{error_type}:{message}:{traceback_str[:500]}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def capture_exception(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        trace_id: str = ""
    ) -> str:
        """捕获异常"""
        error_type = type(error).__name__
        message = str(error)
        tb = traceback.format_exc()
        error_id = self._generate_error_id(error_type, message, tb)
        now = datetime.now()
        
        with self._lock:
            if error_id in self._errors:
                # 已存在的错误，更新计数
                existing = self._errors[error_id]
                existing.count += 1
                existing.last_seen = now
            else:
                # 新错误
                record = ErrorRecord(
                    error_id=error_id,
                    error_type=error_type,
                    message=message,
                    traceback=tb,
                    context=context or {},
                    timestamp=now,
                    trace_id=trace_id
                )
                self._errors[error_id] = record
                
                # 限制错误数量
                if len(self._errors) > self.max_errors:
                    # 删除最旧的错误
                    oldest_id = min(self._errors.keys(), 
                                   key=lambda k: self._errors[k].last_seen)
                    del self._errors[oldest_id]
            
            # 添加到时间线
            self._error_timeline.append({
                "error_id": error_id,
                "error_type": error_type,
                "message": message[:200],
                "timestamp": now.isoformat(),
                "trace_id": trace_id
            })
            
            # 限制时间线长度
            if len(self._error_timeline) > 1000:
                self._error_timeline = self._error_timeline[-500:]
        
        # 持久化到文件
        self._persist_error(error_id, error_type, message, tb, context, trace_id, now)
        
        return error_id
    
    def _persist_error(
        self,
        error_id: str,
        error_type: str,
        message: str,
        tb: str,
        context: Dict,
        trace_id: str,
        timestamp: datetime
    ):
        """持久化错误到文件"""
        try:
            date_str = timestamp.strftime("%Y-%m-%d")
            error_file = self.error_dir / f"errors_{date_str}.jsonl"
            
            error_data = {
                "error_id": error_id,
                "error_type": error_type,
                "message": message,
                "traceback": tb,
                "context": context,
                "trace_id": trace_id,
                "timestamp": timestamp.isoformat()
            }
            
            with open(error_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_data, ensure_ascii=False) + "\n")
        except Exception:
            pass  # 忽略持久化错误
    
    def get_error(self, error_id: str) -> Optional[Dict[str, Any]]:
        """获取错误详情"""
        with self._lock:
            record = self._errors.get(error_id)
            if record:
                return {
                    "error_id": record.error_id,
                    "error_type": record.error_type,
                    "message": record.message,
                    "traceback": record.traceback,
                    "context": record.context,
                    "count": record.count,
                    "first_seen": record.first_seen.isoformat(),
                    "last_seen": record.last_seen.isoformat(),
                    "trace_id": record.trace_id
                }
        return None
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的错误"""
        with self._lock:
            sorted_errors = sorted(
                self._errors.values(),
                key=lambda e: e.last_seen,
                reverse=True
            )[:limit]
            
            return [
                {
                    "error_id": e.error_id,
                    "error_type": e.error_type,
                    "message": e.message[:200],
                    "count": e.count,
                    "first_seen": e.first_seen.isoformat(),
                    "last_seen": e.last_seen.isoformat()
                }
                for e in sorted_errors
            ]
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误统计摘要"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            # 按类型统计
            by_type = defaultdict(int)
            recent_count = 0
            
            for record in self._errors.values():
                if record.last_seen >= cutoff:
                    by_type[record.error_type] += record.count
                    recent_count += record.count
            
            # 时间线统计（按小时）
            hourly = defaultdict(int)
            for item in self._error_timeline:
                ts = datetime.fromisoformat(item["timestamp"])
                if ts >= cutoff:
                    hour_key = ts.strftime("%Y-%m-%d %H:00")
                    hourly[hour_key] += 1
            
            return {
                "total_errors": recent_count,
                "unique_errors": len([e for e in self._errors.values() if e.last_seen >= cutoff]),
                "by_type": dict(by_type),
                "hourly_trend": dict(sorted(hourly.items())),
                "period_hours": hours
            }
    
    def get_top_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取出现次数最多的错误"""
        with self._lock:
            sorted_errors = sorted(
                self._errors.values(),
                key=lambda e: e.count,
                reverse=True
            )[:limit]
            
            return [
                {
                    "error_id": e.error_id,
                    "error_type": e.error_type,
                    "message": e.message[:200],
                    "count": e.count,
                    "first_seen": e.first_seen.isoformat(),
                    "last_seen": e.last_seen.isoformat()
                }
                for e in sorted_errors
            ]
    
    def clear_old_errors(self, days: int = 7):
        """清理旧错误"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self._lock:
            to_delete = [
                error_id for error_id, record in self._errors.items()
                if record.last_seen < cutoff
            ]
            for error_id in to_delete:
                del self._errors[error_id]
            
            self._error_timeline = [
                item for item in self._error_timeline
                if datetime.fromisoformat(item["timestamp"]) >= cutoff
            ]
        
        return len(to_delete)


# 全局错误追踪服务实例
error_tracking_service = ErrorTrackingService()
