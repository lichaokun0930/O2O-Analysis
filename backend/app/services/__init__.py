# -*- coding: utf-8 -*-
"""
服务层模块

提供业务逻辑服务，包括：
- aggregation_service: 预聚合表查询服务
- data_monitor_service: 数据量监控服务
- duckdb_service: DuckDB查询服务（已落地）
- parquet_sync_service: Parquet同步服务（已落地）
- logging_service: 企业级日志服务
- health_service: 健康监控服务
- error_tracking_service: 错误追踪服务
- rate_limiter_service: 请求限流服务
- cache_warmup_service: 缓存预热服务
- cache_protection_service: 缓存保护服务
- slow_query_service: 慢查询监控服务
"""

from .aggregation_service import aggregation_service, AggregationService
from .data_monitor_service import data_monitor_service, DataMonitorService
from .duckdb_service import duckdb_service, DuckDBService
from .parquet_sync_service import parquet_sync_service, ParquetSyncService
from .logging_service import logging_service, LoggingService
from .health_service import health_service, HealthService
from .error_tracking_service import error_tracking_service, ErrorTrackingService
from .rate_limiter_service import rate_limiter_service, RateLimiterService
from .cache_warmup_service import cache_warmup_service, CacheWarmupService
from .cache_protection_service import cache_protection_service, CacheProtectionService
from .slow_query_service import slow_query_service, SlowQueryService
from .query_router_service import query_router_service, QueryRouterService

__all__ = [
    'aggregation_service', 'AggregationService',
    'data_monitor_service', 'DataMonitorService',
    'duckdb_service', 'DuckDBService',
    'parquet_sync_service', 'ParquetSyncService',
    'logging_service', 'LoggingService',
    'health_service', 'HealthService',
    'error_tracking_service', 'ErrorTrackingService',
    'rate_limiter_service', 'RateLimiterService',
    'cache_warmup_service', 'CacheWarmupService',
    'cache_protection_service', 'CacheProtectionService',
    'slow_query_service', 'SlowQueryService',
    'query_router_service', 'QueryRouterService',
]
