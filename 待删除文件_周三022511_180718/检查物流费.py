import pandas as pd

df = pd.read_excel('实际数据/枫瑞.xlsx')
df_mt = df[df['渠道'] == '美团共橙']
df_no_hc = df_mt[df_mt['一级分类名'] != '耗材']

agg = df_no_hc.groupby('订单ID').agg({'物流配送费': 'sum'})
print(f'物流配送费总和: {agg["物流配送费"].sum():.2f}')
print(f'\n前10个订单:')
print(agg.head(10))
