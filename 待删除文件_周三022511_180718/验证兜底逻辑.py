"""
验证all_with_fallback模式下的平台服务费兜底逻辑
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from 智能门店看板_Dash版 import calculate_order_metrics

# 加载枫瑞店数据
df = pd.read_excel('实际数据/枫瑞.xlsx')
if '一级分类名' in df.columns:
    df = df[df['一级分类名'] != '耗材'].copy()

# 筛选美团共橙
mt_data = df[df['渠道'] == '美团共橙'].copy()
print("=" * 80)
print(f"美团共橙数据: {len(mt_data)} 行, {mt_data['订单ID'].nunique()} 个订单")

# 订单聚合
order_agg = calculate_order_metrics(mt_data, calc_mode='all_with_fallback')

print(f"\n📊 关键字段对比:")
print(f"  平台服务费总和: {order_agg['平台服务费'].sum():.2f}")
print(f"  平台佣金总和: {order_agg['平台佣金'].sum():.2f}")

# 检查平台服务费<=0的订单数
service_fee_zero = (order_agg['平台服务费'] <= 0).sum()
print(f"\n平台服务费<=0的订单: {service_fee_zero} / {len(order_agg)}")

# 模拟兜底逻辑
service_fee = order_agg['平台服务费'].copy()
commission = order_agg['平台佣金'].copy()
fallback_mask = (service_fee <= 0)
effective_service_fee = service_fee.mask(fallback_mask, commission)

print(f"\n兜底后有效服务费总和: {effective_service_fee.sum():.2f}")

# 手工计算利润(使用兜底后的服务费)
manual_profit_with_fallback = (
    order_agg['利润额'].sum() - 
    effective_service_fee.sum() - 
    order_agg['物流配送费'].sum() + 
    order_agg['企客后返'].sum()
)

print(f"\n📊 利润计算对比:")
print(f"  使用原始平台服务费: {order_agg['利润额'].sum():.2f} - {order_agg['平台服务费'].sum():.2f} - {order_agg['物流配送费'].sum():.2f} = {order_agg['利润额'].sum() - order_agg['平台服务费'].sum() - order_agg['物流配送费'].sum():.2f}")
print(f"  使用兜底后服务费: {order_agg['利润额'].sum():.2f} - {effective_service_fee.sum():.2f} - {order_agg['物流配送费'].sum():.2f} = {manual_profit_with_fallback:.2f}")
print(f"  系统计算的订单实际利润: {order_agg['订单实际利润'].sum():.2f}")

print(f"\n差异: {abs(manual_profit_with_fallback - order_agg['订单实际利润'].sum()):.2f}")

# 抽样检查
print(f"\n📋 抽样订单(平台服务费=0的订单):")
zero_fee_orders = order_agg[order_agg['平台服务费'] == 0].head()
for idx, row in zero_fee_orders.iterrows():
    print(f"\n  订单 {row['订单ID']}:")
    print(f"    平台服务费: {row['平台服务费']:.2f}")
    print(f"    平台佣金: {row['平台佣金']:.2f}")
    print(f"    利润额: {row['利润额']:.2f}")
    print(f"    物流配送费: {row['物流配送费']:.2f}")
    # 手工计算(用佣金)
    manual_with_commission = row['利润额'] - row['平台佣金'] - row['物流配送费']
    print(f"    手工计算(用佣金): {manual_with_commission:.2f}")
    print(f"    系统计算: {row['订单实际利润']:.2f}")
    print(f"    {'✅ 匹配' if abs(manual_with_commission - row['订单实际利润']) < 0.01 else '❌ 不匹配'}")

print("\n" + "=" * 80)
