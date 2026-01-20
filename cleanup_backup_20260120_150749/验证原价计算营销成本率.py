# -*- coding: utf-8 -*-
"""
验证用商品原价计算营销成本率
"""

import pg8000
from datetime import date

conn = pg8000.connect(
    host='localhost',
    port=5432,
    database='o2o_dashboard',
    user='postgres',
    password='123456'
)
cursor = conn.cursor()

store_name = '惠宜选-徐州沛县店'
start_date = date(2026, 1, 12)
end_date = date(2026, 1, 18)

print(f"=" * 60)
print(f"验证用商品原价计算营销成本率")
print(f"门店: {store_name}")
print(f"日期: {start_date} ~ {end_date}")
print(f"=" * 60)

# 查询所有相关字段
sql = """
SELECT 
    order_id,
    SUM(actual_price) as actual_price_sum,
    SUM(price) as price_sum,  -- 商品实售价
    SUM(original_price) as original_price_sum,  -- 商品原价
    SUM(amount) as amount_sum,  -- 预计订单收入
    SUM(actual_price * COALESCE(quantity, 1)) as revenue_with_qty,
    SUM(price * COALESCE(quantity, 1)) as price_with_qty,
    SUM(original_price * COALESCE(quantity, 1)) as original_with_qty,
    MAX(full_reduction) as full_reduction,
    MAX(product_discount) as product_discount,
    MAX(merchant_voucher) as merchant_voucher,
    MAX(merchant_share) as merchant_share,
    MAX(gift_amount) as gift_amount,
    MAX(other_merchant_discount) as other_merchant_discount,
    MAX(new_customer_discount) as new_customer_discount,
    MAX(delivery_discount) as delivery_discount
FROM orders
WHERE store_name = %s
  AND date >= %s
  AND date <= %s
GROUP BY order_id
"""

cursor.execute(sql, (store_name, start_date, end_date))
rows = cursor.fetchall()

print(f"\n订单数: {len(rows)}")

# 汇总
totals = {
    'actual_price_sum': 0,
    'price_sum': 0,
    'original_price_sum': 0,
    'amount_sum': 0,
    'revenue_with_qty': 0,
    'price_with_qty': 0,
    'original_with_qty': 0,
    'marketing_7': 0,
    'marketing_8': 0,
}

for row in rows:
    totals['actual_price_sum'] += float(row[1] or 0)
    totals['price_sum'] += float(row[2] or 0)
    totals['original_price_sum'] += float(row[3] or 0)
    totals['amount_sum'] += float(row[4] or 0)
    totals['revenue_with_qty'] += float(row[5] or 0)
    totals['price_with_qty'] += float(row[6] or 0)
    totals['original_with_qty'] += float(row[7] or 0)
    
    # 7字段营销成本
    m7 = sum(float(row[i] or 0) for i in range(8, 15))
    totals['marketing_7'] += m7
    
    # 8字段营销成本（含配送费减免）
    m8 = m7 + float(row[15] or 0)
    totals['marketing_8'] += m8

print(f"\n" + "=" * 60)
print(f"各种销售额口径:")
print(f"=" * 60)
print(f"实收价格 sum: ¥{totals['actual_price_sum']:,.2f}")
print(f"商品实售价 sum: ¥{totals['price_sum']:,.2f}")
print(f"商品原价 sum: ¥{totals['original_price_sum']:,.2f}")
print(f"预计订单收入 sum: ¥{totals['amount_sum']:,.2f}")
print(f"实收价格×销量: ¥{totals['revenue_with_qty']:,.2f}")
print(f"商品实售价×销量: ¥{totals['price_with_qty']:,.2f}")
print(f"商品原价×销量: ¥{totals['original_with_qty']:,.2f}")

print(f"\n营销成本:")
print(f"7字段: ¥{totals['marketing_7']:,.2f}")
print(f"8字段(含配送减免): ¥{totals['marketing_8']:,.2f}")

print(f"\n" + "=" * 60)
print(f"营销成本率（7字段）:")
print(f"=" * 60)

denominators = [
    ('实收价格 sum', totals['actual_price_sum']),
    ('商品实售价 sum', totals['price_sum']),
    ('商品原价 sum', totals['original_price_sum']),
    ('预计订单收入 sum', totals['amount_sum']),
    ('实收价格×销量', totals['revenue_with_qty']),
    ('商品实售价×销量', totals['price_with_qty']),
    ('商品原价×销量', totals['original_with_qty']),
]

for name, value in denominators:
    if value > 0:
        rate = totals['marketing_7'] / value * 100
        diff = abs(rate - 12.1)
        marker = " ✅ 最接近!" if diff < 1 else ""
        print(f"{name}: {totals['marketing_7']:,.2f} / {value:,.2f} = {rate:.2f}% (差{diff:.2f}){marker}")

print(f"\n" + "=" * 60)
print(f"营销成本率（8字段含配送减免）:")
print(f"=" * 60)

for name, value in denominators:
    if value > 0:
        rate = totals['marketing_8'] / value * 100
        diff = abs(rate - 12.1)
        marker = " ✅ 最接近!" if diff < 1 else ""
        print(f"{name}: {totals['marketing_8']:,.2f} / {value:,.2f} = {rate:.2f}% (差{diff:.2f}){marker}")

# 反推
print(f"\n" + "=" * 60)
print(f"反推：如果营销成本率=12.1%")
print(f"=" * 60)
print(f"7字段营销成本需要的分母: ¥{totals['marketing_7'] / 0.121:,.2f}")
print(f"8字段营销成本需要的分母: ¥{totals['marketing_8'] / 0.121:,.2f}")

cursor.close()
conn.close()
