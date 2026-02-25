# -*- coding: utf-8 -*-
"""
验证利润额字段的计算方式

利润额 = 实收价格 - 商品采购成本 ?
还是
利润额 = 实收价格 - 商品采购成本 - 其他扣减项 ?
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import SessionLocal
from datetime import datetime, date
from sqlalchemy import text

STORE_NAME = "惠宜选-淮安生态新城店"
START_DATE = date(2026, 1, 12)
END_DATE = date(2026, 1, 18)

def verify_profit_field():
    """验证利润额字段"""
    session = SessionLocal()
    try:
        # 获取几个订单的详细数据
        sql = """
        SELECT 
            order_id,
            product_name,
            actual_price,
            cost,
            profit,
            platform_service_fee,
            delivery_fee,
            quantity
        FROM orders
        WHERE store_name = :store_name
          AND date >= :start_date
          AND date <= :end_date
        ORDER BY order_id
        LIMIT 20
        """
        result = session.execute(text(sql), {
            'store_name': STORE_NAME,
            'start_date': datetime.combine(START_DATE, datetime.min.time()),
            'end_date': datetime.combine(END_DATE, datetime.max.time())
        })
        rows = result.fetchall()
        
        print("=" * 100)
        print("【验证利润额字段计算方式】")
        print("=" * 100)
        
        print(f"\n{'订单ID':<15} {'商品名称':<20} {'实收价格':>10} {'成本':>10} {'利润额':>10} {'计算利润':>10} {'差异':>10}")
        print("-" * 100)
        
        for row in rows:
            order_id = row[0]
            product_name = row[1][:18] if row[1] else ''
            actual_price = float(row[2] or 0)
            cost = float(row[3] or 0)
            profit = float(row[4] or 0)
            quantity = int(row[7] or 1)
            
            # 计算利润 = 实收价格 - 成本
            calculated_profit = actual_price - cost
            diff = profit - calculated_profit
            
            print(f"{order_id:<15} {product_name:<20} {actual_price:>10.2f} {cost:>10.2f} {profit:>10.2f} {calculated_profit:>10.2f} {diff:>10.2f}")
        
        # 汇总验证
        sql2 = """
        SELECT 
            SUM(actual_price) as total_actual_price,
            SUM(cost) as total_cost,
            SUM(profit) as total_profit,
            SUM(actual_price - cost) as calculated_profit
        FROM orders
        WHERE store_name = :store_name
          AND date >= :start_date
          AND date <= :end_date
        """
        result2 = session.execute(text(sql2), {
            'store_name': STORE_NAME,
            'start_date': datetime.combine(START_DATE, datetime.min.time()),
            'end_date': datetime.combine(END_DATE, datetime.max.time())
        })
        row2 = result2.fetchone()
        
        print(f"\n" + "=" * 100)
        print("【汇总验证】")
        print("=" * 100)
        print(f"  实收价格总计: ¥{row2[0]:,.2f}")
        print(f"  成本总计: ¥{row2[1]:,.2f}")
        print(f"  利润额总计（数据库）: ¥{row2[2]:,.2f}")
        print(f"  计算利润（实收-成本）: ¥{row2[3]:,.2f}")
        print(f"  差异: ¥{row2[2] - row2[3]:,.2f}")
        
        if abs(row2[2] - row2[3]) < 1:
            print(f"\n✅ 利润额 = 实收价格 - 商品采购成本")
        else:
            print(f"\n⚠️ 利润额 ≠ 实收价格 - 商品采购成本，可能包含其他扣减项")
        
    finally:
        session.close()


if __name__ == "__main__":
    verify_profit_field()
