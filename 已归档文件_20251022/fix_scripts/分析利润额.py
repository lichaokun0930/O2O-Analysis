import pandas as pd
import numpy as np

# 读取数据
df = pd.read_excel('门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx')

print("="*80)
print("� 原始数据字段列表")
print("="*80)
for i, col in enumerate(df.columns, 1):
    print(f"{i}. {col}")

print("\n" + "="*80)
print("�📊 原始数据样本（前10行）")
print("="*80)
# 找到包含"成本"的字段
cost_cols = [col for col in df.columns if '成本' in col or '利润' in col]
print(f"成本/利润相关字段: {cost_cols}")

display_cols = ['订单ID', '商品名称', '商品实售价']
display_cols.extend(cost_cols)
if '物流配送费' in df.columns:
    display_cols.append('物流配送费')
if '平台佣金' in df.columns:
    display_cols.append('平台佣金')
if '满减金额' in df.columns:
    display_cols.append('满减金额')
if '商品减免金额' in df.columns:
    display_cols.append('商品减免金额')

print(df[display_cols].head(10).to_string())

print("\n" + "="*80)
print("💰 利润额统计分析")
print("="*80)
print(f"利润额总和: ¥{df['利润额'].sum():,.2f}")
print(f"商品实售价总和: ¥{df['商品实售价'].sum():,.2f}")
print(f"成本总和: ¥{df['成本'].sum():,.2f}")

print("\n" + "="*80)
print("🔍 验证利润额公式")
print("="*80)

# 测试1: 利润额 = 商品实售价 - 成本 ?
df_test = df.copy()
df_test['计算利润1'] = df_test['商品实售价'] - df_test['成本']
df_test['差异1'] = (df_test['利润额'] - df_test['计算利润1']).abs()
print(f"\n假设1: 利润额 = 商品实售价 - 成本")
print(f"  有显著差异的行数: {(df_test['差异1'] > 0.01).sum()} / {len(df_test)}")
if (df_test['差异1'] > 0.01).sum() > 0:
    print(f"  ❌ 不符合")
else:
    print(f"  ✅ 符合")

# 测试2: 利润额 = 商品实售价 - 成本 - 活动成本 ?
df_test['活动成本'] = (
    df_test['满减金额'].fillna(0) + 
    df_test['商品减免金额'].fillna(0) + 
    df_test['商家代金券'].fillna(0) + 
    df_test['商家承担部分券'].fillna(0)
)
df_test['计算利润2'] = df_test['商品实售价'] - df_test['成本'] - df_test['活动成本']
df_test['差异2'] = (df_test['利润额'] - df_test['计算利润2']).abs()
print(f"\n假设2: 利润额 = 商品实售价 - 成本 - 活动成本")
print(f"  有显著差异的行数: {(df_test['差异2'] > 0.01).sum()} / {len(df_test)}")
if (df_test['差异2'] > 0.01).sum() > 0:
    print(f"  ❌ 不符合")
    print("\n  差异样本:")
    diff_sample = df_test[df_test['差异2'] > 0.01][['商品名称', '利润额', '计算利润2', '差异2']].head(5)
    print(diff_sample.to_string())
else:
    print(f"  ✅ 符合")

print("\n" + "="*80)
print("📊 按订单ID聚合分析盈利订单")
print("="*80)

# 按订单聚合
order_agg = df.groupby('订单ID').agg({
    '商品实售价': 'sum',
    '成本': 'sum',
    '利润额': 'sum',
    '物流配送费': 'first',
    '平台佣金': 'first',
    '满减金额': 'first',
    '商品减免金额': 'first',
    '商家代金券': 'first',
    '商家承担部分券': 'first'
}).reset_index()

# 计算订单实际利润
order_agg['订单实际利润'] = (
    order_agg['利润额'] - 
    order_agg['物流配送费'] - 
    order_agg['平台佣金']
)

# 原始利润额>0的订单
profit_by_lirun = (order_agg['利润额'] > 0).sum()
profit_rate_by_lirun = profit_by_lirun / len(order_agg) * 100

# 实际利润>0的订单
profit_by_actual = (order_agg['订单实际利润'] > 0).sum()
profit_rate_by_actual = profit_by_actual / len(order_agg) * 100

print(f"总订单数: {len(order_agg):,}")
print(f"\n按原始表'利润额'字段判断:")
print(f"  盈利订单数: {profit_by_lirun:,}")
print(f"  盈利订单占比: {profit_rate_by_lirun:.2f}%")
print(f"\n按'订单实际利润'判断（利润额 - 物流配送费 - 平台佣金）:")
print(f"  盈利订单数: {profit_by_actual:,}")
print(f"  盈利订单占比: {profit_rate_by_actual:.2f}%")
print(f"\n⚠️ 差异:")
print(f"  减少订单数: {profit_by_lirun - profit_by_actual:,}")
print(f"  占比下降: {profit_rate_by_lirun - profit_rate_by_actual:.2f}个百分点")

print("\n" + "="*80)
print("📈 具体案例分析")
print("="*80)
# 找出利润额>0但实际利润<0的订单
false_profit = order_agg[(order_agg['利润额'] > 0) & (order_agg['订单实际利润'] <= 0)]
print(f"\n看似赚钱实际亏损的订单: {len(false_profit):,} 笔")
if len(false_profit) > 0:
    print("\n示例订单（前5笔）:")
    example = false_profit[['订单ID', '利润额', '物流配送费', '平台佣金', '订单实际利润']].head(5)
    print(example.to_string())
