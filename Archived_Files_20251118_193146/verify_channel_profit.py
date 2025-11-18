"""验证铜山万达店美团共橙渠道的利润计算"""
from database.connection import SessionLocal
from database.models import Order
import pandas as pd

session = SessionLocal()

# 查询美团共橙渠道的所有数据
orders = session.query(Order).filter(
    Order.store_name == '惠宜选-徐州铜山万达店',
    Order.channel == '美团共橙'
).all()

print(f"✅ 查询到 {len(orders)} 条商品记录")

# 转换为DataFrame
data = []
for order in orders:
    data.append({
        '订单ID': order.order_id,
        '商品名称': order.product_name,
        '商品实售价': order.price,
        '实收价格': order.actual_price if order.actual_price else order.price,
        '销量': order.quantity,
        '利润额': order.profit,
        '物流配送费': order.delivery_fee,
        '用户支付配送费': order.user_paid_delivery_fee,
        '配送费减免': order.delivery_discount,
        '平台佣金': order.commission,
        '满减金额': order.full_reduction,
        '商品减免金额': order.product_discount,
        '商家代金券': order.merchant_voucher,
        '商家承担部分券': order.merchant_share,
        '打包袋金额': order.packaging_fee
    })

df = pd.DataFrame(data)

print("\n" + "="*100)
print("📊 美团共橙渠道 - 原始数据汇总（商品级）")
print("="*100)
print(f"商品记录数: {len(df)}")
print(f"不重复订单数: {df['订单ID'].nunique()}")
print(f"商品实售价合计: ¥{df['商品实售价'].sum():,.2f}")
print(f"利润额合计（直接SUM-错误）: ¥{df['利润额'].sum():,.2f}")

# ===== 正确计算方法：按订单聚合 =====
print("\n" + "="*100)
print("✅ 正确计算方法：按订单ID聚合（模拟calculate_order_metrics）")
print("="*100)

# Step 1: 订单级聚合
order_agg = df.groupby('订单ID').agg({
    '商品实售价': 'sum',              # 商品级，sum
    '利润额': 'sum',                  # 商品级，sum
    '销量': 'sum',                    # 商品级，sum
    '用户支付配送费': 'first',        # 订单级，first
    '配送费减免': 'first',            # 订单级，first
    '物流配送费': 'first',            # 订单级，first
    '满减金额': 'first',              # 订单级，first
    '商品减免金额': 'first',          # 订单级，first
    '商家代金券': 'first',            # 订单级，first
    '商家承担部分券': 'first',        # 订单级，first
    '平台佣金': 'first',              # 订单级，first
    '打包袋金额': 'first'             # 订单级，first
}).reset_index()

# Step 2: 计算预计订单收入（每个订单）
order_revenue = df.groupby('订单ID').apply(
    lambda x: ((x['实收价格'] * x['销量']).sum())
).reset_index()
order_revenue.columns = ['订单ID', '预计订单收入']
order_agg = order_agg.merge(order_revenue, on='订单ID', how='left')

# Step 3: 计算商家活动成本
order_agg['商家活动成本'] = (
    order_agg['满减金额'] + 
    order_agg['商品减免金额'] + 
    order_agg['商家代金券'] +
    order_agg['商家承担部分券']
)

# Step 4: 计算配送净成本
order_agg['配送净成本'] = (
    order_agg['物流配送费'] - 
    (order_agg['用户支付配送费'] - order_agg['配送费减免'])
)

# Step 5: 计算订单总收入
order_agg['订单总收入'] = (
    order_agg['商品实售价'] + 
    order_agg['打包袋金额'] + 
    order_agg['用户支付配送费']
)

# Step 6: 计算订单实际利润
order_agg['订单实际利润'] = (
    order_agg['利润额'] - 
    order_agg['配送净成本'] - 
    order_agg['平台佣金']
)

print(f"\n订单数: {len(order_agg)}")
print(f"预计订单收入总计: ¥{order_agg['预计订单收入'].sum():,.2f}")
print(f"订单总收入总计: ¥{order_agg['订单总收入'].sum():,.2f}")
print(f"利润额总计: ¥{order_agg['利润额'].sum():,.2f}")
print(f"配送净成本总计: ¥{order_agg['配送净成本'].sum():,.2f}")
print(f"平台佣金总计: ¥{order_agg['平台佣金'].sum():,.2f}")
print(f"商家活动成本总计: ¥{order_agg['商家活动成本'].sum():,.2f}")
print(f"\n📈 订单实际利润总计: ¥{order_agg['订单实际利润'].sum():,.2f}")

# 分析利润分布
print("\n" + "="*100)
print("📊 利润分布分析")
print("="*100)
print(f"盈利订单数: {len(order_agg[order_agg['订单实际利润'] > 0])}")
print(f"亏损订单数: {len(order_agg[order_agg['订单实际利润'] < 0])}")
print(f"平均订单实际利润: ¥{order_agg['订单实际利润'].mean():,.2f}")
print(f"中位数订单实际利润: ¥{order_agg['订单实际利润'].median():,.2f}")

# 显示前5个订单的详细计算
print("\n" + "="*100)
print("🔍 前5个订单的详细计算")
print("="*100)
for idx in range(min(5, len(order_agg))):
    row = order_agg.iloc[idx]
    print(f"\n订单 {idx+1}: {row['订单ID']}")
    print(f"  预计订单收入: ¥{row['预计订单收入']:.2f}")
    print(f"  利润额: ¥{row['利润额']:.2f}")
    print(f"  物流配送费: ¥{row['物流配送费']:.2f}")
    print(f"  用户支付配送费: ¥{row['用户支付配送费']:.2f}")
    print(f"  配送费减免: ¥{row['配送费减免']:.2f}")
    print(f"  配送净成本: ¥{row['配送净成本']:.2f}")
    print(f"  平台佣金: ¥{row['平台佣金']:.2f}")
    print(f"  → 订单实际利润: ¥{row['订单实际利润']:.2f}")

session.close()
