"""
对比你提供的订单ID和利润额,找出差异
"""
import pandas as pd

# 读取你提供的订单列表
your_data = pd.read_excel('门店数据/枫瑞店.xlsx', sheet_name='Sheet1')
print("=" * 80)
print("📋 你提供的数据:")
print("=" * 80)
print(f"  订单数: {len(your_data)}")
print(f"  利润额总和: {your_data['利润额'].sum():.2f}")
print(f"  列名: {your_data.columns.tolist()}")

# 重命名列以便对比
your_data.columns = ['订单ID', '利润额_你的']

# 读取源数据
source_df = pd.read_excel('实际数据/枫瑞.xlsx')
print(f"\n📂 源数据(实际数据/枫瑞.xlsx):")
print(f"  总行数: {len(source_df)}")

# 筛选美团共橙
mt_source = source_df[source_df['渠道'] == '美团共橙'].copy()
print(f"\n美团共橙源数据:")
print(f"  行数: {len(mt_source)}")
print(f"  订单数: {mt_source['订单ID'].nunique()}")

# 按订单聚合利润额(不剔除耗材)
source_profit_no_filter = mt_source.groupby('订单ID')['利润额'].sum().reset_index()
source_profit_no_filter.columns = ['订单ID', '利润额_源数据未剔除耗材']

print(f"\n源数据聚合(未剔除耗材):")
print(f"  订单数: {len(source_profit_no_filter)}")
print(f"  利润额总和: {source_profit_no_filter['利润额_源数据未剔除耗材'].sum():.2f}")

# 剔除耗材后
mt_clean = source_df[(source_df['渠道'] == '美团共橙') & (source_df['一级分类名'] != '耗材')].copy()
source_profit_clean = mt_clean.groupby('订单ID')['利润额'].sum().reset_index()
source_profit_clean.columns = ['订单ID', '利润额_源数据剔除耗材']

print(f"\n源数据聚合(剔除耗材):")
print(f"  订单数: {len(source_profit_clean)}")
print(f"  利润额总和: {source_profit_clean['利润额_源数据剔除耗材'].sum():.2f}")

# 合并对比
merged = your_data.merge(source_profit_no_filter, on='订单ID', how='outer', indicator=True)
merged = merged.merge(source_profit_clean, on='订单ID', how='outer')

print(f"\n" + "=" * 80)
print("🔍 对比结果:")
print("=" * 80)

# 检查订单ID是否一致
only_in_yours = merged[merged['_merge'] == 'left_only']
only_in_source = merged[merged['_merge'] == 'right_only']
in_both = merged[merged['_merge'] == 'both']

print(f"\n订单ID对比:")
print(f"  只在你的表中: {len(only_in_yours)} 个订单")
print(f"  只在源数据中: {len(only_in_source)} 个订单")
print(f"  两边都有: {len(in_both)} 个订单")

if len(only_in_yours) > 0:
    print(f"\n只在你的表中的订单(前10个):")
    print(only_in_yours[['订单ID', '利润额_你的']].head(10))

if len(only_in_source) > 0:
    print(f"\n只在源数据中的订单(前10个):")
    print(only_in_source[['订单ID', '利润额_源数据未剔除耗材']].head(10))

# 对比利润额差异
in_both_copy = in_both.copy()
in_both_copy['差异_未剔除'] = in_both_copy['利润额_你的'] - in_both_copy['利润额_源数据未剔除耗材']
in_both_copy['差异_剔除后'] = in_both_copy['利润额_你的'] - in_both_copy['利润额_源数据剔除耗材']

print(f"\n利润额对比(两边都有的订单):")
print(f"  你的利润额总和: {in_both_copy['利润额_你的'].sum():.2f}")
print(f"  源数据利润额总和(未剔除耗材): {in_both_copy['利润额_源数据未剔除耗材'].sum():.2f}")
print(f"  源数据利润额总和(剔除耗材): {in_both_copy['利润额_源数据剔除耗材'].sum():.2f}")

# 检查有差异的订单
diff_orders = in_both_copy[abs(in_both_copy['差异_未剔除']) > 0.01]
print(f"\n利润额有差异的订单(未剔除耗材对比): {len(diff_orders)} 个")
if len(diff_orders) > 0:
    print(diff_orders[['订单ID', '利润额_你的', '利润额_源数据未剔除耗材', '差异_未剔除']].head(10))
else:
    print("  ✅ 所有订单利润额完全一致!")

print("\n" + "=" * 80)
