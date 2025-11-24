"""
重新验证物流配送费 - 订单级字段
"""
import pandas as pd

print("=" * 80)
print("验证物流配送费是否为订单级字段")
print("=" * 80)

# 读取数据
df = pd.read_excel('实际数据/枫瑞.xlsx')
print(f"\n✅ 数据行数: {len(df)}")
print(f"✅ 订单数: {df['订单ID'].nunique()}")

print("\n" + "=" * 80)
print("测试1: 检查同一订单的多行,物流配送费是否相同")
print("=" * 80)

# 取一个有多个商品的订单
multi_item_orders = df.groupby('订单ID').size()
multi_item_orders = multi_item_orders[multi_item_orders > 1]

if len(multi_item_orders) > 0:
    # 取前3个多商品订单
    sample_orders = multi_item_orders.head(3).index.tolist()
    
    for order_id in sample_orders:
        order_data = df[df['订单ID'] == order_id]
        print(f"\n订单 {order_id} ({len(order_data)}个商品):")
        print(order_data[['商品名称', '物流配送费']].to_string(index=False))
        
        # 检查物流配送费是否相同
        unique_fees = order_data['物流配送费'].unique()
        if len(unique_fees) == 1:
            print(f"  ✅ 物流配送费相同: {unique_fees[0]}")
        else:
            print(f"  ❌ 物流配送费不同: {unique_fees}")

print("\n" + "=" * 80)
print("测试2: 按订单聚合,对比 .first() 和 .sum() 的差异")
print("=" * 80)

# 方法1: 使用.first() (订单级字段正确方式)
delivery_fee_first = df.groupby('订单ID')['物流配送费'].first().sum()
print(f"\n使用 .first() 聚合: {delivery_fee_first:,.2f}")

# 方法2: 使用.sum() (错误方式,会重复计算)
delivery_fee_sum = df.groupby('订单ID')['物流配送费'].sum().sum()
print(f"使用 .sum() 聚合: {delivery_fee_sum:,.2f}")

# 差异
diff = delivery_fee_sum - delivery_fee_first
diff_pct = (diff / delivery_fee_first * 100) if delivery_fee_first > 0 else 0
print(f"\n差异: {diff:,.2f} ({diff_pct:.1f}%)")

if abs(diff) < 1:
    print("✅ 两种方式结果接近,物流配送费可能是订单级字段")
else:
    print("❌ 两种方式结果差异大,说明使用了错误的聚合方式!")

print("\n" + "=" * 80)
print("正确的计算方式")
print("=" * 80)

# 订单级聚合
order_agg = df.groupby('订单ID').agg({
    '利润额': 'sum',              # 商品级 - sum
    '平台服务费': 'sum',          # 商品级 - sum
    '物流配送费': 'first',        # 订单级 - first ✅
    '企客后返': 'sum'             # 商品级 - sum
}).reset_index()

print(f"\n订单聚合后:")
print(f"  利润额总和: {order_agg['利润额'].sum():,.2f}")
print(f"  平台服务费总和: {order_agg['平台服务费'].sum():,.2f}")
print(f"  物流配送费总和: {order_agg['物流配送费'].sum():,.2f}")  # 这个才是正确的
print(f"  企客后返总和: {order_agg['企客后返'].sum():,.2f}")

# 计算订单实际利润
order_agg['订单实际利润'] = (
    order_agg['利润额'] - 
    order_agg['平台服务费'] - 
    order_agg['物流配送费'] +  # 使用.first()聚合后的值
    order_agg['企客后返']
)

total_actual_profit = order_agg['订单实际利润'].sum()
print(f"\n订单实际利润: {total_actual_profit:,.2f}")

# 按您的公式验证
profit_by_formula = 62372 - 40377 - 11269 + 0
print(f"\n按您的公式计算: 62372 - 40377 - 11269 + 0 = {profit_by_formula:,.2f}")

print(f"\n对比:")
print(f"  我计算的物流配送费: {order_agg['物流配送费'].sum():,.2f}")
print(f"  您提供的物流配送费: 40,377")
print(f"  差异: {order_agg['物流配送费'].sum() - 40377:,.2f}")

print("\n" + "=" * 80)
