# -*- coding: utf-8 -*-
"""
检查各字段是订单级还是商品级

订单级字段：同一订单的所有商品行值相同，应该用 first 聚合
商品级字段：同一订单的不同商品行值不同，应该用 sum 聚合
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import text
import pandas as pd

def check_field_level():
    """检查各字段是订单级还是商品级"""
    
    session = SessionLocal()
    
    # 找一个有多个商品的订单
    sql = """
    SELECT order_id, COUNT(*) as item_count
    FROM orders
    WHERE store_name = '惠宜选-泰州兴化店'
    GROUP BY order_id
    HAVING COUNT(*) > 3
    LIMIT 5
    """
    
    result = session.execute(text(sql))
    orders = result.fetchall()
    
    print("=" * 80)
    print("检查字段级别（订单级 vs 商品级）")
    print("=" * 80)
    
    for order_id, item_count in orders:
        print(f"\n订单ID: {order_id} (包含 {item_count} 个商品)")
        print("-" * 60)
        
        # 获取该订单的所有商品行
        sql2 = """
        SELECT 
            product_name,
            profit,
            platform_service_fee,
            delivery_fee,
            corporate_rebate,
            actual_price,
            quantity
        FROM orders
        WHERE order_id = :order_id
        """
        
        result2 = session.execute(text(sql2), {'order_id': order_id})
        rows = result2.fetchall()
        
        # 检查各字段值
        profits = [r[1] for r in rows]
        platform_fees = [r[2] for r in rows]
        delivery_fees = [r[3] for r in rows]
        rebates = [r[4] for r in rows]
        prices = [r[5] for r in rows]
        quantities = [r[6] for r in rows]
        
        print(f"  利润额: {profits}")
        print(f"    → 值{'相同' if len(set(profits)) == 1 else '不同'} → {'订单级(first)' if len(set(profits)) == 1 else '商品级(sum)'}")
        
        print(f"  平台服务费: {platform_fees}")
        print(f"    → 值{'相同' if len(set(platform_fees)) == 1 else '不同'} → {'订单级(first)' if len(set(platform_fees)) == 1 else '商品级(sum)'}")
        
        print(f"  物流配送费: {delivery_fees}")
        print(f"    → 值{'相同' if len(set(delivery_fees)) == 1 else '不同'} → {'订单级(first)' if len(set(delivery_fees)) == 1 else '商品级(sum)'}")
        
        print(f"  企客后返: {rebates}")
        print(f"    → 值{'相同' if len(set(rebates)) == 1 else '不同'} → {'订单级(first)' if len(set(rebates)) == 1 else '商品级(sum)'}")
        
        print(f"  实收价格: {prices}")
        print(f"    → 值{'相同' if len(set(prices)) == 1 else '不同'} → {'订单级(first)' if len(set(prices)) == 1 else '商品级(sum)'}")
        
        print(f"  销量: {quantities}")
        print(f"    → 值{'相同' if len(set(quantities)) == 1 else '不同'} → {'订单级(first)' if len(set(quantities)) == 1 else '商品级(sum)'}")
    
    session.close()


if __name__ == "__main__":
    check_field_level()
