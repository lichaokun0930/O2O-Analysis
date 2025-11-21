"""
诊断美团共橙渠道为什么利润为负
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from 智能门店看板_Dash版 import calculate_order_metrics

# 加载枫瑞店数据
print("=" * 80)
print("📂 加载枫瑞店数据...")
df = pd.read_excel('实际数据/枫瑞.xlsx')

# 剔除耗材
if '一级分类名' in df.columns:
    df = df[df['一级分类名'] != '耗材'].copy()

print(f"总数据: {len(df)} 行, {df['订单ID'].nunique()} 个订单")

# 检查渠道分布
print(f"\n渠道分布:")
print(df['渠道'].value_counts())

# 筛选美团共橙渠道
mt_data = df[df['渠道'] == '美团共橙'].copy()
print(f"\n美团共橙数据: {len(mt_data)} 行, {mt_data['订单ID'].nunique()} 个订单")

# 原始数据统计
print(f"\n📊 美团共橙原始数据统计:")
print(f"  利润额总和: {mt_data['利润额'].sum():.2f}")
print(f"  物流配送费(直接sum): {mt_data['物流配送费'].sum():.2f}")
print(f"  物流配送费(first聚合): {mt_data.groupby('订单ID')['物流配送费'].first().sum():.2f}")
print(f"  平台服务费(sum): {mt_data['平台服务费'].sum():.2f}")
print(f"  企客后返(sum): {mt_data['企客后返'].sum():.2f}")

# 使用calculate_order_metrics处理
print("\n" + "=" * 80)
print("🔧 调用 calculate_order_metrics...")
order_agg = calculate_order_metrics(mt_data, calc_mode='all_with_fallback')

print(f"\n📊 订单聚合后:")
print(f"  订单数: {len(order_agg)}")
print(f"  利润额总和: {order_agg['利润额'].sum():.2f}")
print(f"  物流配送费总和: {order_agg['物流配送费'].sum():.2f}")
print(f"  平台服务费总和: {order_agg['平台服务费'].sum():.2f}")
print(f"  企客后返总和: {order_agg['企客后返'].sum():.2f}")
print(f"  订单实际利润总和: {order_agg['订单实际利润'].sum():.2f}")

# 手工验证公式
manual_profit = (
    order_agg['利润额'].sum() - 
    order_agg['平台服务费'].sum() - 
    order_agg['物流配送费'].sum() + 
    order_agg['企客后返'].sum()
)
print(f"\n手工验证公式:")
print(f"  {order_agg['利润额'].sum():.2f} - {order_agg['平台服务费'].sum():.2f} - {order_agg['物流配送费'].sum():.2f} + {order_agg['企客后返'].sum():.2f}")
print(f"  = {manual_profit:.2f}")

# 检查样本订单
print(f"\n📋 样本订单 (前5个):")
sample_orders = order_agg.head()
for idx, row in sample_orders.iterrows():
    print(f"\n  订单 {row['订单ID']}:")
    print(f"    利润额: {row['利润额']:.2f}")
    print(f"    平台服务费: {row['平台服务费']:.2f}")
    print(f"    物流配送费: {row['物流配送费']:.2f}")
    print(f"    企客后返: {row['企客后返']:.2f}")
    print(f"    订单实际利润: {row['订单实际利润']:.2f}")
    manual = row['利润额'] - row['平台服务费'] - row['物流配送费'] + row['企客后返']
    print(f"    手工计算: {manual:.2f} {'✅' if abs(manual - row['订单实际利润']) < 0.01 else '❌'}")

# 分析负利润订单
negative_orders = order_agg[order_agg['订单实际利润'] < 0]
print(f"\n🔴 负利润订单分析:")
print(f"  负利润订单数: {len(negative_orders)} / {len(order_agg)} ({len(negative_orders)/len(order_agg)*100:.1f}%)")
print(f"  负利润总额: {negative_orders['订单实际利润'].sum():.2f}")

print("\n" + "=" * 80)
