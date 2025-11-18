"""验证预计订单收入计算逻辑"""
from database.connection import SessionLocal
from database.models import Order
import pandas as pd

session = SessionLocal()

print("="*100)
print("🔍 验证预计订单收入字段计算")
print("="*100)

# 加载美团共橙渠道数据
orders = session.query(Order).filter(
    Order.store_name == '惠宜选-徐州铜山万达店',
    Order.channel == '美团共橙'
).all()

# 模拟 DataSourceManager 的转换逻辑
data = []
for order in orders:
    data.append({
        '订单ID': order.order_id,
        '商品名称': order.product_name,
        '商品实售价': order.price,
        '实收价格': order.actual_price if order.actual_price else order.price,
        '销量': order.quantity,
        '预计订单收入': (order.actual_price if order.actual_price else order.price) * order.quantity,
        '用户支付配送费': order.user_paid_delivery_fee if order.user_paid_delivery_fee else 0.0,
        '打包袋金额': order.packaging_fee if order.packaging_fee else 0.0,
    })

df = pd.DataFrame(data)

print(f"\n📊 原始数据（所有商品行）:")
print(f"   记录数: {len(df)}")
print(f"   唯一订单数: {df['订单ID'].nunique()}")

# 按订单聚合（模拟 calculate_order_metrics）
order_agg = df.groupby('订单ID').agg({
    '商品实售价': 'sum',
    '实收价格': 'sum',
    '销量': 'sum',
    '预计订单收入': 'sum',
    '用户支付配送费': 'first',
    '打包袋金额': 'first'
}).reset_index()

# 计算订单总收入（兼容逻辑）
order_agg['订单总收入_方法1'] = order_agg['预计订单收入']
order_agg['订单总收入_方法2'] = (
    order_agg['商品实售价'] + 
    order_agg['打包袋金额'] + 
    order_agg['用户支付配送费']
)

print(f"\n✅ 按订单聚合后:")
print(f"   订单数: {len(order_agg)}")

# 计算总销售额（两种方法）
total_product_price = order_agg['商品实售价'].sum()
total_revenue_method1 = order_agg['预计订单收入'].sum()
total_revenue_method2 = order_agg['订单总收入_方法2'].sum()

print(f"\n📊 销售额计算结果:")
print("-"*100)
print(f"商品实售价合计（不含配送费和打包费）: ¥{total_product_price:,.2f}")
print(f"预计订单收入合计（实收价格×销量）: ¥{total_revenue_method1:,.2f}")
print(f"订单总收入_方法2（商品实售价+打包费+配送费）: ¥{total_revenue_method2:,.2f}")

# 对比用户计算和看板显示
print(f"\n📌 对比:")
print(f"   您的计算: ¥4,966")
print(f"   看板显示: ¥6,172")
print(f"   商品实售价合计: ¥{total_product_price:,.2f}")
print(f"   预计订单收入合计: ¥{total_revenue_method1:,.2f}")

# 分析差异
if abs(total_product_price - 4966) < 500:
    print(f"\n✅ 商品实售价({total_product_price:,.2f}) 接近您的计算(¥4,966)")
    print(f"   说明：您计算的是纯商品销售额，不含配送费和打包费")
elif abs(total_revenue_method2 - 6172) < 500:
    print(f"\n⚠️ 订单总收入_方法2({total_revenue_method2:,.2f}) 接近看板显示(¥6,172)")
    print(f"   说明：看板使用的是订单总收入（含配送费和打包费）")
elif abs(total_revenue_method1 - 6172) < 500:
    print(f"\n⚠️ 预计订单收入({total_revenue_method1:,.2f}) 接近看板显示(¥6,172)")

# 显示几个示例订单的详细计算
print(f"\n📋 示例订单详细计算（前5个）:")
print("-"*100)
for idx in range(min(5, len(order_agg))):
    row = order_agg.iloc[idx]
    print(f"\n订单 {row['订单ID']}:")
    print(f"   商品实售价: ¥{row['商品实售价']:.2f}")
    print(f"   预计订单收入(实收价格×销量): ¥{row['预计订单收入']:.2f}")
    print(f"   用户支付配送费: ¥{row['用户支付配送费']:.2f}")
    print(f"   打包袋金额: ¥{row['打包袋金额']:.2f}")
    print(f"   订单总收入(方法2): ¥{row['订单总收入_方法2']:.2f}")

session.close()
