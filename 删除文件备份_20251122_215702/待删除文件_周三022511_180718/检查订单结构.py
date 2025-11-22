import pandas as pd

df = pd.read_excel('实际数据/祥和路.xlsx')

# 检查一个订单的详情
sample_order = df['订单ID'].value_counts().head(1).index[0]
order_data = df[df['订单ID'] == sample_order][['订单ID', '商品名称', '销量', '商品实售价', '利润额', '平台服务费']].head(10)

print('示例订单详情:')
print(order_data.to_string(index=False))
print(f'\n该订单商品数: {len(order_data)}')
print(f'利润额sum: {order_data["利润额"].sum():.2f}')
print(f'利润额first: {order_data["利润额"].iloc[0]:.2f}')

# 统计多商品订单
multi_item_orders = df.groupby('订单ID').size()
print(f'\n多商品订单统计:')
print(f'总订单数: {len(multi_item_orders)}')
print(f'多商品订单数: {(multi_item_orders > 1).sum()}')
print(f'平均商品数: {multi_item_orders.mean():.2f}')
