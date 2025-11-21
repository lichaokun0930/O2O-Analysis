"""
诊断利润为负值的原因
"""
import pandas as pd
import numpy as np

print("=" * 80)
print("利润异常诊断")
print("=" * 80)

# 读取数据
df = pd.read_excel('实际数据/2025-10-19 00_00_00至2025-11-17 23_59_59订单明细数据导出汇总.xlsx')
print(f"\n✅ 数据行数: {len(df)}")
print(f"✅ 订单数: {df['订单ID'].nunique()}")

# 显示所有列名
print(f"\n📋 所有列名:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i:2d}. {col}")

print("\n" + "=" * 80)
print("第一步: 检查利润额字段")
print("=" * 80)

if '利润额' in df.columns:
    print(f"\n利润额统计:")
    print(f"  总和: {df['利润额'].sum():,.2f}")
    print(f"  均值: {df['利润额'].mean():,.2f}")
    print(f"  最小值: {df['利润额'].min():,.2f}")
    print(f"  最大值: {df['利润额'].max():,.2f}")
    
    # 利润为负的行数
    negative_profit = df[df['利润额'] < 0]
    print(f"\n利润额<0的行数: {len(negative_profit)} ({len(negative_profit)/len(df)*100:.1f}%)")
    
    if len(negative_profit) > 0:
        print(f"\n利润为负的样本(前5行):")
        print(negative_profit[['商品名称', '商品实售价', '成本', '利润额', '销量']].head())

print("\n" + "=" * 80)
print("第二步: 检查成本和售价关系")
print("=" * 80)

if '商品实售价' in df.columns and '成本' in df.columns:
    print(f"\n商品实售价统计:")
    print(f"  均值: {df['商品实售价'].mean():,.2f}")
    print(f"  最小值: {df['商品实售价'].min():,.2f}")
    print(f"  最大值: {df['商品实售价'].max():,.2f}")
    
    print(f"\n成本统计:")
    print(f"  均值: {df['成本'].mean():,.2f}")
    print(f"  最小值: {df['成本'].min():,.2f}")
    print(f"  最大值: {df['成本'].max():,.2f}")
    
    # 成本>售价的情况
    cost_over_price = df[df['成本'] > df['商品实售价']]
    print(f"\n成本>售价的商品: {len(cost_over_price)} 行 ({len(cost_over_price)/len(df)*100:.1f}%)")
    
    if len(cost_over_price) > 0:
        print(f"\n成本>售价样本(前10行):")
        print(cost_over_price[['商品名称', '商品实售价', '成本', '利润额']].head(10))

print("\n" + "=" * 80)
print("第三步: 按订单聚合,检查订单级利润")
print("=" * 80)

# 按订单聚合
order_agg = df.groupby('订单ID').agg({
    '渠道': 'first',
    '利润额': 'sum',
    '平台服务费': 'sum',
    '物流配送费': 'sum',
    '企客后返': 'sum',
    '商品实售价': 'sum',
    '销量': 'sum'
}).reset_index()

# 计算订单实际利润
order_agg['订单实际利润'] = (
    order_agg['利润额'] - 
    order_agg['平台服务费'] - 
    order_agg['物流配送费'] + 
    order_agg['企客后返']
)

print(f"\n订单实际利润统计:")
print(f"  总和: {order_agg['订单实际利润'].sum():,.2f}")
print(f"  均值: {order_agg['订单实际利润'].mean():,.2f}")
print(f"  最小值: {order_agg['订单实际利润'].min():,.2f}")
print(f"  最大值: {order_agg['订单实际利润'].max():,.2f}")

# 利润为负的订单
negative_orders = order_agg[order_agg['订单实际利润'] < 0]
print(f"\n订单实际利润<0的订单: {len(negative_orders)} ({len(negative_orders)/len(order_agg)*100:.1f}%)")

print("\n各成本项统计:")
print(f"  利润额总和: {order_agg['利润额'].sum():,.2f}")
print(f"  平台服务费总和: {order_agg['平台服务费'].sum():,.2f}")
print(f"  物流配送费总和: {order_agg['物流配送费'].sum():,.2f}")
print(f"  企客后返总和: {order_agg['企客后返'].sum():,.2f}")

print("\n" + "=" * 80)
print("第四步: 检查是否是数据字段理解问题")
print("=" * 80)

# 显示一个订单的完整信息
sample_order_id = df['订单ID'].iloc[0]
sample_order = df[df['订单ID'] == sample_order_id]

print(f"\n样本订单ID: {sample_order_id}")
print(f"商品数: {len(sample_order)}")
print(f"\n订单详情:")
display_cols = ['商品名称', '商品实售价', '成本', '销量', '利润额', '平台服务费', '物流配送费', '企客后返']
available_cols = [col for col in display_cols if col in sample_order.columns]
print(sample_order[available_cols])

# 手动计算这个订单的利润
if len(sample_order) > 0:
    total_revenue = (sample_order['商品实售价'] * sample_order['销量']).sum()
    total_cost = (sample_order['成本'] * sample_order['销量']).sum()
    profit_margin = sample_order['利润额'].sum()
    platform_fee = sample_order['平台服务费'].sum()
    logistics_fee = sample_order['物流配送费'].sum()
    rebate = sample_order['企客后返'].sum()
    
    print(f"\n手动计算:")
    print(f"  商品总售价(实售价×销量): {total_revenue:,.2f}")
    print(f"  商品总成本(成本×销量): {total_cost:,.2f}")
    print(f"  毛利(售价-成本): {total_revenue - total_cost:,.2f}")
    print(f"  数据中的利润额: {profit_margin:,.2f}")
    print(f"  平台服务费: {platform_fee:,.2f}")
    print(f"  物流配送费: {logistics_fee:,.2f}")
    print(f"  企客后返: {rebate:,.2f}")
    print(f"  订单实际利润: {profit_margin - platform_fee - logistics_fee + rebate:,.2f}")

print("\n" + "=" * 80)
print("第五步: 检查是否有门店维度字段")
print("=" * 80)

if '门店名称' in df.columns:
    stores = df['门店名称'].unique()
    print(f"\n数据包含的门店:")
    for i, store in enumerate(stores, 1):
        store_orders = df[df['门店名称'] == store]['订单ID'].nunique()
        print(f"  {i}. {store}: {store_orders} 订单")
    
    # 按门店统计利润
    print(f"\n各门店利润统计:")
    store_profit = df.groupby('门店名称').agg({
        '订单ID': 'nunique',
        '利润额': 'sum',
        '平台服务费': 'sum',
        '物流配送费': 'sum'
    }).reset_index()
    
    store_profit['订单实际利润'] = (
        store_profit['利润额'] - 
        store_profit['平台服务费'] - 
        store_profit['物流配送费']
    )
    
    store_profit.columns = ['门店', '订单数', '利润额', '平台服务费', '物流配送费', '订单实际利润']
    print(store_profit.to_string(index=False))

print("\n" + "=" * 80)
print("诊断完成")
print("=" * 80)
