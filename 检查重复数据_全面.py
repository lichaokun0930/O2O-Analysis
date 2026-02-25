# -*- coding: utf-8 -*-
"""
全面检查重复数据

检查所有门店是否存在重复导入的数据
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import text
import pandas as pd

def check_duplicate_imports():
    """检查是否有重复导入的数据"""
    print("=" * 70)
    print("【检查重复导入数据】")
    print("=" * 70)
    
    session = SessionLocal()
    try:
        # 检查是否有完全相同的行（除了id）
        sql = """
        SELECT 
            order_id,
            store_name,
            date,
            product_name,
            profit,
            platform_service_fee,
            delivery_fee,
            COUNT(*) as dup_count
        FROM orders
        GROUP BY order_id, store_name, date, product_name, profit, platform_service_fee, delivery_fee
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
        LIMIT 20
        """
        result = session.execute(text(sql))
        rows = result.fetchall()
        
        if rows:
            print(f"\n发现 {len(rows)} 组重复数据（显示前20组）:")
            total_dup = 0
            for row in rows:
                print(f"  订单 {row[0]} | {row[1]} | {row[3][:20]}... | 利润={row[4]:.2f} | 重复{row[7]}次")
                total_dup += row[7] - 1  # 减1是因为保留一条
            print(f"\n预计重复行数: {total_dup}+")
        else:
            print("没有发现完全重复的行")
        
        # 统计每个门店的数据量
        sql2 = """
        SELECT 
            store_name,
            COUNT(*) as total_rows,
            COUNT(DISTINCT order_id) as total_orders,
            ROUND(COUNT(*)::numeric / COUNT(DISTINCT order_id), 2) as avg_rows_per_order
        FROM orders
        GROUP BY store_name
        ORDER BY total_rows DESC
        """
        result2 = session.execute(text(sql2))
        rows2 = result2.fetchall()
        
        print(f"\n【各门店数据量统计】")
        print(f"{'门店名称':<30} {'总行数':>10} {'订单数':>10} {'平均行数':>10}")
        print("-" * 70)
        for row in rows2:
            print(f"{row[0]:<30} {row[1]:>10} {row[2]:>10} {row[3]:>10}")
        
        # 检查总体重复情况
        sql3 = """
        WITH dup_check AS (
            SELECT 
                order_id, store_name, date, product_name, profit, platform_service_fee, delivery_fee,
                ROW_NUMBER() OVER (
                    PARTITION BY order_id, store_name, date, product_name, profit, platform_service_fee, delivery_fee
                    ORDER BY id
                ) as rn
            FROM orders
        )
        SELECT COUNT(*) as dup_rows FROM dup_check WHERE rn > 1
        """
        result3 = session.execute(text(sql3))
        dup_count = result3.fetchone()[0]
        
        print(f"\n【总体重复统计】")
        print(f"  重复行数: {dup_count}")
        
        return dup_count
        
    finally:
        session.close()


def check_specific_store(store_name, start_date, end_date):
    """检查特定门店的重复情况"""
    print(f"\n" + "=" * 70)
    print(f"【检查 {store_name}】")
    print(f"日期: {start_date} ~ {end_date}")
    print("=" * 70)
    
    session = SessionLocal()
    try:
        # 检查该门店该日期范围内的重复
        sql = """
        WITH dup_check AS (
            SELECT 
                id,
                order_id, 
                product_name, 
                profit, 
                platform_service_fee, 
                delivery_fee,
                ROW_NUMBER() OVER (
                    PARTITION BY order_id, product_name, profit, platform_service_fee, delivery_fee
                    ORDER BY id
                ) as rn
            FROM orders
            WHERE store_name = :store_name
              AND date >= :start_date
              AND date <= :end_date
        )
        SELECT COUNT(*) as dup_rows FROM dup_check WHERE rn > 1
        """
        result = session.execute(text(sql), {
            'store_name': store_name,
            'start_date': start_date,
            'end_date': end_date
        })
        dup_count = result.fetchone()[0]
        
        print(f"重复行数: {dup_count}")
        
        # 获取总行数和订单数
        sql2 = """
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT order_id) as total_orders
        FROM orders
        WHERE store_name = :store_name
          AND date >= :start_date
          AND date <= :end_date
        """
        result2 = session.execute(text(sql2), {
            'store_name': store_name,
            'start_date': start_date,
            'end_date': end_date
        })
        row = result2.fetchone()
        print(f"总行数: {row[0]}, 订单数: {row[1]}")
        print(f"去重后应有行数: {row[0] - dup_count}")
        
        return dup_count
        
    finally:
        session.close()


def clean_duplicates_dry_run():
    """模拟清理重复数据（不实际删除）"""
    print(f"\n" + "=" * 70)
    print("【模拟清理重复数据】")
    print("=" * 70)
    
    session = SessionLocal()
    try:
        # 找出所有重复行的ID
        sql = """
        WITH dup_check AS (
            SELECT 
                id,
                order_id, 
                store_name,
                product_name, 
                profit, 
                platform_service_fee, 
                delivery_fee,
                ROW_NUMBER() OVER (
                    PARTITION BY order_id, store_name, product_name, profit, platform_service_fee, delivery_fee
                    ORDER BY id
                ) as rn
            FROM orders
        )
        SELECT id, order_id, store_name FROM dup_check WHERE rn > 1
        """
        result = session.execute(text(sql))
        rows = result.fetchall()
        
        print(f"需要删除的重复行数: {len(rows)}")
        
        if rows:
            # 按门店统计
            store_counts = {}
            for row in rows:
                store = row[2]
                store_counts[store] = store_counts.get(store, 0) + 1
            
            print(f"\n各门店重复行数:")
            for store, count in sorted(store_counts.items(), key=lambda x: -x[1]):
                print(f"  {store}: {count} 行")
        
        return len(rows)
        
    finally:
        session.close()


def actually_clean_duplicates():
    """实际清理重复数据"""
    print(f"\n" + "=" * 70)
    print("【实际清理重复数据】")
    print("=" * 70)
    
    session = SessionLocal()
    try:
        # 删除重复行（保留id最小的）
        sql = """
        DELETE FROM orders
        WHERE id IN (
            SELECT id FROM (
                SELECT 
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY order_id, store_name, product_name, profit, platform_service_fee, delivery_fee
                        ORDER BY id
                    ) as rn
                FROM orders
            ) t
            WHERE rn > 1
        )
        """
        result = session.execute(text(sql))
        deleted = result.rowcount
        session.commit()
        
        print(f"✅ 已删除 {deleted} 行重复数据")
        return deleted
        
    except Exception as e:
        session.rollback()
        print(f"❌ 删除失败: {e}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    # 1. 全面检查
    total_dup = check_duplicate_imports()
    
    # 2. 检查淮安店
    check_specific_store(
        "惠宜选-淮安生态新城店",
        "2026-01-12",
        "2026-01-18"
    )
    
    # 3. 检查兴化店
    check_specific_store(
        "惠宜选-泰州兴化店",
        "2026-01-16",
        "2026-01-22"
    )
    
    # 4. 模拟清理
    to_delete = clean_duplicates_dry_run()
    
    # 5. 询问是否实际清理
    if to_delete > 0:
        print(f"\n" + "=" * 70)
        print(f"发现 {to_delete} 行重复数据需要清理")
        print("=" * 70)
        
        # 自动清理
        actually_clean_duplicates()
