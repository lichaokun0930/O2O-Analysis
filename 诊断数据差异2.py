# -*- coding: utf-8 -*-
"""
诊断数据差异2 - 测试不同过滤条件下的利润
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import SessionLocal
from sqlalchemy import text

def test_different_filters():
    """测试不同过滤条件"""
    
    session = SessionLocal()
    store_name = "惠宜选-泰州兴化店"
    
    print("=" * 70)
    print(f"测试不同过滤条件下的利润计算")
    print("=" * 70)
    
    # 场景1: 不过滤任何订单
    sql1 = """
    WITH order_level AS (
        SELECT 
            order_id,
            SUM(profit) as profit,
            SUM(platform_service_fee) as platform_fee,
            MAX(delivery_fee) as delivery_fee,
            SUM(corporate_rebate) as rebate
        FROM orders
        WHERE store_name = :store_name
        GROUP BY order_id
    )
    SELECT 
        COUNT(*) as order_count,
        SUM(profit - platform_fee - delivery_fee + rebate) as actual_profit
    FROM order_level
    """
    
    result = session.execute(text(sql1), {'store_name': store_name})
    row = result.fetchone()
    print(f"\n场景1: 不过滤任何订单")
    print(f"  订单数: {row[0]}, 利润: ¥{row[1]:,.2f}")
    
    # 场景2: 过滤收费渠道中平台服务费=0的订单
    sql2 = """
    WITH order_level AS (
        SELECT 
            order_id,
            channel,
            SUM(profit) as profit,
            SUM(platform_service_fee) as platform_fee,
            MAX(delivery_fee) as delivery_fee,
            SUM(corporate_rebate) as rebate
        FROM orders
        WHERE store_name = :store_name
        GROUP BY order_id, channel
    )
    SELECT 
        COUNT(*) as order_count,
        SUM(profit - platform_fee - delivery_fee + rebate) as actual_profit
    FROM order_level
    WHERE NOT (
        channel IN ('饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店')
        AND platform_fee <= 0
    )
    """
    
    result = session.execute(text(sql2), {'store_name': store_name})
    row = result.fetchone()
    print(f"\n场景2: 过滤收费渠道中平台服务费=0的订单")
    print(f"  订单数: {row[0]}, 利润: ¥{row[1]:,.2f}")
    
    # 场景3: 只过滤平台服务费<0的订单（负数）
    sql3 = """
    WITH order_level AS (
        SELECT 
            order_id,
            SUM(profit) as profit,
            SUM(platform_service_fee) as platform_fee,
            MAX(delivery_fee) as delivery_fee,
            SUM(corporate_rebate) as rebate
        FROM orders
        WHERE store_name = :store_name
        GROUP BY order_id
    )
    SELECT 
        COUNT(*) as order_count,
        SUM(profit - platform_fee - delivery_fee + rebate) as actual_profit
    FROM order_level
    WHERE platform_fee >= 0
    """
    
    result = session.execute(text(sql3), {'store_name': store_name})
    row = result.fetchone()
    print(f"\n场景3: 只过滤平台服务费<0的订单")
    print(f"  订单数: {row[0]}, 利润: ¥{row[1]:,.2f}")
    
    # 场景4: 检查是否有重复的订单ID
    sql4 = """
    SELECT order_id, COUNT(*) as cnt
    FROM (
        SELECT DISTINCT order_id, channel FROM orders WHERE store_name = :store_name
    ) t
    GROUP BY order_id
    HAVING COUNT(*) > 1
    """
    
    result = session.execute(text(sql4), {'store_name': store_name})
    rows = result.fetchall()
    print(f"\n场景4: 检查同一订单是否有多个渠道")
    print(f"  有多渠道的订单数: {len(rows)}")
    
    # 场景5: 用户可能的计算方式（直接SUM，不做订单级聚合）
    sql5 = """
    SELECT 
        COUNT(DISTINCT order_id) as order_count,
        SUM(profit) as total_profit,
        SUM(platform_service_fee) as total_platform_fee,
        SUM(delivery_fee) as total_delivery_fee,
        SUM(corporate_rebate) as total_rebate,
        SUM(profit) - SUM(platform_service_fee) - SUM(delivery_fee) + SUM(corporate_rebate) as actual_profit
    FROM orders
    WHERE store_name = :store_name
    """
    
    result = session.execute(text(sql5), {'store_name': store_name})
    row = result.fetchone()
    print(f"\n场景5: 直接SUM（不做订单级聚合，物流费会重复计算）")
    print(f"  订单数: {row[0]}")
    print(f"  原始利润: ¥{row[1]:,.2f}")
    print(f"  平台服务费: ¥{row[2]:,.2f}")
    print(f"  物流配送费: ¥{row[3]:,.2f}（注意：这里会重复计算）")
    print(f"  企客后返: ¥{row[4]:,.2f}")
    print(f"  计算利润: ¥{row[5]:,.2f}")
    
    # 场景6: 正确的订单级聚合（物流费用first）
    sql6 = """
    WITH order_level AS (
        SELECT 
            order_id,
            SUM(profit) as profit,
            SUM(platform_service_fee) as platform_fee,
            MAX(delivery_fee) as delivery_fee,  -- 订单级字段，用MAX/FIRST
            SUM(corporate_rebate) as rebate
        FROM orders
        WHERE store_name = :store_name
        GROUP BY order_id
    )
    SELECT 
        COUNT(*) as order_count,
        SUM(profit) as total_profit,
        SUM(platform_fee) as total_platform_fee,
        SUM(delivery_fee) as total_delivery_fee,
        SUM(rebate) as total_rebate,
        SUM(profit - platform_fee - delivery_fee + rebate) as actual_profit
    FROM order_level
    """
    
    result = session.execute(text(sql6), {'store_name': store_name})
    row = result.fetchone()
    print(f"\n场景6: 正确的订单级聚合（物流费用MAX）")
    print(f"  订单数: {row[0]}")
    print(f"  原始利润: ¥{row[1]:,.2f}")
    print(f"  平台服务费: ¥{row[2]:,.2f}")
    print(f"  物流配送费: ¥{row[3]:,.2f}")
    print(f"  企客后返: ¥{row[4]:,.2f}")
    print(f"  计算利润: ¥{row[5]:,.2f}")
    
    print("\n" + "=" * 70)
    print("用户期望值: ¥17,341.00")
    print("=" * 70)
    
    session.close()


if __name__ == "__main__":
    test_different_filters()
