"""
测试看板实际加载枫瑞店数据时的计算结果
检查是否与预期一致
"""
import pandas as pd
import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))

# 导入calculate_order_metrics函数
from 智能门店看板_Dash版 import calculate_order_metrics

# 加载枫瑞店数据
print("=" * 80)
print("📂 加载枫瑞店数据...")
df = pd.read_excel('实际数据/枫瑞.xlsx')
print(f"✅ 加载完成: {len(df)} 行")

# 剔除耗材
if '一级分类名' in df.columns:
    before = len(df)
    df = df[df['一级分类名'] != '耗材'].copy()
    after = len(df)
    print(f"🔧 剔除耗材: {before} → {after} 行 (剔除{before-after}行)")

print(f"\n原始数据统计:")
print(f"  订单ID数: {df['订单ID'].nunique()}")
print(f"  利润额总和: {df['利润额'].sum():.2f}")
if '物流配送费' in df.columns:
    print(f"  物流配送费(直接sum): {df['物流配送费'].sum():.2f}")
    print(f"  物流配送费(first聚合): {df.groupby('订单ID')['物流配送费'].first().sum():.2f}")
if '平台服务费' in df.columns:
    print(f"  平台服务费(sum): {df['平台服务费'].sum():.2f}")
if '企客后返' in df.columns:
    print(f"  企客后返(sum): {df['企客后返'].sum():.2f}")

# 使用calculate_order_metrics处理
print("\n" + "=" * 80)
print("🔧 调用 calculate_order_metrics(df, calc_mode='all_with_fallback')...")
print("=" * 80)

order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')

print("\n" + "=" * 80)
print("📊 订单聚合结果:")
print(f"  订单数: {len(order_agg)}")
if '利润额' in order_agg.columns:
    print(f"  利润额总和: {order_agg['利润额'].sum():.2f}")
if '物流配送费' in order_agg.columns:
    print(f"  物流配送费总和: {order_agg['物流配送费'].sum():.2f}")
if '平台服务费' in order_agg.columns:
    print(f"  平台服务费总和: {order_agg['平台服务费'].sum():.2f}")
if '企客后返' in order_agg.columns:
    print(f"  企客后返总和: {order_agg['企客后返'].sum():.2f}")
if '订单实际利润' in order_agg.columns:
    print(f"  订单实际利润总和: {order_agg['订单实际利润'].sum():.2f}")

# 对比用户提供的准确数据
print("\n" + "=" * 80)
print("🎯 与用户数据对比:")
print("=" * 80)
user_profit = 62372
user_logistics = 40377
user_platform_fee = 11269

if '利润额' in order_agg.columns:
    calc_profit = order_agg['利润额'].sum()
    print(f"  利润额: {calc_profit:.2f} (用户: {user_profit}) {'✅' if abs(calc_profit - user_profit) < 1000 else '❌'}")

if '物流配送费' in order_agg.columns:
    calc_logistics = order_agg['物流配送费'].sum()
    print(f"  物流配送费: {calc_logistics:.2f} (用户: {user_logistics}) {'✅' if abs(calc_logistics - user_logistics) < 2000 else '❌'}")

if '平台服务费' in order_agg.columns:
    calc_platform = order_agg['平台服务费'].sum()
    print(f"  平台服务费: {calc_platform:.2f} (用户: {user_platform_fee}) {'✅' if abs(calc_platform - user_platform_fee) < 1000 else '❌'}")

# 手工计算订单实际利润
if all(col in order_agg.columns for col in ['利润额', '平台服务费', '物流配送费', '企客后返']):
    manual_profit = (
        order_agg['利润额'].sum() - 
        order_agg['平台服务费'].sum() - 
        order_agg['物流配送费'].sum() + 
        order_agg['企客后返'].sum()
    )
    print(f"\n  手工计算订单实际利润: {manual_profit:.2f}")
    
    expected_profit = user_profit - user_platform_fee - user_logistics
    print(f"  预期订单实际利润: {expected_profit:.2f}")
    print(f"  差异: {abs(manual_profit - expected_profit):.2f}")

print("\n" + "=" * 80)
