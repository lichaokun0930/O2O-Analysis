"""
验证:过滤掉平台服务费=0的订单后,物流配送费也会减少
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# 加载枫瑞店数据
df = pd.read_excel('实际数据/枫瑞.xlsx')
if '一级分类名' in df.columns:
    df = df[df['一级分类名'] != '耗材'].copy()

# 筛选美团共橙
mt_data = df[df['渠道'] == '美团共橙'].copy()

# 手工订单聚合
from 智能门店看板_Dash版 import calculate_order_metrics

print("=" * 80)
print("🔍 分析订单过滤对各字段的影响")
print("=" * 80)

# 不过滤版本
order_agg_all = mt_data.groupby('订单ID').agg({
    '利润额': 'sum',
    '物流配送费': 'first',
    '平台服务费': 'sum',
    '平台佣金': 'first',
    '企客后返': 'sum'
}).reset_index()

print(f"\n📊 过滤前(所有{len(order_agg_all)}个订单):")
print(f"  利润额总和: {order_agg_all['利润额'].sum():.2f}")
print(f"  物流配送费总和: {order_agg_all['物流配送费'].sum():.2f}")
print(f"  平台服务费总和: {order_agg_all['平台服务费'].sum():.2f}")
print(f"  平台佣金总和: {order_agg_all['平台佣金'].sum():.2f}")

# 计算利润(过滤前)
profit_before = (
    order_agg_all['利润额'].sum() - 
    order_agg_all['平台服务费'].sum() - 
    order_agg_all['物流配送费'].sum()
)
print(f"  订单实际利润: {profit_before:.2f}")

# 过滤平台服务费>0
filtered = order_agg_all[order_agg_all['平台服务费'] > 0].copy()

print(f"\n📊 过滤后(剩余{len(filtered)}个订单,过滤了{len(order_agg_all)-len(filtered)}个):")
print(f"  利润额总和: {filtered['利润额'].sum():.2f}")
print(f"  物流配送费总和: {filtered['物流配送费'].sum():.2f}  ⬅️ 减少了 {order_agg_all['物流配送费'].sum() - filtered['物流配送费'].sum():.2f}")
print(f"  平台服务费总和: {filtered['平台服务费'].sum():.2f}  ⬅️ 减少了 {order_agg_all['平台服务费'].sum() - filtered['平台服务费'].sum():.2f}")

# 计算利润(过滤后)
profit_after = (
    filtered['利润额'].sum() - 
    filtered['平台服务费'].sum() - 
    filtered['物流配送费'].sum()
)
print(f"  订单实际利润: {profit_after:.2f}")

print(f"\n🎯 关键发现:")
print(f"  过滤掉的订单中:")
removed_orders = order_agg_all[order_agg_all['平台服务费'] == 0]
print(f"    利润额: {removed_orders['利润额'].sum():.2f}")
print(f"    物流配送费: {removed_orders['物流配送费'].sum():.2f}")
print(f"    平台服务费: {removed_orders['平台服务费'].sum():.2f}")
print(f"    平台佣金: {removed_orders['平台佣金'].sum():.2f}")

print(f"\n💡 结论:")
print(f"  如果用 all_with_fallback 模式(过滤平台服务费>0或平台佣金>0):")
fallback_filtered = order_agg_all[
    (order_agg_all['平台服务费'] > 0) | (order_agg_all['平台佣金'] > 0)
].copy()
print(f"    剩余订单: {len(fallback_filtered)} 个")
print(f"    利润额: {fallback_filtered['利润额'].sum():.2f}")
print(f"    物流配送费: {fallback_filtered['物流配送费'].sum():.2f}")
print(f"    平台服务费: {fallback_filtered['平台服务费'].sum():.2f}")
profit_fallback = (
    fallback_filtered['利润额'].sum() - 
    fallback_filtered['平台服务费'].sum() - 
    fallback_filtered['物流配送费'].sum()
)
print(f"    订单实际利润: {profit_fallback:.2f}")

print("\n" + "=" * 80)
