# -*- coding: utf-8 -*-
"""检查"其他"渠道的数据异常"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from sqlalchemy import text

session = SessionLocal()
try:
    # 检查沛县店"其他"渠道的原始数据
    sql = """
        SELECT 
            order_id,
            order_number,
            channel,
            actual_price,
            quantity,
            full_reduction,
            product_discount,
            merchant_voucher,
            delivery_discount
        FROM orders
        WHERE store_name = '惠宜选-徐州沛县店'
          AND DATE(date) = '2026-01-12'
          AND (order_number NOT LIKE 'SG%' 
               AND order_number NOT LIKE 'ELE%' 
               AND order_number NOT LIKE 'JD%')
        LIMIT 20
    """
    
    result = session.execute(text(sql))
    rows = result.fetchall()
    
    print("沛县店 2026-01-12 '其他'渠道数据:")
    print("-" * 100)
    for row in rows:
        print(f"订单ID: {row[0]}, 订单号: {row[1]}, 渠道: {row[2]}")
        print(f"  实收: {row[3]}, 数量: {row[4]}, 满减: {row[5]}, 商品减免: {row[6]}, 代金券: {row[7]}, 配送减免: {row[8]}")
        print()
    
    # 统计"其他"渠道的订单数和金额
    sql2 = """
        SELECT 
            COUNT(DISTINCT order_id) as order_count,
            SUM(actual_price * COALESCE(quantity, 1)) as total_revenue,
            SUM(COALESCE(full_reduction, 0) + COALESCE(product_discount, 0) + 
                COALESCE(merchant_voucher, 0) + COALESCE(delivery_discount, 0)) as total_discount
        FROM orders
        WHERE store_name = '惠宜选-徐州沛县店'
          AND DATE(date) = '2026-01-12'
          AND (order_number NOT LIKE 'SG%' 
               AND order_number NOT LIKE 'ELE%' 
               AND order_number NOT LIKE 'JD%')
    """
    
    result2 = session.execute(text(sql2)).fetchone()
    print(f"\n统计:")
    print(f"  订单数: {result2[0]}")
    print(f"  实收金额: {result2[1]}")
    print(f"  折扣金额: {result2[2]}")
    
    # 检查预聚合表中"其他"渠道的数据
    sql3 = """
        SELECT channel, order_count, total_revenue, gmv, total_marketing_cost
        FROM store_daily_summary
        WHERE store_name = '惠宜选-徐州沛县店'
          AND summary_date = '2026-01-12'
    """
    
    result3 = session.execute(text(sql3)).fetchall()
    print(f"\n预聚合表数据:")
    for row in result3:
        print(f"  渠道: {row[0]}, 订单数: {row[1]}, 实收: {row[2]}, GMV: {row[3]}, 营销成本: {row[4]}")

finally:
    session.close()
