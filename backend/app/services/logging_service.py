# -*- coding: utf-8 -*-
"""
企业级日志服务

功能:
- 结构化日志（JSON格式）
- 日志轮转（按大小/日期）
- 日志聚合查询
- 请求追踪（trace_id）
- 性能日志（慢请求告警）
"""

import os
import sys
import json
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextvars import ContextVar
from loguru import logger

# 请求追踪上下文
trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')

# 日志目录
LOG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


class LoggingService:
    """企业级日志服务"""
    
    def __init__(self):
        self.log_dir = LOG_DIR
        self._setup_logger()
    
    def _setup_logger(self):
        """配置日志器"""
        # 移除默认处理器
        logger.remove()
        
        # 控制台输出（彩色）
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{extra[trace_id]}</cyan> | "
                   "<level>{message}</level>",
            level="INFO",
            filter=lambda record: record["extra"].setdefault("trace_id", "--------")
        )
        
        # 应用日志（JSON格式，按天轮转）
        logger.add(
            self.log_dir / "app_{time:YYYY-MM-DD}.log",
            format="{message}",
            level="INFO",
            rotation="00:00",  # 每天轮转
            retention="30 days",  # 保留30天
            compression="gz",  # 压缩旧日志
            serialize=True,  # JSON格式
            filter=lambda record: record["extra"].setdefault("trace_id", "")
        )
        
        # 错误日志（单独文件）
        logger.add(
            self.log_dir / "error_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[trace_id]} | {message}",
            level="ERROR",
            rotation="00:00",
            retention="90 days",  # 错误日志保留更久
            compression="gz",
            filter=lambda record: record["extra"].setdefault("trace_id", "")
        )
        
        # 慢请求日志
        logger.add(
            self.log_dir / "slow_requests_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            level="WARNING",
            rotation="00:00",
            retention="30 days",
            filter=lambda record: record["extra"].get("slow_request", False)
        )
        
        # API访问日志
        logger.add(
            self.log_dir / "access_{time:YYYY-MM-DD}.log",
            format="{message}",
            level="INFO",
            rotation="00:00",
            retention="7 days",
            filter=lambda record: record["extra"].get("access_log", False)
        )
    
    def generate_trace_id(self) -> str:
        """生成请求追踪ID"""
        return str(uuid.uuid4())[:8]
    
    def set_trace_id(self, trace_id: str):
        """设置当前请求的追踪ID"""
        trace_id_var.set(trace_id)
    
    def get_trace_id(self) -> str:
        """获取当前请求的追踪ID"""
        return trace_id_var.get() or "--------"
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        logger.bind(trace_id=self.get_trace_id(), **kwargs).info(message)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        logger.bind(trace_id=self.get_trace_id(), **kwargs).warning(message)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        logger.bind(trace_id=self.get_trace_id(), **kwargs).error(message)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        logger.bind(trace_id=self.get_trace_id(), **kwargs).debug(message)
    
    def log_request(self, method: str, path: str, status_code: int, 
                    duration_ms: float, client_ip: str, **kwargs):
        """记录API访问日志"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "trace_id": self.get_trace_id(),
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            **kwargs
        }
        logger.bind(access_log=True, trace_id=self.get_trace_id()).info(
            json.dumps(log_data, ensure_ascii=False)
        )
        
        # 慢请求告警（>500ms）
        if duration_ms > 500:
            logger.bind(slow_request=True, trace_id=self.get_trace_id()).warning(
                f"🐢 慢请求: {method} {path} {duration_ms:.0f}ms"
            )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """记录错误日志（带上下文）"""
        import traceback
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "trace_id": self.get_trace_id(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        logger.bind(trace_id=self.get_trace_id()).error(
            f"❌ {type(error).__name__}: {str(error)}"
        )
    
    def get_recent_logs(self, level: str = "INFO", limit: int = 100) -> List[Dict]:
        """获取最近的日志（用于日志聚合查询）"""
        logs = []
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"app_{today}.log"
        
        if not log_file.exists():
            return logs
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    try:
                        log_entry = json.loads(line.strip())
                        if level == "ALL" or log_entry.get("record", {}).get("level", {}).get("name") == level:
                            logs.append({
                                "timestamp": log_entry.get("record", {}).get("time", {}).get("repr", ""),
                                "level": log_entry.get("record", {}).get("level", {}).get("name", ""),
                                "message": log_entry.get("record", {}).get("message", ""),
                                "trace_id": log_entry.get("record", {}).get("extra", {}).get("trace_id", "")
                            })
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.error(f"读取日志文件失败: {e}")
        
        return logs
    
    def get_error_summary(self, days: int = 7) -> Dict[str, Any]:
        """获取错误统计摘要"""
        error_counts = {}
        total_errors = 0
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            error_file = self.log_dir / f"error_{date}.log"
            
            if error_file.exists():
                try:
                    with open(error_file, 'r', encoding='utf-8') as f:
                        count = sum(1 for _ in f)
                        error_counts[date] = count
                        total_errors += count
                except Exception:
                    error_counts[date] = 0
            else:
                error_counts[date] = 0
        
        return {
            "total_errors": total_errors,
            "by_date": error_counts,
            "avg_per_day": round(total_errors / days, 1) if days > 0 else 0
        }
    
    def get_slow_requests(self, limit: int = 50) -> List[Dict]:
        """获取慢请求列表"""
        slow_requests = []
        today = datetime.now().strftime("%Y-%m-%d")
        slow_file = self.log_dir / f"slow_requests_{today}.log"
        
        if not slow_file.exists():
            return slow_requests
        
        try:
            with open(slow_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    parts = line.strip().split(" | ", 1)
                    if len(parts) == 2:
                        slow_requests.append({
                            "timestamp": parts[0],
                            "message": parts[1]
                        })
        except Exception:
            pass
        
        return slow_requests


# 全局日志服务实例
logging_service = LoggingService()
