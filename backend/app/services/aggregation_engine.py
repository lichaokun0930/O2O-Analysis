# -*- coding: utf-8 -*-
"""
配置驱动的预聚合表引擎

根据 aggregation_config.py 中的配置自动生成 SQL 并执行同步。
新增预聚合表只需添加配置，无需修改此文件。
"""

import sys
from pathlib import Path
from typing import List, Optional
from sqlalchemy import text

APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from .aggregation_config import (
    AGGREGATION_CONFIGS, 
    AggregationConfig, 
    get_all_table_names,
    get_config
)


class AggregationEngine:
    """配置驱动的预聚合表引擎"""
    
    @staticmethod
    def sync_all_tables(store_names: List[str], session=None):
        """
        同步所有预聚合表
        
        Args:
            store_names: 需要同步的门店列表
            session: 数据库会话（可选，不传则自动创建）
        """
        own_session = session is None
        if own_session:
            session = SessionLocal()
        
        try:
            for table_name in get_all_table_names():
                AggregationEngine.sync_table(table_name, store_names, session)
            
            if own_session:
                session.commit()
        except Exception as e:
            if own_session:
                session.rollback()
            raise e
        finally:
            if own_session:
                session.close()
    
    @staticmethod
    def sync_table(table_name: str, store_names: List[str], session=None):
        """
        同步单个预聚合表
        
        Args:
            table_name: 表名
            store_names: 需要同步的门店列表
            session: 数据库会话
        """
        config = get_config(table_name)
        if not config:
            print(f"   ⚠️ 未找到表配置: {table_name}")
            return
        
        own_session = session is None
        if own_session:
            session = SessionLocal()
        
        try:
            store_list = "', '".join(store_names)
            
            # 1. 删除旧数据
            delete_sql = f"DELETE FROM {table_name} WHERE store_name IN ('{store_list}')"
            result = session.execute(text(delete_sql))
            if result.rowcount > 0:
                print(f"   🗑️ {table_name}: 删除 {result.rowcount} 条")
            
            # 2. 生成并执行插入 SQL
            insert_sql = AggregationEngine._generate_insert_sql(config, store_list)
            session.execute(text(insert_sql))
            
            # 3. 更新派生字段
            if config.derived_fields:
                update_sql = AggregationEngine._generate_update_sql(config, store_list)
                session.execute(text(update_sql))
            
            if own_session:
                session.commit()
            
            # 统计结果
            count_result = session.execute(
                text(f"SELECT COUNT(*) FROM {table_name} WHERE store_name IN ('{store_list}')")
            )
            count = count_result.scalar()
            print(f"   ✅ {table_name}: {count} 条")
            
        except Exception as e:
            print(f"   ❌ {table_name}: {e}")
            if own_session:
                session.rollback()
        finally:
            if own_session:
                session.close()
    
    @staticmethod
    def _generate_insert_sql(config: AggregationConfig, store_list: str) -> str:
        """
        根据配置生成 INSERT SQL
        
        对于订单级字段（is_order_level=True），需要先按订单聚合再汇总：
        1. 子查询：按 order_id 聚合，取 MAX
        2. 外层查询：按目标维度聚合，取 SUM
        """
        
        # 检查是否有订单级字段
        has_order_level_fields = any(f.is_order_level for f in config.fields)
        
        if has_order_level_fields and config.order_level_first:
            return AggregationEngine._generate_order_level_insert_sql(config, store_list)
        else:
            return AggregationEngine._generate_simple_insert_sql(config, store_list)
    
    @staticmethod
    def _generate_simple_insert_sql(config: AggregationConfig, store_list: str) -> str:
        """生成简单的 INSERT SQL（无订单级字段）"""
        
        # 提取目标字段名
        target_fields = [f.name for f in config.fields]
        
        # 提取分组字段名（去掉 AS 别名部分用于 SELECT）
        group_by_selects = []
        group_by_names = []
        for g in config.group_by:
            if " as " in g.lower():
                # 有别名，如 "DATE(date) as summary_date"
                parts = g.lower().split(" as ")
                group_by_selects.append(g)
                group_by_names.append(parts[1].strip())
            else:
                group_by_selects.append(g)
                group_by_names.append(g)
        
        # 生成 SELECT 字段
        select_fields = []
        for g in group_by_selects:
            select_fields.append(g)
        
        for f in config.fields:
            if f.agg_func == "COUNT_DISTINCT":
                select_fields.append(f"COUNT(DISTINCT {f.source}) as {f.name}")
            elif f.agg_func == "FIRST":
                # PostgreSQL 没有 FIRST，用子查询或 MIN
                select_fields.append(f"MIN({f.source}) as {f.name}")
            else:
                select_fields.append(f"{f.agg_func}({f.source}) as {f.name}")
        
        # 生成 GROUP BY（只用字段名，不用别名）
        group_by_clause = []
        for g in config.group_by:
            if " as " in g.lower():
                # 提取表达式部分
                expr = g.lower().split(" as ")[0].strip()
                # 还原大小写
                for orig in config.group_by:
                    if orig.lower().startswith(expr):
                        group_by_clause.append(orig.split(" as ")[0].strip() if " as " in orig.lower() else orig)
                        break
            else:
                group_by_clause.append(g)
        
        # 生成 INSERT 字段列表
        insert_fields = group_by_names + target_fields
        
        sql = f"""
        INSERT INTO {config.table_name} ({', '.join(insert_fields)})
        SELECT {', '.join(select_fields)}
        FROM orders
        WHERE store_name IN ('{store_list}')
        """
        
        if config.filter_condition:
            sql += f" AND {config.filter_condition}"
        
        sql += f" GROUP BY {', '.join(group_by_clause)}"
        
        return sql
    
    @staticmethod
    def _generate_order_level_insert_sql(config: AggregationConfig, store_list: str) -> str:
        """
        生成带订单级聚合的 INSERT SQL
        
        两层聚合：
        1. 内层：按 order_id + 分组维度聚合，订单级字段取 MAX
        2. 外层：按分组维度聚合，订单级字段取 SUM
        """
        
        # 提取分组字段
        group_by_selects = []
        group_by_names = []
        group_by_exprs = []  # 用于 GROUP BY 子句
        
        for g in config.group_by:
            if " as " in g.lower():
                parts = g.lower().split(" as ")
                expr = g.split(" as ")[0].strip() if " as " in g else g
                alias = parts[1].strip()
                group_by_selects.append(g)
                group_by_names.append(alias)
                group_by_exprs.append(expr)
            else:
                group_by_selects.append(g)
                group_by_names.append(g)
                group_by_exprs.append(g)
        
        # 内层查询：按 order_id + 分组维度聚合
        inner_select = ["order_id"]
        for g in group_by_selects:
            inner_select.append(g)
        
        for f in config.fields:
            if f.is_order_level:
                # 订单级字段：内层取 MAX
                inner_select.append(f"MAX({f.source}) as {f.name}")
            elif f.agg_func == "COUNT_DISTINCT":
                # COUNT_DISTINCT 在内层也需要处理
                inner_select.append(f"COUNT(DISTINCT {f.source}) as {f.name}")
            else:
                inner_select.append(f"{f.agg_func}({f.source}) as {f.name}")
        
        inner_group_by = ["order_id"] + group_by_exprs
        
        # 外层查询：按分组维度聚合
        outer_select = []
        for name in group_by_names:
            outer_select.append(name)
        
        for f in config.fields:
            if f.is_order_level:
                # 订单级字段：外层取 SUM
                outer_select.append(f"SUM({f.name}) as {f.name}")
            elif f.agg_func == "COUNT_DISTINCT":
                # COUNT_DISTINCT 在外层取 SUM（因为内层已经去重）
                outer_select.append(f"SUM({f.name}) as {f.name}")
            else:
                outer_select.append(f"SUM({f.name}) as {f.name}")
        
        # 生成 INSERT 字段列表
        target_fields = [f.name for f in config.fields]
        insert_fields = group_by_names + target_fields
        
        # 构建完整 SQL
        sql = f"""
        INSERT INTO {config.table_name} ({', '.join(insert_fields)})
        SELECT {', '.join(outer_select)}
        FROM (
            SELECT {', '.join(inner_select)}
            FROM orders
            WHERE store_name IN ('{store_list}')
        """
        
        if config.filter_condition:
            sql += f" AND {config.filter_condition}"
        
        sql += f"""
            GROUP BY {', '.join(inner_group_by)}
        ) order_agg
        GROUP BY {', '.join(group_by_names)}
        """
        
        return sql
    
    @staticmethod
    def _generate_update_sql(config: AggregationConfig, store_list: str) -> str:
        """根据配置生成 UPDATE SQL（更新派生字段）"""
        
        set_clauses = []
        for df in config.derived_fields:
            set_clauses.append(f"{df.name} = {df.formula}")
        
        sql = f"""
        UPDATE {config.table_name} SET
            {', '.join(set_clauses)}
        WHERE store_name IN ('{store_list}')
        """
        
        return sql
    
    @staticmethod
    def check_table_exists(table_name: str) -> bool:
        """检查表是否存在"""
        session = SessionLocal()
        try:
            session.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
            return True
        except:
            return False
        finally:
            session.close()
    
    @staticmethod
    def get_table_count(table_name: str, store_name: Optional[str] = None) -> int:
        """获取表记录数"""
        session = SessionLocal()
        try:
            sql = f"SELECT COUNT(*) FROM {table_name}"
            if store_name:
                sql += f" WHERE store_name = '{store_name}'"
            result = session.execute(text(sql))
            return result.scalar() or 0
        except:
            return 0
        finally:
            session.close()


# 单例
aggregation_engine = AggregationEngine()
