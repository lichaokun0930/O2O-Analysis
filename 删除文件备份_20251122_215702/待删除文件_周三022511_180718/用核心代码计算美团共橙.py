"""
使用核心代码逻辑计算美团共橙利润
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from 智能门店看板_Dash版 import calculate_order_metrics

# 加载数据
df = pd.read_excel('实际数据/枫瑞.xlsx')

print("=" * 80)
print("使用核心代码逻辑计算美团共橙利润")
print("=" * 80)

# Step 1: 剔除耗材(模拟核心代码的数据加载逻辑)
original_rows = len(df)
if '一级分类名' in df.columns:
    df = df[df['一级分类名'] != '耗材'].copy()
    removed = original_rows - len(df)
    print(f"\nStep 1: 剔除耗材")
    print(f"  原始数据: {original_rows} 行")
    print(f"  剔除耗材: {removed} 行")
    print(f"  剩余数据: {len(df)} 行")

# Step 2: 筛选美团共橙渠道
mt_data = df[df['渠道'] == '美团共橙'].copy()
print(f"\nStep 2: 筛选美团共橙")
print(f"  数据行数: {len(mt_data)}")
print(f"  订单数: {mt_data['订单ID'].nunique()}")

# Step 3: 使用核心代码的calculate_order_metrics函数
print(f"\nStep 3: 调用 calculate_order_metrics(calc_mode='all_with_fallback')")
order_agg = calculate_order_metrics(mt_data, calc_mode='all_with_fallback')

# Step 4: 统计结果
print(f"\n" + "=" * 80)
print(f"📊 计算结果:")
print(f"=" * 80)
print(f"  订单数: {len(order_agg)}")
print(f"  利润额总和: {order_agg['利润额'].sum():.2f}")
print(f"  平台服务费总和: {order_agg['平台服务费'].sum():.2f}")
print(f"  物流配送费总和: {order_agg['物流配送费'].sum():.2f}")
print(f"  企客后返总和: {order_agg['企客后返'].sum():.2f}")
print(f"  订单实际利润总和: {order_agg['订单实际利润'].sum():.2f}")

print(f"\n✅ 美团共橙订单实际利润 = {order_agg['订单实际利润'].sum():.2f} 元")
print("\n" + "=" * 80)
