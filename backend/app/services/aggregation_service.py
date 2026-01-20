# -*- coding: utf-8 -*-
"""
预聚合表查询服务

提供基于预聚合表的高性能查询接口，
替代原始订单表的实时聚合查询。

预聚合表：
- store_daily_summary: 门店日汇总
- store_hourly_summary: 门店小时汇总
- category_daily_summary: 品类日汇总
- delivery_summary: 配送分析汇总
- product_daily_summary: 商品日汇总
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from sqlalchemy import text
import pandas as pd

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal

# 检查预聚合表是否可用
AGGREGATION_TABLES_AVAILABLE = False
AVAILABLE_TABLES = set()

def check_aggregation_tables():
    """检查预聚合表是否可用"""
    global AGGREGATION_TABLES_AVAILABLE, AVAILABLE_TABLES
    
    tables = [
        'store_daily_summary',
        'store_hourly_summary', 
        'category_daily_summary',
        'delivery_summary',
        'product_daily_summary'
    ]
    
    session = SessionLocal()
    try:
        for table in tables:
            try:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                if count and count > 0:
                    AVAILABLE_TABLES.add(table)
            except:
                pass
        
        AGGREGATION_TABLES_AVAILABLE = len(AVAILABLE_TABLES) > 0
        if AGGREGATION_TABLES_AVAILABLE:
            print(f"✅ 预聚合表可用: {AVAILABLE_TABLES}")
        else:
            print("⚠️ 预聚合表不可用")
    finally:
        session.close()

# 启动时检查
check_aggregation_tables()


class AggregationService:
    """预聚合表查询服务"""
    
    @staticmethod
    def get_store_overview(
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从预聚合表获取门店经营总览数据
        
        返回六大核心指标 + GMV和营销成本率：
        - total_orders: 订单总数
        - total_actual_sales: 商品实收额
        - total_profit: 总利润
        - avg_order_value: 平均客单价
        - profit_rate: 总利润率
        - active_products: 动销商品数
        - gmv: 营业额（GMV）
        - marketing_cost: 营销成本（7字段）
        - marketing_cost_rate: 营销成本率
        """
        if 'store_daily_summary' not in AVAILABLE_TABLES:
            return None
        
        session = SessionLocal()
        try:
            # 主查询：获取订单数、收入、利润、GMV、营销成本
            sql = """
                SELECT 
                    SUM(order_count) as total_orders,
                    SUM(total_revenue) as total_revenue,
                    SUM(total_profit) as total_profit,
                    SUM(COALESCE(gmv, 0)) as total_gmv,
                    SUM(total_marketing_cost) as total_marketing_cost
                FROM store_daily_summary
                WHERE 1=1
            """
            params = {}
            
            if store_name:
                sql += " AND store_name = :store_name"
                params['store_name'] = store_name
            if start_date:
                sql += " AND summary_date >= :start_date"
                params['start_date'] = start_date
            if end_date:
                sql += " AND summary_date <= :end_date"
                params['end_date'] = end_date
            if channel and channel in ['美团', '饿了么', '京东']:
                sql += " AND channel = :channel"
                params['channel'] = channel
            
            result = session.execute(text(sql), params)
            row = result.fetchone()
            
            if not row or not row[0]:
                return {
                    "total_orders": 0,
                    "total_actual_sales": 0,
                    "total_profit": 0,
                    "avg_order_value": 0,
                    "profit_rate": 0,
                    "active_products": 0,
                    "gmv": 0,
                    "marketing_cost": 0,
                    "marketing_cost_rate": 0
                }
            
            total_orders = int(row[0]) if row[0] else 0
            total_revenue = float(row[1]) if row[1] else 0
            total_profit = float(row[2]) if row[2] else 0
            total_gmv = float(row[3]) if row[3] else 0
            total_marketing_cost = float(row[4]) if row[4] else 0
            
            # 单独查询动销商品数（从原始订单表查询，跨日期去重）
            # 预聚合表无法准确存储这个值，因为它是跨日期去重的
            active_sql = """
                SELECT COUNT(DISTINCT product_name) 
                FROM orders
                WHERE quantity > 0
            """
            active_params = {}
            if store_name:
                active_sql += " AND store_name = :store_name"
                active_params['store_name'] = store_name
            if start_date:
                active_sql += " AND DATE(date) >= :start_date"
                active_params['start_date'] = start_date
            if end_date:
                active_sql += " AND DATE(date) <= :end_date"
                active_params['end_date'] = end_date
            
            active_result = session.execute(text(active_sql), active_params)
            active_row = active_result.fetchone()
            active_products = int(active_row[0]) if active_row and active_row[0] else 0
            
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
            profit_rate = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            # 营销成本率 = 营销成本 / GMV × 100%
            marketing_cost_rate = (total_marketing_cost / total_gmv * 100) if total_gmv > 0 else 0
            
            return {
                "total_orders": total_orders,
                "total_actual_sales": round(total_revenue, 2),
                "total_profit": round(total_profit, 2),
                "avg_order_value": round(avg_order_value, 2),
                "profit_rate": round(profit_rate, 2),
                "active_products": active_products,
                "gmv": round(total_gmv, 2),
                "marketing_cost": round(total_marketing_cost, 2),
                "marketing_cost_rate": round(marketing_cost_rate, 2)
            }
        finally:
            session.close()
    
    @staticmethod
    def get_daily_trend(
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        channel: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """从预聚合表获取日趋势数据"""
        if 'store_daily_summary' not in AVAILABLE_TABLES:
            return None
        
        session = SessionLocal()
        try:
            sql = """
                SELECT 
                    summary_date,
                    SUM(order_count) as orders,
                    SUM(total_revenue) as revenue,
                    SUM(total_profit) as profit
                FROM store_daily_summary
                WHERE 1=1
            """
            params = {}
            
            if store_name:
                sql += " AND store_name = :store_name"
                params['store_name'] = store_name
            if start_date:
                sql += " AND summary_date >= :start_date"
                params['start_date'] = start_date
            if end_date:
                sql += " AND summary_date <= :end_date"
                params['end_date'] = end_date
            if channel and channel in ['美团', '饿了么', '京东']:
                sql += " AND channel = :channel"
                params['channel'] = channel
            
            sql += " GROUP BY summary_date ORDER BY summary_date"
            
            result = session.execute(text(sql), params)
            rows = result.fetchall()
            
            return [
                {
                    "date": str(row[0]),
                    "orders": int(row[1]) if row[1] else 0,
                    "revenue": float(row[2]) if row[2] else 0,
                    "profit": float(row[3]) if row[3] else 0
                }
                for row in rows
            ]
        finally:
            session.close()

    
    @staticmethod
    def get_hourly_analysis(
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        channel: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """从预聚合表获取分时段分析数据"""
        if 'store_hourly_summary' not in AVAILABLE_TABLES:
            return None
        
        session = SessionLocal()
        try:
            sql = """
                SELECT 
                    hour_of_day,
                    SUM(order_count) as orders,
                    SUM(total_revenue) as revenue,
                    SUM(total_profit) as profit,
                    SUM(delivery_net_cost) as delivery_cost,
                    SUM(total_marketing_cost) as marketing_cost
                FROM store_hourly_summary
                WHERE 1=1
            """
            params = {}
            
            if store_name:
                sql += " AND store_name = :store_name"
                params['store_name'] = store_name
            if start_date:
                sql += " AND summary_date >= :start_date"
                params['start_date'] = start_date
            if end_date:
                sql += " AND summary_date <= :end_date"
                params['end_date'] = end_date
            if channel and channel in ['美团', '饿了么', '京东']:
                sql += " AND channel = :channel"
                params['channel'] = channel
            
            sql += " GROUP BY hour_of_day ORDER BY hour_of_day"
            
            result = session.execute(text(sql), params)
            rows = result.fetchall()
            
            return [
                {
                    "hour": int(row[0]),
                    "orders": int(row[1]) if row[1] else 0,
                    "revenue": float(row[2]) if row[2] else 0,
                    "profit": float(row[3]) if row[3] else 0,
                    "delivery_cost": float(row[4]) if row[4] else 0,
                    "marketing_cost": float(row[5]) if row[5] else 0
                }
                for row in rows
            ]
        finally:
            session.close()
    
    @staticmethod
    def get_category_analysis(
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        channel: Optional[str] = None,
        level: int = 1
    ) -> List[Dict[str, Any]]:
        """从预聚合表获取品类分析数据"""
        if 'category_daily_summary' not in AVAILABLE_TABLES:
            return None
        
        session = SessionLocal()
        try:
            category_col = "category_level1" if level == 1 else "category_level3"
            
            sql = f"""
                SELECT 
                    {category_col} as category,
                    SUM(order_count) as orders,
                    SUM(total_quantity) as quantity,
                    SUM(total_revenue) as revenue,
                    SUM(total_profit) as profit,
                    AVG(avg_discount) as avg_discount,
                    AVG(profit_margin) as profit_margin
                FROM category_daily_summary
                WHERE {category_col} IS NOT NULL AND {category_col} != ''
            """
            params = {}
            
            if store_name:
                sql += " AND store_name = :store_name"
                params['store_name'] = store_name
            if start_date:
                sql += " AND summary_date >= :start_date"
                params['start_date'] = start_date
            if end_date:
                sql += " AND summary_date <= :end_date"
                params['end_date'] = end_date
            if channel and channel in ['美团', '饿了么', '京东']:
                sql += " AND channel = :channel"
                params['channel'] = channel
            
            sql += f" GROUP BY {category_col} ORDER BY SUM(total_revenue) DESC"
            
            result = session.execute(text(sql), params)
            rows = result.fetchall()
            
            return [
                {
                    "category": row[0],
                    "orders": int(row[1]) if row[1] else 0,
                    "quantity": int(row[2]) if row[2] else 0,
                    "revenue": float(row[3]) if row[3] else 0,
                    "profit": float(row[4]) if row[4] else 0,
                    "avg_discount": float(row[5]) if row[5] else 10,
                    "profit_margin": float(row[6]) if row[6] else 0
                }
                for row in rows
            ]
        finally:
            session.close()

    
    @staticmethod
    def get_delivery_analysis(
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """从预聚合表获取配送分析数据"""
        if 'delivery_summary' not in AVAILABLE_TABLES:
            return None
        
        session = SessionLocal()
        try:
            # 按距离区间汇总
            sql = """
                SELECT 
                    distance_band,
                    MIN(distance_min) as min_dist,
                    MAX(distance_max) as max_dist,
                    SUM(order_count) as orders,
                    SUM(total_revenue) as revenue,
                    SUM(delivery_net_cost) as delivery_cost,
                    SUM(high_delivery_count) as high_delivery_orders
                FROM delivery_summary
                WHERE 1=1
            """
            params = {}
            
            if store_name:
                sql += " AND store_name = :store_name"
                params['store_name'] = store_name
            if start_date:
                sql += " AND summary_date >= :start_date"
                params['start_date'] = start_date
            if end_date:
                sql += " AND summary_date <= :end_date"
                params['end_date'] = end_date
            if channel and channel in ['美团', '饿了么', '京东']:
                sql += " AND channel = :channel"
                params['channel'] = channel
            
            sql += " GROUP BY distance_band ORDER BY MIN(distance_min)"
            
            result = session.execute(text(sql), params)
            rows = result.fetchall()
            
            by_distance = [
                {
                    "band": row[0],
                    "min_distance": float(row[1]) if row[1] else 0,
                    "max_distance": float(row[2]) if row[2] else 0,
                    "orders": int(row[3]) if row[3] else 0,
                    "revenue": float(row[4]) if row[4] else 0,
                    "delivery_cost": float(row[5]) if row[5] else 0,
                    "high_delivery_orders": int(row[6]) if row[6] else 0,
                    "avg_delivery_fee": float(row[5]) / int(row[3]) if row[3] and row[3] > 0 else 0
                }
                for row in rows
            ]
            
            # 按小时汇总
            sql2 = """
                SELECT 
                    hour_of_day,
                    SUM(order_count) as orders,
                    SUM(delivery_net_cost) as delivery_cost,
                    SUM(high_delivery_count) as high_delivery_orders
                FROM delivery_summary
                WHERE 1=1
            """
            
            if store_name:
                sql2 += " AND store_name = :store_name"
            if start_date:
                sql2 += " AND summary_date >= :start_date"
            if end_date:
                sql2 += " AND summary_date <= :end_date"
            if channel and channel in ['美团', '饿了么', '京东']:
                sql2 += " AND channel = :channel"
            
            sql2 += " GROUP BY hour_of_day ORDER BY hour_of_day"
            
            result2 = session.execute(text(sql2), params)
            rows2 = result2.fetchall()
            
            by_hour = [
                {
                    "hour": int(row[0]) if row[0] is not None else 0,
                    "orders": int(row[1]) if row[1] else 0,
                    "delivery_cost": float(row[2]) if row[2] else 0,
                    "high_delivery_orders": int(row[3]) if row[3] else 0
                }
                for row in rows2
            ]
            
            return {
                "by_distance": by_distance,
                "by_hour": by_hour
            }
        finally:
            session.close()
    
    @staticmethod
    def get_top_products(
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        channel: Optional[str] = None,
        limit: int = 20,
        sort_by: str = "quantity"
    ) -> List[Dict[str, Any]]:
        """从预聚合表获取商品销量排行"""
        if 'product_daily_summary' not in AVAILABLE_TABLES:
            return None
        
        session = SessionLocal()
        try:
            order_col = "SUM(total_quantity)" if sort_by == "quantity" else "SUM(total_revenue)"
            
            sql = f"""
                SELECT 
                    product_name,
                    category_level1,
                    SUM(order_count) as orders,
                    SUM(total_quantity) as quantity,
                    SUM(total_revenue) as revenue,
                    SUM(total_profit) as profit,
                    AVG(avg_price) as avg_price,
                    AVG(profit_margin) as profit_margin
                FROM product_daily_summary
                WHERE product_name IS NOT NULL AND product_name != ''
            """
            params = {}
            
            if store_name:
                sql += " AND store_name = :store_name"
                params['store_name'] = store_name
            if start_date:
                sql += " AND summary_date >= :start_date"
                params['start_date'] = start_date
            if end_date:
                sql += " AND summary_date <= :end_date"
                params['end_date'] = end_date
            if channel and channel in ['美团', '饿了么', '京东']:
                sql += " AND channel = :channel"
                params['channel'] = channel
            
            sql += f" GROUP BY product_name, category_level1 ORDER BY {order_col} DESC LIMIT :limit"
            params['limit'] = limit
            
            result = session.execute(text(sql), params)
            rows = result.fetchall()
            
            return [
                {
                    "product_name": row[0],
                    "category": row[1],
                    "orders": int(row[2]) if row[2] else 0,
                    "quantity": int(row[3]) if row[3] else 0,
                    "revenue": float(row[4]) if row[4] else 0,
                    "profit": float(row[5]) if row[5] else 0,
                    "avg_price": float(row[6]) if row[6] else 0,
                    "profit_margin": float(row[7]) if row[7] else 0
                }
                for row in rows
            ]
        finally:
            session.close()


# 创建单例实例
aggregation_service = AggregationService()
