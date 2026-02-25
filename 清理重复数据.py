# -*- coding: utf-8 -*-
"""
清理数据库中的重复数据

问题：数据被重复导入，导致所有计算都翻倍
解决：删除重复的行，只保留每组重复数据中的第一条
"""

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent / "backend" / "app"
sys.path.insert(0, str(APP_DIR))

from database.connection import SessionLocal
from sqlalchemy import text


def analyze_duplicates():
    """分析重复数据情况"""
    session = SessionLocal()
    
    print("=" * 60)
    print("分析重复数据")
    print("=" * 60)
    
    # 统计重复情况
    sql = """
    WITH duplicates AS (
        SELECT 
            store_name,
            order_id, 
            product_name, 
            actual_price, 
            COUNT(*) as cnt
        FROM orders
        GROUP BY store_name, order_id, product_name, actual_price
        HAVING COUNT(*) > 1
    )
    SELECT 
        store_name,
        COUNT(*) as duplicate_groups,
        SUM(cnt) as total_rows,
        SUM(cnt - 1) as extra_rows
    FROM duplicates
    GROUP BY store_name
    ORDER BY extra_rows DESC
    """
    
    result = session.execute(text(sql))
    rows = list(result)
    
    total_extra = 0
    print("\n门店                            | 重复组数 | 涉及行数 | 多余行数")
    print("-" * 70)
    for row in rows:
        print(f"{row[0]:30} | {row[1]:>8} | {row[2]:>8} | {row[3]:>8}")
        total_extra += row[3]
    
    print("-" * 70)
    print(f"总计多余行数: {total_extra}")
    
    session.close()
    return total_extra


def clean_duplicates(dry_run=True):
    """
    清理重复数据
    
    策略：保留每组重复数据中 id 最小的那条，删除其他的
    """
    session = SessionLocal()
    
    print("\n" + "=" * 60)
    print("清理重复数据" + (" (预览模式)" if dry_run else " (执行模式)"))
    print("=" * 60)
    
    # 找出需要删除的行（保留每组中id最小的）
    sql_find = """
    WITH ranked AS (
        SELECT 
            id,
            order_id,
            product_name,
            actual_price,
            ROW_NUMBER() OVER (
                PARTITION BY order_id, product_name, actual_price 
                ORDER BY id
            ) as rn
        FROM orders
    )
    SELECT id FROM ranked WHERE rn > 1
    """
    
    result = session.execute(text(sql_find))
    ids_to_delete = [row[0] for row in result]
    
    print(f"\n需要删除的重复行数: {len(ids_to_delete)}")
    
    if dry_run:
        print("\n⚠️ 预览模式，未实际删除数据")
        print("如需执行删除，请运行: clean_duplicates(dry_run=False)")
    else:
        if len(ids_to_delete) > 0:
            # 分批删除，避免一次删除太多
            batch_size = 10000
            deleted = 0
            
            for i in range(0, len(ids_to_delete), batch_size):
                batch = ids_to_delete[i:i+batch_size]
                ids_str = ','.join(str(id) for id in batch)
                sql_delete = f"DELETE FROM orders WHERE id IN ({ids_str})"
                result = session.execute(text(sql_delete))
                deleted += result.rowcount
                print(f"  已删除: {deleted}/{len(ids_to_delete)}")
            
            session.commit()
            print(f"\n✅ 成功删除 {deleted} 条重复数据")
        else:
            print("\n✅ 没有需要删除的重复数据")
    
    session.close()
    return len(ids_to_delete)


def verify_after_clean():
    """验证清理后的数据"""
    session = SessionLocal()
    
    print("\n" + "=" * 60)
    print("验证清理后的数据")
    print("=" * 60)
    
    # 检查是否还有重复
    sql = """
    SELECT COUNT(*) FROM (
        SELECT order_id, product_name, actual_price
        FROM orders
        GROUP BY order_id, product_name, actual_price
        HAVING COUNT(*) > 1
    ) t
    """
    result = session.execute(text(sql))
    remaining = result.scalar()
    
    if remaining == 0:
        print("✅ 没有重复数据")
    else:
        print(f"⚠️ 仍有 {remaining} 组重复数据")
    
    # 统计各门店数据
    sql2 = """
    SELECT 
        store_name,
        COUNT(*) as total_rows,
        COUNT(DISTINCT order_id) as unique_orders
    FROM orders
    GROUP BY store_name
    ORDER BY store_name
    """
    result2 = session.execute(text(sql2))
    
    print("\n门店数据统计:")
    print("门店                            | 总行数   | 订单数")
    print("-" * 60)
    for row in result2:
        print(f"{row[0]:30} | {row[1]:>8} | {row[2]:>8}")
    
    session.close()


if __name__ == "__main__":
    # 1. 分析重复数据
    extra_rows = analyze_duplicates()
    
    if extra_rows > 0:
        # 2. 预览要删除的数据
        clean_duplicates(dry_run=True)
        
        # 3. 询问是否执行
        print("\n" + "=" * 60)
        response = input("是否执行删除？(输入 yes 确认): ")
        if response.lower() == 'yes':
            clean_duplicates(dry_run=False)
            verify_after_clean()
        else:
            print("已取消")
    else:
        print("\n✅ 没有重复数据需要清理")
