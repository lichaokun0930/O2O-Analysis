# -*- coding: utf-8 -*-
"""
验证正确的营销成本率计算公式

根据经营总览（orders.py）的calculate_order_metrics函数：
- 订单总收入 = 实收价格 × 月售（销量）
- 商品实收额 = SUM(订单总收入)
- 营销成本率 = 营销成本 / 商品实收额 × 100%

即：营销成本率 = 营销成本 / SUM(实收价格 × 月售) × 100%
"""

import pg8000
from datetime import date

# 数据库连接
conn = pg8000.connect(
    host='localhost',
    port=5432,
    database='o2o_dashboard',
    user='postgres',
    password='123456'
)
cursor = conn.cursor()

# 查询参数
store_name = '惠宜选-徐州沛县店'
start_date = date(2026, 1, 12)
end_date = date(2026, 1, 18)

print(f"=" * 60)
print(f"验证营销成本率计算公式（基于orders.py逻辑）")
print(f"门店: {store_name}")
print(f"日期: {start_date} ~ {end_date}")
print(f"=" * 60)

# 查询订单级数据（按订单ID聚合）
# 关键：订单总收入 = 实收价格 × 月售（quantity）
sql = """
SELECT 
    order_id,
    -- 商品级字段（用sum）
    SUM(actual_price) as actual_price_sum,  -- 实收价格（单价）sum
    SUM(actual_price * COALESCE(quantity, 1)) as order_revenue,  -- 订单总收入 = 实收价格 × 销量
    SUM(amount) as amount_sum,  -- 预计订单收入（商品级sum）
    SUM(quantity) as total_quantity,  -- 总销量
    -- 营销成本7字段（订单级，用MAX避免重复）
    MAX(full_reduction) as full_reduction,
    MAX(product_discount) as product_discount,
    MAX(merchant_voucher) as merchant_voucher,
    MAX(merchant_share) as merchant_share,
    MAX(gift_amount) as gift_amount,
    MAX(other_merchant_discount) as other_merchant_discount,
    MAX(new_customer_discount) as new_customer_discount
FROM orders
WHERE store_name = %s
  AND date >= %s
  AND date <= %s
GROUP BY order_id
"""

cursor.execute(sql, (store_name, start_date, end_date))
rows = cursor.fetchall()

print(f"\n订单数: {len(rows)}")

# 计算汇总
total_actual_price_sum = 0  # 实收价格（单价sum）
total_order_revenue = 0  # 订单总收入 = 实收价格 × 销量
total_amount_sum = 0  # 预计订单收入
total_quantity = 0  # 总销量
total_marketing_cost = 0

for row in rows:
    order_id = row[0]
    actual_price_sum = float(row[1] or 0)
    order_revenue = float(row[2] or 0)
    amount_sum = float(row[3] or 0)
    quantity = int(row[4] or 0)
    
    # 营销成本7字段
    full_reduction = float(row[5] or 0)
    product_discount = float(row[6] or 0)
    merchant_voucher = float(row[7] or 0)
    merchant_share = float(row[8] or 0)
    gift_amount = float(row[9] or 0)
    other_merchant_discount = float(row[10] or 0)
    new_customer_discount = float(row[11] or 0)
    
    marketing_cost = (full_reduction + product_discount + merchant_voucher + 
                      merchant_share + gift_amount + other_merchant_discount + 
                      new_customer_discount)
    
    total_actual_price_sum += actual_price_sum
    total_order_revenue += order_revenue
    total_amount_sum += amount_sum
    total_quantity += quantity
    total_marketing_cost += marketing_cost

print(f"\n" + "=" * 60)
print(f"汇总数据:")
print(f"=" * 60)
print(f"实收价格（单价sum）: ¥{total_actual_price_sum:,.2f}")
print(f"订单总收入（实收价格×销量）: ¥{total_order_revenue:,.2f}")
print(f"预计订单收入（amount sum）: ¥{total_amount_sum:,.2f}")
print(f"总销量: {total_quantity}")
print(f"营销成本（7字段）: ¥{total_marketing_cost:,.2f}")

print(f"\n" + "=" * 60)
print(f"营销成本率计算:")
print(f"=" * 60)

# 方案1：用实收价格（单价sum）作为分母
rate1 = (total_marketing_cost / total_actual_price_sum * 100) if total_actual_price_sum > 0 else 0
print(f"方案1: 营销成本 / 实收价格(单价sum) = {total_marketing_cost:,.2f} / {total_actual_price_sum:,.2f} = {rate1:.2f}%")

# 方案2：用订单总收入（实收价格×销量）作为分母 - orders.py的逻辑
rate2 = (total_marketing_cost / total_order_revenue * 100) if total_order_revenue > 0 else 0
print(f"方案2: 营销成本 / 订单总收入(实收×销量) = {total_marketing_cost:,.2f} / {total_order_revenue:,.2f} = {rate2:.2f}%")

# 方案3：用预计订单收入作为分母
rate3 = (total_marketing_cost / total_amount_sum * 100) if total_amount_sum > 0 else 0
print(f"方案3: 营销成本 / 预计订单收入 = {total_marketing_cost:,.2f} / {total_amount_sum:,.2f} = {rate3:.2f}%")

print(f"\n" + "=" * 60)
print(f"用户期望值: 12.1%")
print(f"=" * 60)
print(f"方案1（实收价格单价sum）差异: {abs(rate1 - 12.1):.2f}个百分点")
print(f"方案2（订单总收入=实收×销量）差异: {abs(rate2 - 12.1):.2f}个百分点")
print(f"方案3（预计订单收入）差异: {abs(rate3 - 12.1):.2f}个百分点")

# 反推：如果营销成本率是12.1%，分母应该是多少？
expected_denominator = total_marketing_cost / 0.121
print(f"\n如果营销成本率=12.1%，分母应该是: ¥{expected_denominator:,.2f}")

cursor.close()
conn.close()
