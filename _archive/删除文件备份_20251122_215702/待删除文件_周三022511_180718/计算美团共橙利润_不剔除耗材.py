"""
美团共橙利润计算 - 不剔除耗材
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# 读取源数据
df = pd.read_excel('实际数据/枫瑞.xlsx')

# 筛选美团共橙(不剔除耗材)
mt_data = df[df['渠道'] == '美团共橙'].copy()

print("=" * 80)
print("美团共橙利润计算 - 不剔除耗材")
print("=" * 80)

# 按订单聚合
order_agg = mt_data.groupby('订单ID').agg({
    '利润额': 'sum',
    '物流配送费': 'first',
    '平台服务费': 'sum',
    '平台佣金': 'first',
    '企客后返': 'sum'
}).reset_index()

print(f"\n订单聚合后:")
print(f"  订单数: {len(order_agg)}")
print(f"  利润额总和: {order_agg['利润额'].sum():.2f}")
print(f"  物流配送费总和: {order_agg['物流配送费'].sum():.2f}")
print(f"  平台服务费总和: {order_agg['平台服务费'].sum():.2f}")
print(f"  企客后返总和: {order_agg['企客后返'].sum():.2f}")

# 计算订单实际利润
order_agg['订单实际利润'] = (
    order_agg['利润额'] - 
    order_agg['平台服务费'] - 
    order_agg['物流配送费'] + 
    order_agg['企客后返']
)

print(f"\n订单实际利润计算:")
print(f"  公式: 利润额 - 平台服务费 - 物流配送费 + 企客后返")
print(f"  {order_agg['利润额'].sum():.2f} - {order_agg['平台服务费'].sum():.2f} - {order_agg['物流配送费'].sum():.2f} + {order_agg['企客后返'].sum():.2f}")
print(f"  = {order_agg['订单实际利润'].sum():.2f}")

# 过滤平台服务费>0的订单
filtered = order_agg[order_agg['平台服务费'] > 0].copy()

print(f"\n过滤平台服务费=0的订单后:")
print(f"  剩余订单数: {len(filtered)}")
print(f"  利润额总和: {filtered['利润额'].sum():.2f}")
print(f"  物流配送费总和: {filtered['物流配送费'].sum():.2f}")
print(f"  平台服务费总和: {filtered['平台服务费'].sum():.2f}")
print(f"  订单实际利润: {filtered['订单实际利润'].sum():.2f}")

print(f"\n最终答案:")
print(f"  美团共橙订单实际利润(过滤后) = {filtered['订单实际利润'].sum():.2f} 元")

print("\n" + "=" * 80)
