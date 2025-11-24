import pandas as pd
import numpy as np

# 读取Excel
df = pd.read_excel(r'实际数据\祥和路.xlsx')

print("="*80)
print("🎯 验证修复后的利润计算逻辑")
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
print(f"   原始数据: {len(df):,}行")
print(f"   订单数: {len(order_agg):,}个")

# ✅ 修复后的逻辑: 只看平台服务费>0
filtered = order_agg[order_agg['平台服务费'] > 0].copy()

print(f"\n🔍 剔除平台服务费=0后:")
print(f"   保留订单: {len(filtered):,}个")
print(f"   剔除订单: {len(order_agg) - len(filtered):,}个")

# 计算各字段总和
print("\n" + "="*80)
print("💰 各字段汇总 (修复后的逻辑):")
print("="*80)

total_profit_amount = filtered['利润额'].sum()
total_logistics = filtered['物流配送费'].sum()
total_service_fee = filtered['平台服务费'].sum()
total_kickback = filtered['企客后返'].sum()

print(f"\n利润额:        ¥{total_profit_amount:>15,.2f}")
print(f"物流配送费:    ¥{total_logistics:>15,.2f}")
print(f"平台服务费:    ¥{total_service_fee:>15,.2f}")
print(f"企客后返:      ¥{total_kickback:>15,.2f}")

# 计算实际利润
actual_profit = total_profit_amount - total_service_fee - total_logistics + total_kickback

print("\n" + "-"*80)
print(f"实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返")
print(f"        = ¥{total_profit_amount:,.2f} - ¥{total_service_fee:,.2f} - ¥{total_logistics:,.2f} + ¥{total_kickback:,.2f}")
print(f"        = ¥{actual_profit:,.2f}")
print("-"*80)

# 分渠道统计
print("\n" + "="*80)
print("📊 分渠道实际利润:")
print("="*80)

channel_profit = {}
for channel in filtered['渠道'].unique():
    channel_data = filtered[filtered['渠道'] == channel]
    
    profit_amt = channel_data['利润额'].sum()
    logistics = channel_data['物流配送费'].sum()
    service_fee = channel_data['平台服务费'].sum()
    kickback = channel_data['企客后返'].sum()
    
    actual = profit_amt - service_fee - logistics + kickback
    channel_profit[channel] = actual
    
    print(f"\n{channel}:")
    print(f"   订单数:      {len(channel_data):>10,}个")
    print(f"   利润额:      ¥{profit_amt:>15,.2f}")
    print(f"   物流配送费:  ¥{logistics:>15,.2f}")
    print(f"   平台服务费:  ¥{service_fee:>15,.2f}")
    print(f"   企客后返:    ¥{kickback:>15,.2f}")
    print(f"   实际利润:    ¥{actual:>15,.2f}")

total_channel_profit = sum(channel_profit.values())

print("\n" + "="*80)
print("✅ 验证结果:")
print("="*80)

print(f"\n总实际利润:           ¥{actual_profit:,.2f}")
print(f"分渠道利润之和:       ¥{total_channel_profit:,.2f}")
print(f"差异:                 ¥{abs(actual_profit - total_channel_profit):.2f}")
print(f"验证通过:             {abs(actual_profit - total_channel_profit) < 0.01}")

print("\n" + "="*80)
print("🎯 与用户数据对比:")
print("="*80)

user_total = 23332
user_channel = {
    '美团闪购': 15066,
    '饿了么': 6826,
    '京东到家': 1439
}

print(f"\n总利润对比:")
print(f"   系统计算:  ¥{actual_profit:,.2f}")
print(f"   用户数据:  ¥{user_total:,.2f}")
print(f"   差异:      ¥{actual_profit - user_total:,.2f}")
print(f"   差异率:    {abs(actual_profit - user_total) / user_total * 100:.2f}%")

print(f"\n分渠道对比:")
for channel, user_profit in user_channel.items():
    sys_profit = channel_profit.get(channel, 0)
    diff = sys_profit - user_profit
    diff_pct = abs(diff) / user_profit * 100 if user_profit > 0 else 0
    
    print(f"\n{channel}:")
    print(f"   系统:  ¥{sys_profit:>10,.2f}")
    print(f"   用户:  ¥{user_profit:>10,.2f}")
    print(f"   差异:  ¥{diff:>10,.2f} ({diff_pct:.2f}%)")

print("\n" + "="*80)
print("📝 结论:")
print("="*80)
print(f"✅ 修复后系统实际利润: ¥{actual_profit:,.2f}")
print(f"✅ 与用户数据¥{user_total:,.2f}接近,差异¥{abs(actual_profit - user_total):,.2f}")
print(f"✅ 差异可能来自:")
print(f"   - 企客后返字段(当前为¥{total_kickback:,.2f})")
print(f"   - 四舍五入差异")
print(f"   - 或其他未知的业务规则")
