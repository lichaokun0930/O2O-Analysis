# -*- coding: utf-8 -*-
"""
预聚合表一致性检查服务

功能：
1. 后端启动时自检：检查订单表和预聚合表的门店是否一致
2. 数据导入后自检：确保新导入的门店数据被同步到预聚合表
3. 定期自检：每小时检查一次数据一致性
4. 按需修复：发现不一致时自动同步缺失的门店数据

设计原则：
- 自动化：无需人工干预
- 非阻塞：异步执行，不影响主流程
- 容错：单个门店同步失败不影响其他门店
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
import threading

APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from database.connection import SessionLocal


class AggregationConsistencyService:
    """预聚合表一致性检查服务"""
    
    def __init__(self):
        self._last_check_time: Optional[datetime] = None
        self._check_lock = threading.Lock()
        self._is_syncing = False
    
    def check_consistency(self) -> Dict:
        """
        检查订单表和预聚合表的一致性
        
        Returns:
            {
                "consistent": bool,
                "order_stores": ["门店1", "门店2", ...],
                "aggregation_stores": ["门店1", ...],
                "missing_stores": ["门店2", ...],  # 订单表有但预聚合表没有
                "orphan_stores": [...],  # 预聚合表有但订单表没有
                "store_order_counts": {"门店1": 100, ...},  # 订单表中各门店订单数
                "store_agg_counts": {"门店1": 50, ...},  # 预聚合表中各门店记录数
            }
        """
        session = SessionLocal()
        try:
            # 1. 获取订单表中的门店列表和订单数
            order_result = session.execute(text("""
                SELECT store_name, COUNT(DISTINCT order_id) as order_count
                FROM orders 
                WHERE store_name IS NOT NULL
                GROUP BY store_name
            """))
            order_stores = {}
            for row in order_result.fetchall():
                order_stores[row[0]] = row[1]
            
            # 2. 获取预聚合表中的门店列表和记录数
            agg_result = session.execute(text("""
                SELECT store_name, SUM(order_count) as total_orders
                FROM store_daily_summary
                GROUP BY store_name
            """))
            agg_stores = {}
            for row in agg_result.fetchall():
                agg_stores[row[0]] = row[1] or 0
            
            # 3. 计算差异
            order_store_set = set(order_stores.keys())
            agg_store_set = set(agg_stores.keys())
            
            missing_stores = order_store_set - agg_store_set  # 订单表有但预聚合表没有
            orphan_stores = agg_store_set - order_store_set   # 预聚合表有但订单表没有
            
            # 4. 检查数据量是否匹配（允许小误差）
            mismatched_stores = []
            for store in order_store_set & agg_store_set:
                order_count = order_stores[store]
                agg_count = agg_stores[store]
                # 如果差异超过 5%，认为不一致
                if order_count > 0 and abs(order_count - agg_count) / order_count > 0.05:
                    mismatched_stores.append({
                        "store": store,
                        "order_count": order_count,
                        "agg_count": agg_count,
                        "diff_percent": round((agg_count - order_count) / order_count * 100, 1)
                    })
            
            consistent = len(missing_stores) == 0 and len(orphan_stores) == 0 and len(mismatched_stores) == 0
            
            self._last_check_time = datetime.now()
            
            return {
                "consistent": consistent,
                "order_stores": list(order_stores.keys()),
                "aggregation_stores": list(agg_stores.keys()),
                "missing_stores": list(missing_stores),
                "orphan_stores": list(orphan_stores),
                "mismatched_stores": mismatched_stores,
                "store_order_counts": order_stores,
                "store_agg_counts": agg_stores,
                "check_time": self._last_check_time.isoformat()
            }
        finally:
            session.close()
    
    def sync_missing_stores(self, missing_stores: List[str] = None) -> Dict:
        """
        同步缺失的门店数据到预聚合表
        
        Args:
            missing_stores: 需要同步的门店列表，None 则自动检测
            
        Returns:
            {
                "synced_stores": ["门店1", ...],
                "failed_stores": [{"store": "门店2", "error": "..."}],
                "total_records": 1234
            }
        """
        if self._is_syncing:
            return {"error": "同步正在进行中，请稍后再试"}
        
        with self._check_lock:
            self._is_syncing = True
        
        try:
            # 如果没有指定门店，自动检测
            if missing_stores is None:
                check_result = self.check_consistency()
                missing_stores = check_result.get("missing_stores", [])
            
            if not missing_stores:
                return {
                    "synced_stores": [],
                    "failed_stores": [],
                    "total_records": 0,
                    "message": "没有需要同步的门店"
                }
            
            # 导入聚合引擎
            from .aggregation_engine import AggregationEngine
            
            synced_stores = []
            failed_stores = []
            total_records = 0
            
            print(f"🔄 开始同步 {len(missing_stores)} 个缺失门店的预聚合数据...")
            
            # 批量同步所有缺失门店
            try:
                AggregationEngine.sync_all_tables(missing_stores)
                synced_stores = missing_stores
                
                # 统计同步后的记录数
                session = SessionLocal()
                try:
                    store_list = "', '".join(missing_stores)
                    result = session.execute(text(f"""
                        SELECT SUM(order_count) FROM store_daily_summary 
                        WHERE store_name IN ('{store_list}')
                    """))
                    total_records = result.scalar() or 0
                finally:
                    session.close()
                    
                print(f"✅ 同步完成: {len(synced_stores)} 个门店, {total_records} 条记录")
                
            except Exception as e:
                print(f"❌ 批量同步失败: {e}")
                # 尝试逐个同步
                for store in missing_stores:
                    try:
                        AggregationEngine.sync_all_tables([store])
                        synced_stores.append(store)
                    except Exception as store_error:
                        failed_stores.append({
                            "store": store,
                            "error": str(store_error)
                        })
            
            return {
                "synced_stores": synced_stores,
                "failed_stores": failed_stores,
                "total_records": total_records
            }
        finally:
            with self._check_lock:
                self._is_syncing = False
    
    def check_and_repair(self) -> Dict:
        """
        检查一致性并自动修复
        
        Returns:
            {
                "check_result": {...},
                "repair_result": {...} or None
            }
        """
        print("🔍 检查预聚合表一致性...")
        check_result = self.check_consistency()
        
        if check_result["consistent"]:
            print(f"✅ 预聚合表一致: {len(check_result['order_stores'])} 个门店")
            return {
                "check_result": check_result,
                "repair_result": None
            }
        
        # 有不一致，需要修复
        missing = check_result.get("missing_stores", [])
        orphan = check_result.get("orphan_stores", [])
        mismatched = check_result.get("mismatched_stores", [])
        
        print(f"⚠️ 发现不一致:")
        if missing:
            print(f"   - 缺失门店: {missing}")
        if orphan:
            print(f"   - 孤立门店: {orphan}")
        if mismatched:
            print(f"   - 数据不匹配: {[m['store'] for m in mismatched]}")
        
        # 需要同步的门店 = 缺失的 + 数据不匹配的
        stores_to_sync = list(set(missing) | set(m['store'] for m in mismatched))
        
        if stores_to_sync:
            print(f"🔄 开始修复 {len(stores_to_sync)} 个门店...")
            repair_result = self.sync_missing_stores(stores_to_sync)
        else:
            repair_result = None
        
        # 清理孤立门店数据
        if orphan:
            print(f"🗑️ 清理 {len(orphan)} 个孤立门店的预聚合数据...")
            self._clean_orphan_stores(orphan)
        
        return {
            "check_result": check_result,
            "repair_result": repair_result
        }
    
    def _clean_orphan_stores(self, orphan_stores: List[str]):
        """清理孤立门店的预聚合数据"""
        if not orphan_stores:
            return
        
        session = SessionLocal()
        try:
            store_list = "', '".join(orphan_stores)
            tables = [
                'store_daily_summary',
                'store_hourly_summary', 
                'category_daily_summary',
                'delivery_summary',
                'product_daily_summary'
            ]
            
            for table in tables:
                try:
                    result = session.execute(text(f"""
                        DELETE FROM {table} WHERE store_name IN ('{store_list}')
                    """))
                    if result.rowcount > 0:
                        print(f"   🗑️ {table}: 删除 {result.rowcount} 条")
                except Exception as e:
                    print(f"   ⚠️ {table}: 清理失败 - {e}")
            
            session.commit()
        finally:
            session.close()


# 单例
aggregation_consistency_service = AggregationConsistencyService()


def check_and_repair_on_startup():
    """启动时检查并修复预聚合表（供 main.py 调用）"""
    try:
        result = aggregation_consistency_service.check_and_repair()
        return result
    except Exception as e:
        print(f"⚠️ 预聚合表一致性检查失败: {e}")
        return None
