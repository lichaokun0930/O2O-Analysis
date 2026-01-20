# -*- coding: utf-8 -*-
"""
智能查询路由服务（完整版）

根据数据量自动选择最优查询引擎：
- < 100万条: PostgreSQL + 预聚合表（低延迟）
- >= 100万条: DuckDB + Parquet（高吞吐）

特性：
- 自动检测数据量
- 智能引擎切换（真正的路由，不只是状态报告）
- 查询性能监控
- 启动时状态报告
- 统一查询接口（自动选择最优引擎）
"""

from typing import Dict, Any, Optional, Tuple, List
from datetime import date, datetime
from dataclasses import dataclass
from enum import Enum
import time

from .logging_service import logging_service


class QueryEngine(Enum):
    """查询引擎类型"""
    POSTGRESQL = "postgresql"  # PostgreSQL + 预聚合表
    DUCKDB = "duckdb"          # DuckDB + Parquet


@dataclass
class QueryResult:
    """查询结果"""
    data: Any
    engine: QueryEngine
    query_time_ms: float
    source: str  # 数据来源描述


@dataclass
class EngineStatus:
    """引擎状态"""
    engine: QueryEngine
    available: bool
    record_count: int
    reason: str


class QueryRouterService:
    """
    智能查询路由服务
    
    路由策略：
    1. 数据量 < 100万: 使用 PostgreSQL（预聚合表已优化，延迟低）
    2. 数据量 >= 100万: 使用 DuckDB（列式存储，大数据量更快）
    3. DuckDB 不可用时: 降级到 PostgreSQL
    """
    
    # 切换阈值（条）
    SWITCH_THRESHOLD = 1_000_000  # 100万条
    
    # 数据量级别描述
    DATA_LEVELS = {
        "small": (0, 100_000, "小型", "PostgreSQL"),
        "medium": (100_000, 1_000_000, "中型", "PostgreSQL"),
        "large": (1_000_000, 10_000_000, "大型", "DuckDB"),
        "huge": (10_000_000, float('inf'), "超大型", "DuckDB"),
    }
    
    def __init__(self):
        self._current_engine: QueryEngine = QueryEngine.POSTGRESQL
        self._record_count: int = 0
        self._last_check: Optional[datetime] = None
        self._duckdb_available: bool = False
        self._postgresql_available: bool = False
        
        # 统计
        self._stats = {
            "postgresql_queries": 0,
            "duckdb_queries": 0,
            "auto_switches": 0,
        }
    
    def initialize(self) -> Dict[str, Any]:
        """
        初始化路由服务，检测数据量和引擎可用性
        
        Returns:
            初始化状态报告
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "record_count": 0,
            "data_level": "unknown",
            "data_level_desc": "未知",
            "current_engine": "postgresql",
            "recommended_engine": "postgresql",
            "auto_switch_enabled": True,
            "engines": {
                "postgresql": {"available": False, "reason": ""},
                "duckdb": {"available": False, "reason": ""},
            },
            "switch_threshold": self.SWITCH_THRESHOLD,
        }
        
        # 检查 PostgreSQL
        try:
            from database.connection import get_db_context
            from sqlalchemy import text
            
            with get_db_context() as db:
                result = db.execute(text("SELECT COUNT(*) FROM orders"))
                self._record_count = result.scalar() or 0
                report["record_count"] = self._record_count
                self._postgresql_available = True
                report["engines"]["postgresql"]["available"] = True
                report["engines"]["postgresql"]["reason"] = "连接正常"
        except Exception as e:
            report["engines"]["postgresql"]["reason"] = f"连接失败: {str(e)[:50]}"
        
        # 检查 DuckDB
        try:
            from .duckdb_service import duckdb_service
            status = duckdb_service.get_status()
            self._duckdb_available = status.get("has_data", False)
            report["engines"]["duckdb"]["available"] = self._duckdb_available
            if self._duckdb_available:
                report["engines"]["duckdb"]["reason"] = f"就绪 ({status['raw_parquet_count']} 个Parquet文件)"
            else:
                report["engines"]["duckdb"]["reason"] = "无Parquet数据"
        except Exception as e:
            report["engines"]["duckdb"]["reason"] = f"初始化失败: {str(e)[:50]}"
        
        # 确定数据级别
        data_level, level_desc, recommended = self._get_data_level(self._record_count)
        report["data_level"] = data_level
        report["data_level_desc"] = level_desc
        report["recommended_engine"] = recommended
        
        # 选择引擎
        if self._record_count >= self.SWITCH_THRESHOLD and self._duckdb_available:
            self._current_engine = QueryEngine.DUCKDB
            report["current_engine"] = "duckdb"
        else:
            self._current_engine = QueryEngine.POSTGRESQL
            report["current_engine"] = "postgresql"
        
        self._last_check = datetime.now()
        
        return report
    
    def _get_data_level(self, count: int) -> Tuple[str, str, str]:
        """获取数据级别"""
        for level, (min_val, max_val, desc, engine) in self.DATA_LEVELS.items():
            if min_val <= count < max_val:
                return level, desc, engine
        return "unknown", "未知", "postgresql"
    
    def get_engine(self) -> QueryEngine:
        """获取当前应使用的查询引擎"""
        return self._current_engine
    
    def should_use_duckdb(self) -> bool:
        """是否应该使用 DuckDB"""
        return (
            self._current_engine == QueryEngine.DUCKDB
            and self._duckdb_available
        )
    
    def record_query(self, engine: QueryEngine):
        """记录查询"""
        if engine == QueryEngine.POSTGRESQL:
            self._stats["postgresql_queries"] += 1
        else:
            self._stats["duckdb_queries"] += 1
    
    def get_status(self) -> Dict[str, Any]:
        """获取路由状态"""
        data_level, level_desc, recommended = self._get_data_level(self._record_count)
        
        return {
            "current_engine": self._current_engine.value,
            "record_count": self._record_count,
            "data_level": data_level,
            "data_level_desc": level_desc,
            "recommended_engine": recommended,
            "switch_threshold": self.SWITCH_THRESHOLD,
            "will_switch_at": f"{self.SWITCH_THRESHOLD:,} 条",
            "engines": {
                "postgresql": self._postgresql_available,
                "duckdb": self._duckdb_available,
            },
            "stats": self._stats,
            "last_check": self._last_check.isoformat() if self._last_check else None,
        }
    
    # ==================== 智能路由查询方法 ====================
    
    def query_overview(
        self,
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        channel: Optional[str] = None
    ) -> QueryResult:
        """
        智能路由：获取订单概览（六大卡片）
        
        自动选择最优引擎：
        - 数据量 < 100万: PostgreSQL + 预聚合表
        - 数据量 >= 100万: DuckDB + Parquet
        """
        start_time = time.time()
        
        # 确保已初始化
        if self._last_check is None:
            self.initialize()
        
        # 根据当前引擎选择查询方式
        if self.should_use_duckdb():
            try:
                from .duckdb_service import duckdb_service
                data = duckdb_service.query_kpi(store_name, start_date, end_date, channel)
                elapsed = (time.time() - start_time) * 1000
                self.record_query(QueryEngine.DUCKDB)
                
                return QueryResult(
                    data=data,
                    engine=QueryEngine.DUCKDB,
                    query_time_ms=round(elapsed, 2),
                    source="DuckDB + Parquet (智能路由)"
                )
            except Exception as e:
                logging_service.warning(f"DuckDB查询失败，降级到PostgreSQL: {e}")
                # 降级到 PostgreSQL
        
        # PostgreSQL 查询（使用预聚合表）
        try:
            from .aggregation_service import aggregation_service
            data = aggregation_service.get_store_overview(
                store_name=store_name,
                start_date=start_date,
                end_date=end_date
            )
            elapsed = (time.time() - start_time) * 1000
            self.record_query(QueryEngine.POSTGRESQL)
            
            return QueryResult(
                data=data,
                engine=QueryEngine.POSTGRESQL,
                query_time_ms=round(elapsed, 2),
                source="PostgreSQL + 预聚合表 (智能路由)"
            )
        except Exception as e:
            logging_service.error(f"PostgreSQL查询失败: {e}")
            raise
    
    def query_trend(
        self,
        days: int = 30,
        store_name: Optional[str] = None,
        channel: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        granularity: str = "day"
    ) -> QueryResult:
        """
        智能路由：获取订单趋势
        
        自动选择最优引擎
        """
        start_time = time.time()
        
        if self._last_check is None:
            self.initialize()
        
        # DuckDB 路由
        if self.should_use_duckdb():
            try:
                from .duckdb_service import duckdb_service
                data = duckdb_service.query_trend(
                    days=days,
                    store_name=store_name,
                    channel=channel,
                    start_date=start_date,
                    end_date=end_date,
                    granularity=granularity
                )
                elapsed = (time.time() - start_time) * 1000
                self.record_query(QueryEngine.DUCKDB)
                
                return QueryResult(
                    data=data,
                    engine=QueryEngine.DUCKDB,
                    query_time_ms=round(elapsed, 2),
                    source="DuckDB + Parquet (智能路由)"
                )
            except Exception as e:
                logging_service.warning(f"DuckDB趋势查询失败，降级到PostgreSQL: {e}")
        
        # PostgreSQL 查询
        try:
            from .aggregation_service import aggregation_service
            
            # 映射渠道参数
            agg_channel = None if channel == 'all' else channel
            
            data = aggregation_service.get_daily_trend(
                store_name=store_name,
                start_date=start_date,
                end_date=end_date,
                channel=agg_channel
            )
            elapsed = (time.time() - start_time) * 1000
            self.record_query(QueryEngine.POSTGRESQL)
            
            # 转换为统一格式
            if data:
                result_data = {
                    "dates": [str(d.get("date", ""))[:10] for d in data],
                    "order_counts": [d.get("order_count", 0) for d in data],
                    "amounts": [d.get("amount", 0) for d in data],
                    "profits": [d.get("profit", 0) for d in data],
                    "avg_values": [d.get("avg_value", 0) for d in data],
                    "profit_rates": [d.get("profit_rate", 0) for d in data],
                }
            else:
                result_data = {
                    "dates": [], "order_counts": [], "amounts": [],
                    "profits": [], "avg_values": [], "profit_rates": []
                }
            
            return QueryResult(
                data=result_data,
                engine=QueryEngine.POSTGRESQL,
                query_time_ms=round(elapsed, 2),
                source="PostgreSQL + 预聚合表 (智能路由)"
            )
        except Exception as e:
            logging_service.error(f"PostgreSQL趋势查询失败: {e}")
            raise
    
    def query_channels(
        self,
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> QueryResult:
        """
        智能路由：获取渠道分析
        
        自动选择最优引擎
        注意：PostgreSQL 没有渠道预聚合表，使用原始查询
        """
        start_time = time.time()
        
        if self._last_check is None:
            self.initialize()
        
        # DuckDB 路由（优先）
        if self.should_use_duckdb():
            try:
                from .duckdb_service import duckdb_service
                data = duckdb_service.query_channels(store_name, start_date, end_date)
                elapsed = (time.time() - start_time) * 1000
                self.record_query(QueryEngine.DUCKDB)
                
                return QueryResult(
                    data=data,
                    engine=QueryEngine.DUCKDB,
                    query_time_ms=round(elapsed, 2),
                    source="DuckDB + Parquet (智能路由)"
                )
            except Exception as e:
                logging_service.warning(f"DuckDB渠道查询失败，降级到PostgreSQL: {e}")
        
        # PostgreSQL 原始查询（没有渠道预聚合表）
        # 返回空结果，让 v1 API 使用原始查询逻辑
        elapsed = (time.time() - start_time) * 1000
        self.record_query(QueryEngine.POSTGRESQL)
        
        return QueryResult(
            data=None,  # 返回 None 表示需要使用原始查询
            engine=QueryEngine.POSTGRESQL,
            query_time_ms=round(elapsed, 2),
            source="PostgreSQL (需要原始查询)"
        )
    
    def query_categories(
        self,
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        top_n: int = 10
    ) -> QueryResult:
        """
        智能路由：获取品类分析
        
        自动选择最优引擎
        """
        start_time = time.time()
        
        if self._last_check is None:
            self.initialize()
        
        # DuckDB 路由
        if self.should_use_duckdb():
            try:
                from .duckdb_service import duckdb_service
                data = duckdb_service.query_categories(store_name, start_date, end_date, top_n)
                elapsed = (time.time() - start_time) * 1000
                self.record_query(QueryEngine.DUCKDB)
                
                return QueryResult(
                    data=data,
                    engine=QueryEngine.DUCKDB,
                    query_time_ms=round(elapsed, 2),
                    source="DuckDB + Parquet (智能路由)"
                )
            except Exception as e:
                logging_service.warning(f"DuckDB品类查询失败，降级到PostgreSQL: {e}")
        
        # PostgreSQL 查询（使用预聚合表）
        try:
            from .aggregation_service import aggregation_service
            data = aggregation_service.get_category_analysis(
                store_name=store_name,
                start_date=start_date,
                end_date=end_date
            )
            elapsed = (time.time() - start_time) * 1000
            self.record_query(QueryEngine.POSTGRESQL)
            
            # 转换格式并限制数量
            if data:
                result_data = data[:top_n]
            else:
                result_data = []
            
            return QueryResult(
                data=result_data,
                engine=QueryEngine.POSTGRESQL,
                query_time_ms=round(elapsed, 2),
                source="PostgreSQL + 预聚合表 (智能路由)"
            )
        except Exception as e:
            logging_service.error(f"PostgreSQL品类查询失败: {e}")
            raise
    
    # ==================== 测试方法 ====================
    
    def force_engine(self, engine: str) -> Dict[str, Any]:
        """
        强制切换引擎（仅用于测试）
        
        Args:
            engine: "postgresql" 或 "duckdb"
        
        Returns:
            切换结果
        """
        if engine == "duckdb":
            if not self._duckdb_available:
                return {"success": False, "message": "DuckDB 不可用"}
            self._current_engine = QueryEngine.DUCKDB
            self._stats["auto_switches"] += 1
            return {"success": True, "message": "已切换到 DuckDB", "engine": "duckdb"}
        elif engine == "postgresql":
            if not self._postgresql_available:
                return {"success": False, "message": "PostgreSQL 不可用"}
            self._current_engine = QueryEngine.POSTGRESQL
            self._stats["auto_switches"] += 1
            return {"success": True, "message": "已切换到 PostgreSQL", "engine": "postgresql"}
        else:
            return {"success": False, "message": f"未知引擎: {engine}"}
    
    def get_startup_message(self) -> str:
        """
        获取启动时的状态消息（用于终端显示）
        """
        report = self.initialize()
        
        lines = []
        lines.append("")
        lines.append("=" * 60)
        lines.append("  🧠 智能查询路由引擎")
        lines.append("=" * 60)
        lines.append("")
        
        # 数据量
        count = report["record_count"]
        level_desc = report["data_level_desc"]
        lines.append(f"  📊 数据量: {count:,} 条 ({level_desc}数据)")
        lines.append(f"  📈 切换阈值: {self.SWITCH_THRESHOLD:,} 条")
        lines.append("")
        
        # 引擎状态
        lines.append("  🔧 查询引擎状态:")
        pg_status = report["engines"]["postgresql"]
        dk_status = report["engines"]["duckdb"]
        
        pg_icon = "✅" if pg_status["available"] else "❌"
        dk_icon = "✅" if dk_status["available"] else "⚠️"
        
        lines.append(f"     {pg_icon} PostgreSQL: {pg_status['reason']}")
        lines.append(f"     {dk_icon} DuckDB: {dk_status['reason']}")
        lines.append("")
        
        # 当前引擎
        current = report["current_engine"].upper()
        recommended = report["recommended_engine"].upper()
        
        if current == recommended:
            lines.append(f"  🎯 当前引擎: {current} (最优选择)")
        else:
            lines.append(f"  🎯 当前引擎: {current}")
            lines.append(f"  💡 推荐引擎: {recommended}")
        
        # 智能切换提示
        lines.append("")
        if count < self.SWITCH_THRESHOLD:
            remaining = self.SWITCH_THRESHOLD - count
            lines.append(f"  💡 智能切换: 数据量达到 {self.SWITCH_THRESHOLD:,} 条后")
            lines.append(f"              将自动切换到 DuckDB 引擎")
            lines.append(f"              (还需 {remaining:,} 条)")
        else:
            if dk_status["available"]:
                lines.append(f"  ✅ 智能切换: 已启用 DuckDB 加速")
            else:
                lines.append(f"  ⚠️ 智能切换: 数据量已达标，但 DuckDB 未就绪")
                lines.append(f"              请运行 迁移历史数据到Parquet.py")
        
        lines.append("")
        lines.append("=" * 60)
        lines.append("")
        
        return "\n".join(lines)
    
    def format_for_powershell(self) -> str:
        """
        格式化为 PowerShell 输出命令
        """
        report = self.initialize()
        
        commands = []
        
        # 标题
        commands.append('Write-Host ""')
        commands.append('Write-Host "============================================================" -ForegroundColor Magenta')
        commands.append('Write-Host "  🧠 智能查询路由引擎" -ForegroundColor White')
        commands.append('Write-Host "============================================================" -ForegroundColor Magenta')
        commands.append('Write-Host ""')
        
        # 数据量
        count = report["record_count"]
        level_desc = report["data_level_desc"]
        commands.append(f'Write-Host "  📊 数据量: {count:,} 条 ({level_desc}数据)" -ForegroundColor Cyan')
        commands.append(f'Write-Host "  📈 切换阈值: {self.SWITCH_THRESHOLD:,} 条" -ForegroundColor Gray')
        commands.append('Write-Host ""')
        
        # 引擎状态
        commands.append('Write-Host "  🔧 查询引擎状态:" -ForegroundColor White')
        
        pg_status = report["engines"]["postgresql"]
        dk_status = report["engines"]["duckdb"]
        
        pg_color = "Green" if pg_status["available"] else "Red"
        dk_color = "Green" if dk_status["available"] else "Yellow"
        pg_icon = "OK" if pg_status["available"] else "X"
        dk_icon = "OK" if dk_status["available"] else "!"
        
        commands.append(f'Write-Host "     ({pg_icon}) PostgreSQL: {pg_status["reason"]}" -ForegroundColor {pg_color}')
        commands.append(f'Write-Host "     ({dk_icon}) DuckDB: {dk_status["reason"]}" -ForegroundColor {dk_color}')
        commands.append('Write-Host ""')
        
        # 当前引擎
        current = report["current_engine"].upper()
        commands.append(f'Write-Host "  🎯 当前引擎: {current}" -ForegroundColor Green')
        
        # 智能切换提示
        commands.append('Write-Host ""')
        if count < self.SWITCH_THRESHOLD:
            remaining = self.SWITCH_THRESHOLD - count
            commands.append(f'Write-Host "  💡 智能切换: 数据量达到 {self.SWITCH_THRESHOLD:,} 条后自动切换到 DuckDB" -ForegroundColor Yellow')
            commands.append(f'Write-Host "              (还需 {remaining:,} 条)" -ForegroundColor Gray')
        else:
            if dk_status["available"]:
                commands.append('Write-Host "  ✅ 智能切换: 已启用 DuckDB 加速" -ForegroundColor Green')
            else:
                commands.append('Write-Host "  ⚠️ 智能切换: 数据量已达标，但 DuckDB 未就绪" -ForegroundColor Yellow')
        
        commands.append('Write-Host ""')
        
        return "\n".join(commands)


# 全局实例
query_router_service = QueryRouterService()
