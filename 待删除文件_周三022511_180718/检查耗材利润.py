"""
检查耗材商品的利润额情况
"""
import pandas as pd

# 读取源数据
df = pd.read_excel('实际数据/枫瑞.xlsx')

# 筛选美团共橙渠道
mt_data = df[df['渠道'] == '美团共橙'].copy()

print("=" * 80)
print("🔍 检查美团共橙渠道中的耗材数据")
print("=" * 80)

# 筛选耗材
consumables = mt_data[mt_data['一级分类名'] == '耗材'].copy()

print(f"\n耗材数据:")
print(f"  行数: {len(consumables)}")
print(f"  订单数: {consumables['订单ID'].nunique()}")
print(f"  利润额总和: {consumables['利润额'].sum():.2f}")

# 检查利润额分布
print(f"\n利润额分布:")
print(f"  利润额>0: {(consumables['利润额'] > 0).sum()} 行")
print(f"  利润额=0: {(consumables['利润额'] == 0).sum()} 行")
print(f"  利润额<0: {(consumables['利润额'] < 0).sum()} 行")

# 统计
print(f"\n利润额统计:")
print(f"  最大值: {consumables['利润额'].max():.2f}")
print(f"  最小值: {consumables['利润额'].min():.2f}")
print(f"  平均值: {consumables['利润额'].mean():.2f}")
print(f"  总和: {consumables['利润额'].sum():.2f}")

# 显示样本数据
print(f"\n📋 耗材样本数据(前20行):")
print(consumables[['订单ID', '商品名称', '利润额', '商品实售价', '商品采购成本']].head(20).to_string())

# 按订单聚合看看
print(f"\n按订单聚合耗材利润:")
order_consumable_profit = consumables.groupby('订单ID')['利润额'].sum()
print(f"  订单数: {len(order_consumable_profit)}")
print(f"  利润额总和: {order_consumable_profit.sum():.2f}")
print(f"  正利润订单: {(order_consumable_profit > 0).sum()}")
print(f"  零利润订单: {(order_consumable_profit == 0).sum()}")
print(f"  负利润订单: {(order_consumable_profit < 0).sum()}")

# 对比剔除耗材前后的差异
all_profit = mt_data.groupby('订单ID')['利润额'].sum().sum()
no_consumable_profit = mt_data[mt_data['一级分类名'] != '耗材'].groupby('订单ID')['利润额'].sum().sum()

print(f"\n💡 剔除耗材的影响:")
print(f"  未剔除耗材总利润: {all_profit:.2f}")
print(f"  剔除耗材后总利润: {no_consumable_profit:.2f}")
print(f"  耗材利润额: {all_profit - no_consumable_profit:.2f}")
print(f"  差异说明: {'正值=耗材有正利润' if (all_profit - no_consumable_profit) < 0 else '负值=耗材亏损'}")

print("\n" + "=" * 80)
