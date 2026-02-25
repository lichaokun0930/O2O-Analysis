# -*- coding: utf-8 -*-
"""
检查淮安店所有可能影响利润的字段

用户期望: 3554
我们计算: 4630
差异: 1076

需要找出这1076的来源
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import SessionLocal
from database.models import Order
from datetime import datetime, date
from sqlalchemy import text
import pandas as pd

STORE_NAME = "惠宜选-淮安生态新城店"
START_DATE = date(2026, 1, 12)
END_DATE = date(2026, 1, 18)

def check_all_fields():
    """检查所有字段"""
    session = SessionLocal()
    try:
        # 获取所有字段的汇总
        sql = """
        SELECT 
            COUNT(DISTINCT order_id) as order_count,
            SUM(profit) as total_profit,
            SUM(platform_service_fee) as total_platform_fee,
            SUM(commission) as total_commission,
            SUM(delivery_fee) as total_delivery_fee,
            SUM(corporate_rebate) as total_rebate,
            SUM(user_paid_delivery_fee) as total_user_delivery,
            SUM(delivery_discount) as total_delivery_discount,
            SUM(full_reduction) as total_full_reduction,
            SUM(product_discount) as total_product_discount,
            SUM(new_customer_discount) as total_new_customer,
            SUM(merchant_voucher) as total_voucher,
            SUM(merchant_share) as total_share,
            SUM(gift_amount) as total_gift,
            SUM(other_merchant_discount) as total_other,
            SUM(actual_price * COALESCE(quantity, 1)) as total_revenue,
            SUM(cost * COALESCE(quantity, 1)) as total_cost
        FROM orders
        WHERE store_name = :store_name
          AND date >= :start_date
          AND date <= :end_date
        """
        result = session.execute(text(sql), {
            'store_name': STORE_NAME,
            'start_date': datetime.combine(START_DATE, datetime.min.time()),
            'end_date': datetime.combine(END_DATE, datetime.max.time())
        })
        row = result.fetchone()
        
        print("=" * 70)
        print(f"【{STORE_NAME}】所有字段汇总（商品级SUM）")
        print(f"日期: {START_DATE} ~ {END_DATE}")
        print("=" * 70)
        
        print(f"\n订单数: {row[0]}")
        print(f"\n【利润相关】")
        print(f"  利润额(profit): ¥{row[1]:,.2f}")
        print(f"  平台服务费(platform_service_fee): ¥{row[2]:,.2f}")
        print(f"  平台佣金(commission): ¥{row[3]:,.2f}")
        print(f"  物流配送费(delivery_fee): ¥{row[4]:,.2f}")
        print(f"  企客后返(corporate_rebate): ¥{row[5]:,.2f}")
        
        print(f"\n【配送相关】")
        print(f"  用户支付配送费: ¥{row[6]:,.2f}")
        print(f"  配送费减免金额: ¥{row[7]:,.2f}")
        
        print(f"\n【营销成本】")
        print(f"  满减金额: ¥{row[8]:,.2f}")
        print(f"  商品减免金额: ¥{row[9]:,.2f}")
        print(f"  新客减免金额: ¥{row[10]:,.2f}")
        print(f"  商家代金券: ¥{row[11]:,.2f}")
        print(f"  商家承担部分券: ¥{row[12]:,.2f}")
        print(f"  满赠金额: ¥{row[13]:,.2f}")
        print(f"  商家其他优惠: ¥{row[14]:,.2f}")
        
        marketing_total = (row[8] or 0) + (row[9] or 0) + (row[10] or 0) + (row[11] or 0) + (row[12] or 0) + (row[13] or 0) + (row[14] or 0)
        print(f"  营销成本合计: ¥{marketing_total:,.2f}")
        
        print(f"\n【收入成本】")
        print(f"  实收金额: ¥{row[15]:,.2f}")
        print(f"  商品成本: ¥{row[16]:,.2f}")
        
        # 计算各种公式
        print(f"\n" + "=" * 70)
        print("【各种利润计算公式】")
        print("=" * 70)
        
        profit = row[1] or 0
        platform_fee = row[2] or 0
        delivery_fee = row[4] or 0
        rebate = row[5] or 0
        
        # 当前公式（商品级SUM，不正确）
        formula1 = profit - platform_fee - delivery_fee + rebate
        print(f"\n公式1（商品级SUM，当前错误方式）:")
        print(f"  利润额 - 平台服务费 - 物流配送费 + 企客后返")
        print(f"  = {profit:.2f} - {platform_fee:.2f} - {delivery_fee:.2f} + {rebate:.2f}")
        print(f"  = ¥{formula1:,.2f}")
        
        # 检查物流配送费是否被重复计算
        sql2 = """
        SELECT 
            COUNT(DISTINCT order_id) as order_count,
            SUM(delivery_fee) as sum_delivery,
            (SELECT SUM(t.delivery_fee) FROM (
                SELECT DISTINCT order_id, delivery_fee FROM orders
                WHERE store_name = :store_name
                  AND date >= :start_date
                  AND date <= :end_date
            ) t) as distinct_delivery
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
        
        print(f"\n【物流配送费重复检查】")
        print(f"  SUM(delivery_fee): ¥{row2[1]:,.2f}")
        print(f"  按订单去重后SUM: ¥{row2[2]:,.2f}")
        print(f"  差异（重复计算部分）: ¥{row2[1] - row2[2]:,.2f}")
        
        # 正确的订单级聚合
        sql3 = """
        WITH order_agg AS (
            SELECT 
                order_id,
                channel,
                SUM(profit) as profit,
                SUM(platform_service_fee) as platform_fee,
                MAX(delivery_fee) as delivery_fee,  -- 订单级字段用MAX/FIRST
                MAX(corporate_rebate) as rebate
            FROM orders
            WHERE store_name = :store_name
              AND date >= :start_date
              AND date <= :end_date
            GROUP BY order_id, channel
        )
        SELECT 
            COUNT(*) as order_count,
            SUM(profit) as total_profit,
            SUM(platform_fee) as total_platform_fee,
            SUM(delivery_fee) as total_delivery_fee,
            SUM(rebate) as total_rebate,
            SUM(profit - platform_fee - delivery_fee + rebate) as actual_profit
        FROM order_agg
        """
        result3 = session.execute(text(sql3), {
            'store_name': STORE_NAME,
            'start_date': datetime.combine(START_DATE, datetime.min.time()),
            'end_date': datetime.combine(END_DATE, datetime.max.time())
        })
        row3 = result3.fetchone()
        
        print(f"\n【正确的订单级聚合】")
        print(f"  订单数: {row3[0]}")
        print(f"  利润额(SUM): ¥{row3[1]:,.2f}")
        print(f"  平台服务费(SUM): ¥{row3[2]:,.2f}")
        print(f"  物流配送费(MAX): ¥{row3[3]:,.2f}")
        print(f"  企客后返(MAX): ¥{row3[4]:,.2f}")
        print(f"  订单实际利润: ¥{row3[5]:,.2f}")
        
        # 过滤异常订单后
        sql4 = """
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
        )
        SELECT 
            COUNT(*) as order_count,
            SUM(profit) as total_profit,
            SUM(platform_fee) as total_platform_fee,
            SUM(delivery_fee) as total_delivery_fee,
            SUM(rebate) as total_rebate,
            SUM(profit - platform_fee - delivery_fee + rebate) as actual_profit
        FROM order_agg
        WHERE NOT (
            channel IN ('饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店')
            AND platform_fee <= 0
        )
        """
        result4 = session.execute(text(sql4), {
            'store_name': STORE_NAME,
            'start_date': datetime.combine(START_DATE, datetime.min.time()),
            'end_date': datetime.combine(END_DATE, datetime.max.time())
        })
        row4 = result4.fetchone()
        
        print(f"\n【过滤异常订单后】")
        print(f"  订单数: {row4[0]}")
        print(f"  利润额(SUM): ¥{row4[1]:,.2f}")
        print(f"  平台服务费(SUM): ¥{row4[2]:,.2f}")
        print(f"  物流配送费(MAX): ¥{row4[3]:,.2f}")
        print(f"  企客后返(MAX): ¥{row4[4]:,.2f}")
        print(f"  订单实际利润: ¥{row4[5]:,.2f}")
        
        print(f"\n【对比】")
        print(f"  用户期望: ¥3,554")
        print(f"  我们计算: ¥{row4[5]:,.2f}")
        print(f"  差异: ¥{row4[5] - 3554:,.2f}")
        
    finally:
        session.close()


if __name__ == "__main__":
    check_all_fields()
