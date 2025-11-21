import pandas as pd

df = pd.read_excel('实际数据/枫瑞.xlsx')
mt = df[df['渠道']=='美团共橙']
consumables = mt[mt['一级分类名']=='耗材']

print(f"耗材利润额总和: {consumables['利润额'].sum():.2f}")
print(f"利润>0: {(consumables['利润额']>0).sum()}行")
print(f"利润=0: {(consumables['利润额']==0).sum()}行")  
print(f"利润<0: {(consumables['利润额']<0).sum()}行")
print(f"\n未剔除耗材: {mt['利润额'].sum():.2f}")
no_consumables = mt[mt['一级分类名']!='耗材']
print(f"剔除耗材后: {no_consumables['利润额'].sum():.2f}")
print(f"差异: {mt['利润额'].sum() - no_consumables['利润额'].sum():.2f}")
