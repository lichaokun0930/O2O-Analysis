# -*- coding: utf-8 -*-
import pandas as pd
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

df = pd.read_excel('实际数据/金寨.xlsx')

print("金寨.xlsx 文件信息：")
print(f"数据行数: {len(df)}")
print(f"门店名称: {df['门店名称'].unique().tolist()}")
print(f"渠道: {df['渠道'].unique().tolist()}")
print(f"时间范围: {df['下单时间'].min()} 至 {df['下单时间'].max()}")
