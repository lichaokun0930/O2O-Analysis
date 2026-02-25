# -*- coding: utf-8 -*-
"""
找出1076差异的来源

用户期望: 3554
我们计算: 4630.59
差异: 1076.59

可能的原因：
1. 用户的公式不同
2. 用户扣除了某些我们没扣的项目
3. 日期范围不同
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

def find_difference():
    """找出差异来源"""
    session = SessionLocal()
    try:
        # 正确的订单级聚合（过滤异常订单后）
        sql = """
        WITH order_agg AS (
            SELECT 
                order_id,
                channel,
                SUM(profit) as profit,
                SUM(platform_service_fee) as platform_fee,
                MAX(delivery_fee) as delivery_fee,
                MAX(corporate_rebate) as rebate,
                MAX(user_paid_delivery_fee) as user_delivery,
                MAX(delivery_discount) as delivery_discount,
                SUM(full_reduction) as full_reduction,
                SUM(product_discount) as product_discount,
                SUM(new_customer_discount) as new_customer,
                SUM(merchant_voucher) as voucher,
                SUM(merchant_share) as share,
                SUM(gift_amount) as gift,
                SUM(other_merchant_discount) as other_discount
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
            SUM(profit) as total_profit,
            SUM(platform_fee) as total_platform_fee,
            SUM(delivery_fee) as total_delivery_fee,
            SUM(rebate) as total_rebate,
            SUM(user_delivery) as total_user_delivery,
            SUM(delivery_discount) as total_delivery_discount,
            SUM(full_reduction) as total_full_reduction,
            SUM(product_discount) as total_product_discount,
            SUM(new_customer) as total_new_customer,
            SUM(voucher) as total_voucher,
            SUM(share) as total_share,
            SUM(gift) as total_gift,
            SUM(other_discount) as total_other
        FROM filtered
        """
        result = session.execute(text(sql), {
            'store_name': STORE_NAME,
            'start_date': datetime.combine(START_DATE, datetime.min.time()),
            'end_date': datetime.combine(END_DATE, datetime.max.time())
        })
        row = result.fetchone()
        
        print("=" * 70)
        print(f"【{STORE_NAME}】订单级聚合后的字段汇总")
        print(f"日期: {START_DATE} ~ {END_DATE}")
        print("=" * 70)
        
        order_count = row[0]
        profit = row[1] or 0
        platform_fee = row[2] or 0
        delivery_fee = row[3] or 0
        rebate = row[4] or 0
        user_delivery = row[5] or 0
        delivery_discount = row[6] or 0
        full_reduction = row[7] or 0
        product_discount = row[8] or 0
        new_customer = row[9] or 0
        voucher = row[10] or 0
        share = row[11] or 0
        gift = row[12] or 0
        other_discount = row[13] or 0
        
        print(f"\n订单数: {order_count}")
        print(f"\n【核心字段】")
        print(f"  利润额: ¥{profit:,.2f}")
        print(f"  平台服务费: ¥{platform_fee:,.2f}")
        print(f"  物流配送费: ¥{delivery_fee:,.2f}")
        print(f"  企客后返: ¥{rebate:,.2f}")
        
        print(f"\n【配送相关】")
        print(f"  用户支付配送费: ¥{user_delivery:,.2f}")
        print(f"  配送费减免金额: ¥{delivery_discount:,.2f}")
        
        # 配送净成本
        delivery_net = delivery_fee - (user_delivery - delivery_discount) - rebate
        print(f"  配送净成本: ¥{delivery_net:,.2f}")
        print(f"    = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返")
        print(f"    = {delivery_fee:.2f} - ({user_delivery:.2f} - {delivery_discount:.2f}) - {rebate:.2f}")
        
        print(f"\n【营销成本】")
        print(f"  满减金额: ¥{full_reduction:,.2f}")
        print(f"  商品减免金额: ¥{product_discount:,.2f}")
        print(f"  新客减免金额: ¥{new_customer:,.2f}")
        print(f"  商家代金券: ¥{voucher:,.2f}")
        print(f"  商家承担部分券: ¥{share:,.2f}")
        print(f"  满赠金额: ¥{gift:,.2f}")
        print(f"  商家其他优惠: ¥{other_discount:,.2f}")
        
        marketing_total = full_reduction + product_discount + new_customer + voucher + share + gift + other_discount
        print(f"  营销成本合计: ¥{marketing_total:,.2f}")
        
        print(f"\n" + "=" * 70)
        print("【各种利润计算公式】")
        print("=" * 70)
        
        # 公式1: 当前公式
        formula1 = profit - platform_fee - delivery_fee + rebate
        print(f"\n公式1（当前）: 利润额 - 平台服务费 - 物流配送费 + 企客后返")
        print(f"  = {profit:.2f} - {platform_fee:.2f} - {delivery_fee:.2f} + {rebate:.2f}")
        print(f"  = ¥{formula1:,.2f}")
        
        # 公式2: 使用配送净成本
        formula2 = profit - platform_fee - delivery_net
        print(f"\n公式2: 利润额 - 平台服务费 - 配送净成本")
        print(f"  = {profit:.2f} - {platform_fee:.2f} - {delivery_net:.2f}")
        print(f"  = ¥{formula2:,.2f}")
        
        # 公式3: 扣除营销成本
        formula3 = formula1 - marketing_total
        print(f"\n公式3: 公式1 - 营销成本")
        print(f"  = {formula1:.2f} - {marketing_total:.2f}")
        print(f"  = ¥{formula3:,.2f}")
        
        # 公式4: 使用配送净成本 + 扣除营销成本
        formula4 = formula2 - marketing_total
        print(f"\n公式4: 公式2 - 营销成本")
        print(f"  = {formula2:.2f} - {marketing_total:.2f}")
        print(f"  = ¥{formula4:,.2f}")
        
        # 公式5: 只扣除部分营销成本（商品减免金额）
        formula5 = formula1 - product_discount
        print(f"\n公式5: 公式1 - 商品减免金额")
        print(f"  = {formula1:.2f} - {product_discount:.2f}")
        print(f"  = ¥{formula5:,.2f}")
        
        # 公式6: 扣除商家代金券和商家承担部分券
        formula6 = formula1 - voucher - share
        print(f"\n公式6: 公式1 - 商家代金券 - 商家承担部分券")
        print(f"  = {formula1:.2f} - {voucher:.2f} - {share:.2f}")
        print(f"  = ¥{formula6:,.2f}")
        
        print(f"\n" + "=" * 70)
        print("【与用户期望对比】")
        print("=" * 70)
        print(f"用户期望: ¥3,554")
        print(f"\n各公式与用户期望的差异:")
        print(f"  公式1: ¥{formula1:,.2f}, 差异: ¥{abs(formula1 - 3554):,.2f}")
        print(f"  公式2: ¥{formula2:,.2f}, 差异: ¥{abs(formula2 - 3554):,.2f}")
        print(f"  公式3: ¥{formula3:,.2f}, 差异: ¥{abs(formula3 - 3554):,.2f}")
        print(f"  公式4: ¥{formula4:,.2f}, 差异: ¥{abs(formula4 - 3554):,.2f}")
        print(f"  公式5: ¥{formula5:,.2f}, 差异: ¥{abs(formula5 - 3554):,.2f}")
        print(f"  公式6: ¥{formula6:,.2f}, 差异: ¥{abs(formula6 - 3554):,.2f}")
        
        # 反推：用户可能扣除了什么
        diff = formula1 - 3554
        print(f"\n【反推】")
        print(f"  公式1结果: ¥{formula1:,.2f}")
        print(f"  用户期望: ¥3,554")
        print(f"  差异: ¥{diff:,.2f}")
        print(f"\n  可能的扣减项:")
        print(f"    商品减免金额: ¥{product_discount:,.2f} (差异: ¥{abs(diff - product_discount):,.2f})")
        print(f"    商家代金券+商家承担部分券: ¥{voucher + share:,.2f} (差异: ¥{abs(diff - voucher - share):,.2f})")
        print(f"    配送费减免金额: ¥{delivery_discount:,.2f} (差异: ¥{abs(diff - delivery_discount):,.2f})")
        
    finally:
        session.close()


if __name__ == "__main__":
    find_difference()
