"""验证铜山万达店美团共橙渠道销售额计算"""
from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func
import pandas as pd

session = SessionLocal()

print("="*100)
print("🔍 铜山万达店 - 美团共橙渠道销售额验证")
print("="*100)

# 查询美团共橙渠道的所有数据
orders = session.query(Order).filter(
    Order.store_name == '惠宜选-徐州铜山万达店',
    Order.channel == '美团共橙'
).all()

print(f"\n📊 数据基本信息:")
print(f"   总记录数（商品行）: {len(orders)}")

# 统计唯一订单数
unique_orders = set(order.order_id for order in orders)
print(f"   唯一订单数: {len(unique_orders)}")

# 方法1: 直接对商品实售价求和（错误方法 - 会包含所有商品行）
total_price_all_rows = sum(order.price or 0 for order in orders)
print(f"\n❌ 方法1 - 直接对所有商品行的价格求和:")
print(f"   结果: ¥{total_price_all_rows:,.2f}")
print(f"   说明: 这会累加所有商品的价格，不是订单销售额")

# 方法2: 按订单聚合后计算（正确方法 - 看板应该用这个）
df = pd.DataFrame([{
    'order_id': order.order_id,
    'price': order.price or 0,
    'actual_price': order.actual_price or 0,
    'amount': order.amount or 0,
    'product_name': order.product_name,
    'quantity': order.quantity or 1
} for order in orders])

print(f"\n✅ 方法2 - 按订单聚合商品实售价（看板calculate_order_metrics方法）:")
order_agg = df.groupby('order_id').agg({
    'price': 'sum',  # 商品实售价求和
    'actual_price': 'sum',
    'amount': 'sum',
    'quantity': 'sum'
}).reset_index()

total_sales_correct = order_agg['price'].sum()
print(f"   订单聚合后的商品实售价总和: ¥{total_sales_correct:,.2f}")
print(f"   订单聚合后的实收价格总和: ¥{order_agg['actual_price'].sum():,.2f}")
print(f"   订单聚合后的销售额总和: ¥{order_agg['amount'].sum():,.2f}")

# 显示前5个订单的详情
print(f"\n📋 前5个订单明细:")
print("-"*100)
for idx, order_id in enumerate(list(unique_orders)[:5], 1):
    order_items = [o for o in orders if o.order_id == order_id]
    total_price = sum(o.price or 0 for o in order_items)
    total_actual = sum(o.actual_price or 0 for o in order_items)
    total_amount = sum(o.amount or 0 for o in order_items)
    
    print(f"\n订单{idx}: {order_id}")
    print(f"   商品数: {len(order_items)}")
    print(f"   商品实售价合计: ¥{total_price:.2f}")
    print(f"   实收价格合计: ¥{total_actual:.2f}")
    print(f"   销售额合计: ¥{total_amount:.2f}")
    
    # 显示每个商品
    for item in order_items:
        print(f"      - {item.product_name}: 价格¥{item.price:.2f} × {item.quantity} = ¥{(item.price or 0) * (item.quantity or 1):.2f}")

# 方法3: 检查是否有"预计订单收入"字段
print(f"\n🔍 方法3 - 检查预计订单收入字段（看板Tab2使用）:")
# 注意：数据库模型中没有这个字段，所以查不到
# 但看板代码中提到使用"预计订单收入"作为销售额

# 方法4: 使用amount字段（销售额）
total_amount_all = sum(order.amount or 0 for order in orders)
print(f"\n❓ 方法4 - 直接对所有行的amount字段求和:")
print(f"   结果: ¥{total_amount_all:,.2f}")

# 按订单聚合amount
total_amount_by_order = order_agg['amount'].sum()
print(f"\n✅ 方法5 - 按订单聚合amount字段:")
print(f"   结果: ¥{total_amount_by_order:,.2f}")

print("\n"+"="*100)
print("📊 结果对比:")
print("="*100)
print(f"您的计算结果: ¥4,966")
print(f"看板显示: ¥6,172")
print(f"方法2（商品实售价按订单聚合）: ¥{total_sales_correct:,.2f}")
print(f"方法5（销售额按订单聚合）: ¥{total_amount_by_order:,.2f}")
print("\n💡 分析:")
if abs(total_sales_correct - 4966) < 100:
    print("   ✅ 方法2的结果接近您的计算（¥4,966）")
if abs(total_sales_correct - 6172) < 100:
    print("   ⚠️ 方法2的结果接近看板显示（¥6,172）")
if abs(total_amount_by_order - 4966) < 100:
    print("   ✅ 方法5的结果接近您的计算（¥4,966）")
if abs(total_amount_by_order - 6172) < 100:
    print("   ⚠️ 方法5的结果接近看板显示（¥6,172）")

session.close()
