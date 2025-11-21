import pandas as pd

df = pd.read_excel('实际数据/枫瑞.xlsx')
print(f'原始数据: {len(df)}行')

mt = df[df['渠道']=='美团共橙']
print(f'美团共橙: {len(mt)}行')

haocai = mt[mt['一级分类名']=='耗材']
print(f'耗材行数: {len(haocai)}行')
print(f'耗材利润: {haocai["利润额"].sum():.2f}')

print(f'\n美团共橙总利润额: {mt["利润额"].sum():.2f}')
print(f'不含耗材利润额: {mt[mt["一级分类名"]!="耗材"]["利润额"].sum():.2f}')
