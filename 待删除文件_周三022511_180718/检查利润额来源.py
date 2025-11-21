"""
检查美团共橙的利润额到底是多少
"""
import pandas as pd

# 加载枫瑞店数据
df = pd.read_excel('实际数据/枫瑞.xlsx')

# 剔除耗材
if '一级分类名' in df.columns:
    df = df[df['一级分类名'] != '耗材'].copy()

# 筛选美团共橙
mt_data = df[df['渠道'] == '美团共橙'].copy()

print("=" * 80)
print("🔍 检查美团共橙利润额来源")
print("=" * 80)

print(f"\n原始数据(美团共橙):")
print(f"  总行数: {len(mt_data)}")
print(f"  订单数: {mt_data['订单ID'].nunique()}")

# 直接sum利润额
print(f"\n📊 利润额统计:")
print(f"  利润额列直接sum: {mt_data['利润额'].sum():.2f}")
print(f"  利润额>0的行: {len(mt_data[mt_data['利润额'] > 0])}")
print(f"  利润额=0的行: {len(mt_data[mt_data['利润额'] == 0])}")
print(f"  利润额<0的行: {len(mt_data[mt_data['利润额'] < 0])}")

# 按订单聚合
order_profit = mt_data.groupby('订单ID')['利润额'].sum()
print(f"\n📊 按订单聚合后:")
print(f"  订单数: {len(order_profit)}")
print(f"  利润额总和: {order_profit.sum():.2f}")
print(f"  利润额>0的订单: {len(order_profit[order_profit > 0])}")
print(f"  利润额=0的订单: {len(order_profit[order_profit == 0])}")
print(f"  利润额<0的订单: {len(order_profit[order_profit < 0])}")

# 检查平台服务费=0的订单
order_service_fee = mt_data.groupby('订单ID')['平台服务费'].sum()
zero_fee_orders = order_service_fee[order_service_fee == 0].index

print(f"\n📊 平台服务费=0的订单:")
print(f"  数量: {len(zero_fee_orders)}")

# 这些订单的利润额
profit_of_zero_fee = order_profit[order_profit.index.isin(zero_fee_orders)]
print(f"  这些订单的利润额总和: {profit_of_zero_fee.sum():.2f}")

# 平台服务费>0的订单
positive_fee_orders = order_service_fee[order_service_fee > 0].index
profit_of_positive_fee = order_profit[order_profit.index.isin(positive_fee_orders)]
print(f"\n📊 平台服务费>0的订单:")
print(f"  数量: {len(positive_fee_orders)}")
print(f"  这些订单的利润额总和: {profit_of_positive_fee.sum():.2f}")

print("\n" + "=" * 80)
