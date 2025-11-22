"""
检查枫瑞店美团共橙渠道的准确数据
"""
import pandas as pd

# 加载枫瑞店数据
df = pd.read_excel('实际数据/枫瑞.xlsx')
print(f"原始数据: {len(df)} 行")

# 剔除耗材
if '一级分类名' in df.columns:
    df = df[df['一级分类名'] != '耗材'].copy()
print(f"剔除耗材后: {len(df)} 行")

# 筛选美团共橙渠道
mt_data = df[df['渠道'] == '美团共橙'].copy()
print(f"\n美团共橙渠道原始数据: {len(mt_data)} 行")
print(f"订单ID数量: {mt_data['订单ID'].nunique()} 个")

# 检查利润额
print(f"\n利润额统计(原始数据,未聚合):")
print(f"  利润额总和: {mt_data['利润额'].sum():.2f}")
print(f"  利润额非0的行数: {(mt_data['利润额'] != 0).sum()}")
print(f"  利润额为0的行数: {(mt_data['利润额'] == 0).sum()}")

# 按订单聚合利润额
order_profit = mt_data.groupby('订单ID')['利润额'].sum()
print(f"\n按订单聚合后的利润额:")
print(f"  订单数: {len(order_profit)}")
print(f"  利润额总和: {order_profit.sum():.2f}")
print(f"  利润额>0的订单: {(order_profit > 0).sum()}")
print(f"  利润额=0的订单: {(order_profit == 0).sum()}")
print(f"  利润额<0的订单: {(order_profit < 0).sum()}")

# 检查平台服务费
print(f"\n平台服务费统计:")
print(f"  平台服务费总和(原始): {mt_data['平台服务费'].sum():.2f}")
order_service_fee = mt_data.groupby('订单ID')['平台服务费'].sum()
print(f"  平台服务费总和(聚合): {order_service_fee.sum():.2f}")
print(f"  平台服务费>0的订单: {(order_service_fee > 0).sum()}")
print(f"  平台服务费=0的订单: {(order_service_fee == 0).sum()}")

# 检查物流配送费
print(f"\n物流配送费统计:")
print(f"  物流配送费总和(直接sum): {mt_data['物流配送费'].sum():.2f}")
order_logistics = mt_data.groupby('订单ID')['物流配送费'].first()
print(f"  物流配送费总和(first聚合): {order_logistics.sum():.2f}")

# 检查你说的数字
print(f"\n🎯 你提供的数据验证:")
print(f"  你说的利润额: 31,176")
print(f"  实际利润额: {order_profit.sum():.2f}")
print(f"  差异: {abs(31176 - order_profit.sum()):.2f}")
