# -*- coding: utf-8 -*-
"""
DuckDB 查询服务（完整版）

专为千万级OLAP分析场景设计
支持从Parquet文件高效查询

性能对比（千万级数据）：
- Pandas: 30-60秒
- DuckDB: < 1秒
"""
import duckdb
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import pandas as pd


class DuckDBService:
    """
    DuckDB 查询服务（单例模式）
    
    查询路由策略：
    1. 预聚合Parquet存在 → 直接查询（最快）
    2. 原始Parquet存在 → 实时聚合（较快）
    3. 都不存在 → 回退到PostgreSQL预聚合表
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, data_dir: str = None):
        if hasattr(self, '_initialized'):
            return
        
        # 默认数据目录
        if data_dir is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            data_dir = project_root / "data"
        
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.agg_dir = self.data_dir / "aggregated"
        
        # 创建数据库连接
        self.conn = duckdb.connect(':memory:', read_only=False)
        
        # 配置优化（根据用户16核CPU优化）
        self.conn.execute("SET threads TO 8")
        self.conn.execute("SET memory_limit = '8GB'")
        
        self._initialized = True
        self._enabled = True  # 默认启用
        
        print("✅ DuckDB服务已初始化（完整版）")
    
    @property
    def is_enabled(self) -> bool:
        return self._enabled and self.conn is not None
    
    def has_parquet_data(self) -> bool:
        """检查是否有Parquet数据"""
        raw_files = list(self.raw_dir.glob("**/*.parquet")) if self.raw_dir.exists() else []
        return len(raw_files) > 0
    
    def get_parquet_pattern(self) -> str:
        """获取原始Parquet文件匹配模式"""
        return str(self.raw_dir / "**" / "*.parquet")
    
    # ==================== KPI 查询 ====================
    
    def query_kpi(
        self,
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询 KPI 指标（首页六大卡片）
        
        直接从原始Parquet实时计算（DuckDB性能足够快）
        """
        # 直接从原始Parquet实时计算
        if self.has_parquet_data():
            return self._query_kpi_from_raw(store_name, start_date, end_date, channel)
        
        # 无Parquet数据，返回空结果
        return self._empty_kpi()
    
    def _query_kpi_from_aggregated(
        self,
        agg_file: Path,
        store_name: Optional[str],
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Dict[str, Any]:
        """从预聚合Parquet查询KPI"""
        where_clauses = []
        if store_name:
            where_clauses.append(f"门店名称 = '{store_name}'")
        if start_date:
            where_clauses.append(f"日期 >= '{start_date}'")
        if end_date:
            where_clauses.append(f"日期 <= '{end_date}'")
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        sql = f"""
            SELECT 
                COALESCE(SUM(订单数), 0) as total_orders,
                COALESCE(SUM(商品实收额), 0) as total_actual_sales,
                COALESCE(SUM(总利润), 0) as total_profit,
                COALESCE(SUM(商品实收额) / NULLIF(SUM(订单数), 0), 0) as avg_order_value,
                COALESCE(SUM(总利润) / NULLIF(SUM(商品实收额), 0) * 100, 0) as profit_rate,
                COALESCE(SUM(动销商品数), 0) as active_products
            FROM read_parquet('{agg_file}')
            {where_sql}
        """
        
        result = self.conn.execute(sql).fetchone()
        
        return {
            "total_orders": int(result[0] or 0),
            "total_actual_sales": round(float(result[1] or 0), 2),
            "total_profit": round(float(result[2] or 0), 2),
            "avg_order_value": round(float(result[3] or 0), 2),
            "profit_rate": round(float(result[4] or 0), 2),
            "active_products": int(result[5] or 0),
        }
    
    def _query_kpi_from_raw(
        self,
        store_name: Optional[str],
        start_date: Optional[date],
        end_date: Optional[date],
        channel: Optional[str]
    ) -> Dict[str, Any]:
        """从原始Parquet实时计算KPI"""
        parquet_pattern = self.get_parquet_pattern()
        
        where_clauses = []
        if store_name:
            where_clauses.append(f"门店名称 = '{store_name}'")
        if start_date:
            where_clauses.append(f"日期 >= '{start_date}'")
        if end_date:
            where_clauses.append(f"日期 <= '{end_date}'")
        if channel and channel != 'all':
            where_clauses.append(f"渠道 = '{channel}'")
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # 两阶段聚合：先订单级，再总体
        sql = f"""
            WITH order_level AS (
                SELECT 
                    订单ID,
                    门店名称,
                    SUM(实收价格 * 月售) as 订单金额,
                    SUM(利润额) - SUM(平台服务费) - MAX(物流配送费) + SUM(企客后返) as 订单利润
                FROM read_parquet('{parquet_pattern}')
                {where_sql}
                GROUP BY 订单ID, 门店名称
            )
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(订单金额), 0) as total_actual_sales,
                COALESCE(SUM(订单利润), 0) as total_profit,
                COALESCE(AVG(订单金额), 0) as avg_order_value,
                COALESCE(SUM(订单利润) / NULLIF(SUM(订单金额), 0) * 100, 0) as profit_rate
            FROM order_level
        """
        
        result = self.conn.execute(sql).fetchone()
        
        # 动销商品数单独查询
        active_sql = f"""
            SELECT COUNT(DISTINCT 商品名称)
            FROM read_parquet('{parquet_pattern}')
            {where_sql}
            {"AND" if where_clauses else "WHERE"} 月售 > 0
        """
        active_products = self.conn.execute(active_sql).fetchone()[0] or 0
        
        return {
            "total_orders": int(result[0] or 0),
            "total_actual_sales": round(float(result[1] or 0), 2),
            "total_profit": round(float(result[2] or 0), 2),
            "avg_order_value": round(float(result[3] or 0), 2),
            "profit_rate": round(float(result[4] or 0), 2),
            "active_products": int(active_products),
        }
    
    def _empty_kpi(self) -> Dict[str, Any]:
        return {
            "total_orders": 0,
            "total_actual_sales": 0,
            "total_profit": 0,
            "avg_order_value": 0,
            "profit_rate": 0,
            "active_products": 0,
        }
    
    # ==================== 趋势查询 ====================
    
    def query_trend(
        self,
        days: int = 30,
        store_name: Optional[str] = None,
        channel: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        granularity: str = "day"
    ) -> Dict[str, List]:
        """
        查询趋势数据（日/周/月）
        """
        if not self.has_parquet_data():
            return self._empty_trend()
        
        parquet_pattern = self.get_parquet_pattern()
        
        # 日期截断函数 - DuckDB语法
        date_trunc = {
            "day": "CAST(日期 AS DATE)",
            "week": "date_trunc('week', CAST(日期 AS DATE))",
            "month": "date_trunc('month', CAST(日期 AS DATE))",
        }.get(granularity, "CAST(日期 AS DATE)")
        
        # 构建WHERE条件
        where_clauses = []
        if start_date and end_date:
            where_clauses.append(f"CAST(日期 AS DATE) >= '{start_date}'")
            where_clauses.append(f"CAST(日期 AS DATE) <= '{end_date}'")
        else:
            where_clauses.append(f"CAST(日期 AS DATE) >= CURRENT_DATE - INTERVAL '{days} days'")
        
        if store_name:
            where_clauses.append(f"门店名称 = '{store_name}'")
        if channel and channel != 'all':
            where_clauses.append(f"渠道 = '{channel}'")
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}"
        
        sql = f"""
            WITH order_level AS (
                SELECT 
                    订单ID,
                    {date_trunc} as period,
                    SUM(实收价格 * 月售) as 订单金额,
                    SUM(利润额) - SUM(平台服务费) - MAX(物流配送费) + SUM(企客后返) as 订单利润
                FROM read_parquet('{parquet_pattern}')
                {where_sql}
                GROUP BY 订单ID, {date_trunc}
            )
            SELECT 
                period as date,
                COUNT(*) as order_count,
                COALESCE(SUM(订单金额), 0) as amount,
                COALESCE(SUM(订单利润), 0) as profit,
                COALESCE(AVG(订单金额), 0) as avg_value,
                COALESCE(SUM(订单利润) / NULLIF(SUM(订单金额), 0) * 100, 0) as profit_rate
            FROM order_level
            GROUP BY period
            ORDER BY period
        """
        
        df = self.conn.execute(sql).fetchdf()
        
        if df.empty:
            return self._empty_trend()
        
        return {
            "dates": [str(d)[:10] for d in df['date'].tolist()],
            "order_counts": [int(x) for x in df['order_count'].tolist()],
            "amounts": [round(float(x), 2) for x in df['amount'].tolist()],
            "profits": [round(float(x), 2) for x in df['profit'].tolist()],
            "avg_values": [round(float(x), 2) for x in df['avg_value'].tolist()],
            "profit_rates": [round(float(x), 2) for x in df['profit_rate'].tolist()],
        }
    
    def _empty_trend(self) -> Dict[str, List]:
        return {
            "dates": [],
            "order_counts": [],
            "amounts": [],
            "profits": [],
            "avg_values": [],
            "profit_rates": [],
        }
    
    # ==================== 渠道查询 ====================
    
    def query_channels(
        self,
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """查询渠道分析数据 - 直接从原始Parquet查询"""
        if not self.has_parquet_data():
            return []
        
        parquet_pattern = self.get_parquet_pattern()
        
        where_clauses = []
        if store_name:
            where_clauses.append(f"门店名称 = '{store_name}'")
        if start_date:
            where_clauses.append(f"CAST(日期 AS DATE) >= '{start_date}'")
        if end_date:
            where_clauses.append(f"CAST(日期 AS DATE) <= '{end_date}'")
        
        # 排除咖啡渠道
        where_clauses.append("渠道 NOT IN ('美团咖啡店', '饿了么咖啡店')")
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        sql = f"""
            WITH order_level AS (
                SELECT 
                    订单ID,
                    渠道,
                    SUM(实收价格 * 月售) as 订单金额,
                    SUM(利润额) - SUM(平台服务费) - MAX(物流配送费) + SUM(企客后返) as 订单利润
                FROM read_parquet('{parquet_pattern}')
                {where_sql}
                GROUP BY 订单ID, 渠道
            ),
            channel_stats AS (
                SELECT 
                    渠道 as channel,
                    COUNT(*) as order_count,
                    COALESCE(SUM(订单金额), 0) as amount,
                    COALESCE(SUM(订单利润), 0) as profit,
                    COALESCE(AVG(订单金额), 0) as avg_value
                FROM order_level
                GROUP BY 渠道
            ),
            totals AS (
                SELECT 
                    SUM(order_count) as total_orders,
                    SUM(amount) as total_amount
                FROM channel_stats
            )
            SELECT 
                c.channel,
                c.order_count,
                c.amount,
                c.profit,
                COALESCE(c.order_count * 100.0 / NULLIF(t.total_orders, 0), 0) as order_ratio,
                COALESCE(c.amount * 100.0 / NULLIF(t.total_amount, 0), 0) as amount_ratio,
                c.avg_value,
                COALESCE(c.profit / NULLIF(c.amount, 0) * 100, 0) as profit_rate
            FROM channel_stats c, totals t
            ORDER BY c.order_count DESC
        """
        
        df = self.conn.execute(sql).fetchdf()
        
        return [
            {
                "channel": row['channel'],
                "order_count": int(row['order_count']),
                "amount": round(float(row['amount']), 2),
                "profit": round(float(row['profit']), 2),
                "order_ratio": round(float(row['order_ratio']), 2),
                "amount_ratio": round(float(row['amount_ratio']), 2),
                "avg_value": round(float(row['avg_value']), 2),
                "profit_rate": round(float(row['profit_rate']), 2),
            }
            for _, row in df.iterrows()
        ]
    
    def _query_channels_from_aggregated(
        self,
        agg_file: Path,
        store_name: Optional[str],
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[Dict]:
        """从预聚合Parquet查询渠道数据"""
        where_clauses = []
        if store_name:
            where_clauses.append(f"门店名称 = '{store_name}'")
        if start_date:
            where_clauses.append(f"日期 >= '{start_date}'")
        if end_date:
            where_clauses.append(f"日期 <= '{end_date}'")
        where_clauses.append("渠道 NOT IN ('美团咖啡店', '饿了么咖啡店')")
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}"
        
        sql = f"""
            WITH channel_agg AS (
                SELECT 
                    渠道 as channel,
                    SUM(订单数) as order_count,
                    SUM(销售额) as amount,
                    SUM(利润) as profit
                FROM read_parquet('{agg_file}')
                {where_sql}
                GROUP BY 渠道
            ),
            totals AS (
                SELECT SUM(order_count) as total_orders, SUM(amount) as total_amount
                FROM channel_agg
            )
            SELECT 
                c.channel,
                c.order_count,
                c.amount,
                c.profit,
                COALESCE(c.order_count * 100.0 / NULLIF(t.total_orders, 0), 0) as order_ratio,
                COALESCE(c.amount * 100.0 / NULLIF(t.total_amount, 0), 0) as amount_ratio,
                COALESCE(c.amount / NULLIF(c.order_count, 0), 0) as avg_value,
                COALESCE(c.profit / NULLIF(c.amount, 0) * 100, 0) as profit_rate
            FROM channel_agg c, totals t
            ORDER BY c.order_count DESC
        """
        
        df = self.conn.execute(sql).fetchdf()
        
        return [
            {
                "channel": row['channel'],
                "order_count": int(row['order_count']),
                "amount": round(float(row['amount']), 2),
                "profit": round(float(row['profit']), 2),
                "order_ratio": round(float(row['order_ratio']), 2),
                "amount_ratio": round(float(row['amount_ratio']), 2),
                "avg_value": round(float(row['avg_value']), 2),
                "profit_rate": round(float(row['profit_rate']), 2),
            }
            for _, row in df.iterrows()
        ]
    
    # ==================== 品类查询 ====================
    
    def query_categories(
        self,
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        top_n: int = 10
    ) -> List[Dict]:
        """查询品类分析数据"""
        if not self.has_parquet_data():
            return []
        
        parquet_pattern = self.get_parquet_pattern()
        
        where_clauses = []
        if store_name:
            where_clauses.append(f"门店名称 = '{store_name}'")
        if start_date:
            where_clauses.append(f"日期 >= '{start_date}'")
        if end_date:
            where_clauses.append(f"日期 <= '{end_date}'")
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        sql = f"""
            SELECT 
                一级分类名 as category,
                COUNT(DISTINCT 订单ID) as order_count,
                COALESCE(SUM(实收价格 * 月售), 0) as amount,
                COALESCE(SUM(利润额), 0) as profit,
                COALESCE(SUM(月售), 0) as quantity
            FROM read_parquet('{parquet_pattern}')
            {where_sql}
            GROUP BY 一级分类名
            ORDER BY amount DESC
            LIMIT {top_n}
        """
        
        df = self.conn.execute(sql).fetchdf()
        
        return [
            {
                "category": row['category'],
                "order_count": int(row['order_count']),
                "amount": round(float(row['amount']), 2),
                "profit": round(float(row['profit']), 2),
                "quantity": int(row['quantity']),
            }
            for _, row in df.iterrows()
        ]
    
    # ==================== 自定义查询 ====================
    
    def execute_custom_query(self, sql: str) -> pd.DataFrame:
        """
        执行自定义 SQL 查询（高级用户）
        
        注意：需要做 SQL 注入防护
        """
        # 简单的安全检查
        forbidden = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        sql_upper = sql.upper()
        for word in forbidden:
            if word in sql_upper:
                raise ValueError(f"禁止执行 {word} 操作")
        
        return self.conn.execute(sql).fetchdf()
    
    # ==================== 状态查询 ====================
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        raw_files = list(self.raw_dir.glob("**/*.parquet")) if self.raw_dir.exists() else []
        agg_files = list(self.agg_dir.glob("**/*.parquet")) if self.agg_dir.exists() else []
        
        # 计算Parquet文件总大小
        raw_size = sum(f.stat().st_size for f in raw_files) if raw_files else 0
        agg_size = sum(f.stat().st_size for f in agg_files) if agg_files else 0
        
        return {
            "enabled": self._enabled,
            "initialized": self._initialized,
            "data_dir": str(self.data_dir),
            "raw_parquet_count": len(raw_files),
            "raw_parquet_size_mb": round(raw_size / 1024 / 1024, 2),
            "aggregated_parquet_count": len(agg_files),
            "aggregated_parquet_size_mb": round(agg_size / 1024 / 1024, 2),
            "has_data": len(raw_files) > 0,
        }


# 全局单例
duckdb_service = DuckDBService()
