import pandas as pd

# 读取Excel
df = pd.read_excel(r'实际数据\祥和路.xlsx')

print("="*80)
print("🔍 反推¥24,484这个数字是怎么来的")
print("="*80)

# 按订单聚合
agg_dict = {
    '利润额': 'sum',
    '物流配送费': 'first',
    '平台服务费': 'sum',
    '平台佣金': 'first',
    '企客后返': 'sum',
    '渠道': 'first'
}

order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()

print(f"\n📊 基础数据:")
print(f"   订单数: {len(order_agg):,}")

# 测试各种可能的计算方式
print("\n" + "="*80)
print("💡 可能的计算方式:")
print("="*80)

# 方式1: 不剔除任何订单
all_profit = (
    order_agg['利润额'] -
    order_agg['平台服务费'] -
    order_agg['物流配送费'] +
    order_agg['企客后返']
).sum()
print(f"\n1️⃣ 不剔除任何订单: ¥{all_profit:,.2f}")

# 方式2: 只剔除服务费>0
filtered_service_fee = order_agg[order_agg['平台服务费'] > 0]
profit_service_fee = (
    filtered_service_fee['利润额'] -
    filtered_service_fee['平台服务费'] -
    filtered_service_fee['物流配送费'] +
    filtered_service_fee['企客后返']
).sum()
print(f"2️⃣ 剔除服务费=0: ¥{profit_service_fee:,.2f} ({'✅匹配!' if abs(profit_service_fee - 23800.34) < 1 else ''})")

# 方式3: 服务费>0 或 佣金>0 (旧逻辑)
filtered_old = order_agg[(order_agg['平台服务费'] > 0) | (order_agg['平台佣金'] > 0)]
profit_old = (
    filtered_old['利润额'] -
    filtered_old['平台服务费'] -
    filtered_old['物流配送费'] +
    filtered_old['企客后返']
).sum()
print(f"3️⃣ 旧逻辑(服务费>0或佣金>0): ¥{profit_old:,.2f}")

# 方式4: 直接sum利润额
direct_profit = order_agg['利润额'].sum()
print(f"4️⃣ 直接sum利润额: ¥{direct_profit:,.2f}")

# 方式5: 利润额 - 平台服务费 (不扣配送费)
profit_no_logistics = (
    order_agg['利润额'] -
    order_agg['平台服务费']
).sum()
print(f"5️⃣ 利润额 - 平台服务费(不扣配送费): ¥{profit_no_logistics:,.2f}")

# 方式6: 剔除服务费=0后,利润额 - 服务费(不扣配送费)
filtered_profit_no_logistics = (
    filtered_service_fee['利润额'] -
    filtered_service_fee['平台服务费']
).sum()
print(f"6️⃣ 剔除后,利润额-服务费(不扣配送费): ¥{filtered_profit_no_logistics:,.2f}")

# 方式7: 直接sum利润额,剔除服务费=0
filtered_direct = filtered_service_fee['利润额'].sum()
print(f"7️⃣ 剔除后,直接sum利润额: ¥{filtered_direct:,.2f}")

# 方式8: 从商品行直接sum利润额
raw_profit = df['利润额'].sum()
print(f"8️⃣ 商品行直接sum利润额: ¥{raw_profit:,.2f}")

# 方式9: 检查是否是配送费计算错误
# 如果配送费没有正确聚合
profit_wrong_logistics = (
    order_agg['利润额'] -
    order_agg['平台服务费'] -
    order_agg['物流配送费'].fillna(0) * len(df) / len(order_agg) +  # 错误的配送费聚合
    order_agg['企客后返']
).sum()

print("\n" + "="*80)
print("🎯 查找¥24,484:")
print("="*80)

target = 24484
for i, value in enumerate([
    all_profit, profit_service_fee, profit_old, direct_profit,
    profit_no_logistics, filtered_profit_no_logistics, filtered_direct, raw_profit
], 1):
    diff = abs(value - target)
    if diff < 100:
        print(f"✅ 方式{i}非常接近! 差异仅¥{diff:.2f}")
    elif diff < 1000:
        print(f"⚠️ 方式{i}比较接近, 差异¥{diff:.2f}")

print("\n" + "="*80)
print("💡 分析:")
print("="*80)
print(f"您看板显示的¥24,484可能是:")
print(f"1. 使用了旧的利润计算逻辑(未扣除配送费)")
print(f"2. 或者缓存的数据还没有刷新")
print(f"3. 或者数据库中的利润字段还是老数据")
print(f"\n正确的实际利润应该是: ¥{profit_service_fee:,.2f}")
print(f"您手动计算的是: ¥23,332.00")
print(f"差异: ¥{abs(profit_service_fee - 23332):,.2f} (可能是企客后返或四舍五入)")
