import pandas as pd
import numpy as np

# 读取Excel
df = pd.read_excel(r'实际数据\祥和路.xlsx')

print(f"📊 原始数据: {len(df)}行")

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
print(f"📊 订单数: {len(order_agg)}")

# 检查三种剔除情况
print("\n" + "="*80)
print("🔍 检查不同剔除逻辑的订单数:")
print("="*80)

# 1. 系统当前逻辑: 平台服务费>0 或 平台佣金>0
mask_system = (order_agg['平台服务费'] > 0) | (order_agg['平台佣金'] > 0)
system_orders = order_agg[mask_system]
print(f"\n1️⃣ 系统逻辑(服务费>0 或 佣金>0): {len(system_orders)}订单")

# 2. 用户逻辑: 只看平台服务费>0
mask_user = order_agg['平台服务费'] > 0
user_orders = order_agg[mask_user]
print(f"2️⃣ 用户逻辑(只看服务费>0): {len(user_orders)}订单")

# 3. 被兜底逻辑保留的订单: 服务费=0 但 佣金>0
mask_fallback = (order_agg['平台服务费'] <= 0) & (order_agg['平台佣金'] > 0)
fallback_orders = order_agg[mask_fallback]
print(f"3️⃣ 兜底订单(服务费=0但佣金>0): {len(fallback_orders)}订单")

print("\n" + "="*80)
print("💰 计算实际利润 (利润额 - 平台服务费 - 物流配送费 + 企客后返):")
print("="*80)

# 计算实际利润
def calc_profit(df_subset):
    return (
        df_subset['利润额'] -
        df_subset['平台服务费'] -
        df_subset['物流配送费'] +
        df_subset['企客后返']
    ).sum()

system_profit = calc_profit(system_orders)
user_profit = calc_profit(user_orders)
fallback_profit = calc_profit(fallback_orders)

print(f"\n1️⃣ 系统逻辑实际利润: ¥{system_profit:,.2f}")
print(f"2️⃣ 用户逻辑实际利润: ¥{user_profit:,.2f}")
print(f"3️⃣ 兜底订单的利润: ¥{fallback_profit:,.2f}")
print(f"\n差异 (系统-用户): ¥{system_profit - user_profit:,.2f}")
print(f"是否等于兜底订单利润: {abs((system_profit - user_profit) - fallback_profit) < 0.01}")

# 分析兜底订单
if len(fallback_orders) > 0:
    print("\n" + "="*80)
    print("🔍 兜底订单详细分析:")
    print("="*80)
    
    # 按渠道统计
    print("\n📊 按渠道统计兜底订单:")
    channel_stats = fallback_orders.groupby('渠道').agg({
        '订单ID': 'count',
        '利润额': 'sum',
        '平台服务费': 'sum',
        '物流配送费': 'sum',
        '平台佣金': 'sum',
        '企客后返': 'sum'
    })
    channel_stats.columns = ['订单数', '利润额', '平台服务费', '物流配送费', '平台佣金', '企客后返']
    channel_stats['实际利润'] = (
        channel_stats['利润额'] -
        channel_stats['平台服务费'] -
        channel_stats['物流配送费'] +
        channel_stats['企客后返']
    )
    print(channel_stats)
    
    # 样本数据
    print("\n📋 兜底订单样本(前10个):")
    sample = fallback_orders.head(10)[['订单ID', '渠道', '利润额', '平台服务费', '平台佣金', '物流配送费', '企客后返']]
    sample['实际利润'] = (
        sample['利润额'] -
        sample['平台服务费'] -
        sample['物流配送费'] +
        sample['企客后返']
    )
    print(sample.to_string())

print("\n" + "="*80)
print("✅ 结论:")
print("="*80)
print(f"系统多保留了{len(fallback_orders)}个订单(平台服务费=0但佣金>0)")
print(f"这些订单贡献了¥{fallback_profit:,.2f}的利润")
print(f"这正是您发现的差异!")
print(f"\n用户期望利润¥23,332 vs 系统实际利润¥{system_profit:,.2f}")
print(f"如果系统改用用户逻辑: ¥{user_profit:,.2f}")
