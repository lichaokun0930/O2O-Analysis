# -*- coding: utf-8 -*-
"""
检查日期边界问题

可能用户选择的日期范围和我们查询的不一致
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import SessionLocal
from datetime import datetime, date, timedelta
from sqlalchemy import text

STORE_NAME = "惠宜选-淮安生态新城店"

def check_date_boundary():
    """检查不同日期范围的利润"""
    session = SessionLocal()
    try:
        print("=" * 70)
        print(f"【{STORE_NAME}】不同日期范围的利润对比")
        print("=" * 70)
        
        # 检查多个日期范围
        date_ranges = [
            (date(2026, 1, 12), date(2026, 1, 18)),  # 用户说的范围
            (date(2026, 1, 12), date(2026, 1, 17)),  # 少一天
            (date(2026, 1, 13), date(2026, 1, 18)),  # 少一天
            (date(2026, 1, 11), date(2026, 1, 17)),  # 不同范围
        ]
        
        for start_date, end_date in date_ranges:
            sql = """
            WITH order_agg AS (
                SELECT 
                    order_id,
                    channel,
                    SUM(profit) as profit,
                    SUM(platform_service_fee) as platform_fee,
                    MAX(delivery_fee) as delivery_fee,
                    MAX(corporate_rebate) as rebate
                FROM orders
                WHERE store_name = :store_name
                  AND date >= :start_date
                  AND date <= :end_date
                GROUP BY order_id, channel
            ),
            filtered AS (
                SELECT * FROM order_agg
                WHERE NOT (
                    channel IN ('饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店')
                    AND platform_fee <= 0
                )
            )
            SELECT 
                COUNT(*) as order_count,
                SUM(profit - platform_fee - delivery_fee + rebate) as actual_profit
            FROM filtered
            """
            result = session.execute(text(sql), {
                'store_name': STORE_NAME,
                'start_date': datetime.combine(start_date, datetime.min.time()),
                'end_date': datetime.combine(end_date, datetime.max.time())
            })
            row = result.fetchone()
            
            print(f"\n{start_date} ~ {end_date}:")
            print(f"  订单数: {row[0]}, 利润: ¥{row[1]:,.2f}")
        
        # 检查每天的利润
        print(f"\n" + "=" * 70)
        print("【每日利润明细】")
        print("=" * 70)
        
        sql2 = """
        WITH order_agg AS (
            SELECT 
                order_id,
                channel,
                DATE(date) as order_date,
                SUM(profit) as profit,
                SUM(platform_service_fee) as platform_fee,
                MAX(delivery_fee) as delivery_fee,
                MAX(corporate_rebate) as rebate
            FROM orders
            WHERE store_name = :store_name
              AND date >= :start_date
              AND date <= :end_date
            GROUP BY order_id, channel, DATE(date)
        ),
        filtered AS (
            SELECT * FROM order_agg
            WHERE NOT (
                channel IN ('饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店')
                AND platform_fee <= 0
            )
        )
        SELECT 
            order_date,
            COUNT(*) as order_count,
            SUM(profit - platform_fee - delivery_fee + rebate) as actual_profit
        FROM filtered
        GROUP BY order_date
        ORDER BY order_date
        """
        result2 = session.execute(text(sql2), {
            'store_name': STORE_NAME,
            'start_date': datetime.combine(date(2026, 1, 12), datetime.min.time()),
            'end_date': datetime.combine(date(2026, 1, 18), datetime.max.time())
        })
        rows = result2.fetchall()
        
        total_profit = 0
        for row in rows:
            print(f"  {row[0]}: {row[1]} 订单, 利润 ¥{row[2]:,.2f}")
            total_profit += row[2]
        
        print(f"\n  合计: ¥{total_profit:,.2f}")
        print(f"  用户期望: ¥3,554")
        print(f"  差异: ¥{total_profit - 3554:,.2f}")
        
    finally:
        session.close()


if __name__ == "__main__":
    check_date_boundary()
