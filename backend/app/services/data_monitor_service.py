# -*- coding: utf-8 -*-
"""
数据量监控服务

监控订单数据量，当达到阈值时提醒升级到千万级架构
"""
from datetime import datetime
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func


# 数据量阈值配置
THRESHOLDS = {
    "warning": 1_000_000,      # 100万：建议开始准备Parquet归档
    "critical": 3_000_000,     # 300万：建议启用DuckDB
    "urgent": 5_000_000,       # 500万：强烈建议完整实施千万级方案
}


class DataMonitorService:
    """数据量监控服务"""
    
    def __init__(self):
        self._last_check = None
        self._last_count = 0
    
    def get_data_stats(self) -> Dict[str, Any]:
        """
        获取数据统计信息
        
        Returns:
            包含数据量、增长率、建议等信息的字典
        """
        session = SessionLocal()
        try:
            # 总订单数
            total_orders = session.query(func.count(Order.id)).scalar() or 0
            
            # 总记录数（商品级）
            total_records = session.query(func.count(Order.id)).scalar() or 0
            
            # 唯一订单数
            unique_orders = session.query(func.count(func.distinct(Order.order_id))).scalar() or 0
            
            # 门店数
            store_count = session.query(func.count(func.distinct(Order.store_name))).scalar() or 0
            
            # 日期范围
            min_date = session.query(func.min(Order.date)).scalar()
            max_date = session.query(func.max(Order.date)).scalar()
            
            # 最近7天新增
            from datetime import timedelta
            if max_date:
                week_ago = max_date - timedelta(days=7)
                recent_records = session.query(func.count(Order.id)).filter(
                    Order.date > week_ago
                ).scalar() or 0
            else:
                recent_records = 0
            
            # 计算日均增长
            if min_date and max_date and min_date != max_date:
                days = (max_date - min_date).days or 1
                daily_growth = total_records / days
            else:
                daily_growth = 0
            
            # 预估达到阈值的时间
            predictions = {}
            for level, threshold in THRESHOLDS.items():
                if total_records >= threshold:
                    predictions[level] = "已达到"
                elif daily_growth > 0:
                    days_to_reach = (threshold - total_records) / daily_growth
                    predictions[level] = f"约{int(days_to_reach)}天后"
                else:
                    predictions[level] = "无法预估"
            
            # 生成建议
            recommendation = self._generate_recommendation(total_records)
            
            self._last_check = datetime.now()
            self._last_count = total_records
            
            return {
                "total_records": total_records,
                "unique_orders": unique_orders,
                "store_count": store_count,
                "date_range": {
                    "start": str(min_date) if min_date else None,
                    "end": str(max_date) if max_date else None,
                },
                "recent_7days": recent_records,
                "daily_growth": round(daily_growth, 0),
                "thresholds": THRESHOLDS,
                "predictions": predictions,
                "recommendation": recommendation,
                "check_time": datetime.now().isoformat(),
            }
        finally:
            session.close()
    
    def _generate_recommendation(self, total_records: int) -> Dict[str, Any]:
        """生成优化建议"""
        if total_records >= THRESHOLDS["urgent"]:
            return {
                "level": "urgent",
                "message": "🔴 数据量已超过500万，强烈建议立即实施千万级优化方案",
                "actions": [
                    "启用DuckDB查询引擎",
                    "实施完整Parquet存储方案",
                    "切换到API v2接口",
                ]
            }
        elif total_records >= THRESHOLDS["critical"]:
            return {
                "level": "critical",
                "message": "🟠 数据量已超过300万，建议启用DuckDB查询引擎",
                "actions": [
                    "实施DuckDB查询服务",
                    "开始Parquet数据归档",
                ]
            }
        elif total_records >= THRESHOLDS["warning"]:
            return {
                "level": "warning",
                "message": "🟡 数据量已超过100万，建议开始准备Parquet归档",
                "actions": [
                    "开始历史数据Parquet归档",
                    "配置定时同步任务",
                ]
            }
        else:
            return {
                "level": "normal",
                "message": "✅ 当前数据量正常，预聚合表架构足以支撑",
                "actions": []
            }
    
    def check_and_alert(self) -> Optional[str]:
        """
        检查数据量并返回告警信息（如果有）
        
        Returns:
            告警信息字符串，无告警返回None
        """
        stats = self.get_data_stats()
        rec = stats["recommendation"]
        
        if rec["level"] in ["warning", "critical", "urgent"]:
            return rec["message"]
        return None


# 全局单例
data_monitor_service = DataMonitorService()
