"""
检查物流配送费差异
"""
import pandas as pd

df = pd.read_excel('实际数据/枫瑞.xlsx')

print("=" * 80)
print("物流配送费字段检查")
print("=" * 80)

# 查看物流相关字段
logistics_cols = [col for col in df.columns if '物流' in col or '配送' in col]
print(f"\n物流/配送相关字段:")
for col in logistics_cols:
    print(f"  - {col}")

# 物流配送费统计
print(f"\n物流配送费字段统计:")
print(f"  总和(行级): {df['物流配送费'].sum():,.2f}")
print(f"  非零行数: {(df['物流配送费'] > 0).sum()}")
print(f"  为零行数: {(df['物流配送费'] == 0).sum()}")

# 按订单聚合
order_logistics = df.groupby('订单ID')['物流配送费'].agg(['first', 'sum', 'count'])
print(f"\n按订单聚合:")
print(f"  使用first(每单取第一个值)总和: {order_logistics['first'].sum():,.2f}")
print(f"  使用sum(每单累加)总和: {order_logistics['sum'].sum():,.2f}")

print(f"\n样本数据(前10个订单):")
print(order_logistics.head(10))

# 检查每个订单的物流费是否重复
print(f"\n检查重复统计:")
multi_row_orders = order_logistics[order_logistics['count'] > 1]
print(f"  多行订单数: {len(multi_row_orders)}")
if len(multi_row_orders) > 0:
    # 看看这些订单的物流费是不是每行都一样
    sample_order = multi_row_orders.index[0]
    sample_data = df[df['订单ID'] == sample_order][['订单ID', '商品名称', '物流配送费']]
    print(f"\n  样本订单 {sample_order} 的物流费:")
    print(sample_data)

# 显示配送距离
if '配送距离' in df.columns:
    print(f"\n配送距离统计:")
    print(f"  平均: {df['配送距离'].mean():.2f} km")
    print(f"  最大: {df['配送距离'].max():.2f} km")

print("\n" + "=" * 80)
print("结论")
print("=" * 80)
print(f"""
您说的物流配送费: 40,377
我计算的(错误方法-sum): 165,852.90
正确方法(first): {order_logistics['first'].sum():,.2f}

差异原因: 每个订单有多个商品行,物流费在每行都重复了!
应该用 first() 或 max() 而不是 sum()
""")
