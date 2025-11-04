#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试按日分析的日期筛选问题"""

import pandas as pd
from datetime import timedelta
from pathlib import Path
import sys

# 设置stdout编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 加载数据
data_file = Path("门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx")
df = pd.read_excel(data_file)

print(f"数据行数: {len(df)}")

# 转换日期
df['日期'] = pd.to_datetime(df['下单时间'], errors='coerce')

print(f"日期列类型: {df['日期'].dtype}")
print(f"日期范围: {df['日期'].min()} 至 {df['日期'].max()}")

# 模拟按日分析的日期计算
max_date = df['日期'].max()
min_date = df['日期'].min()

print(f"\n测试按日筛选:")
print(f"max_date = {max_date} (类型: {type(max_date)})")

# 测试Period 0的筛选
i = 0
current_start = max_date - timedelta(days=i)
current_end = current_start

print(f"\nPeriod {i}:")
print(f"  current_start = {current_start} (类型: {type(current_start)})")
print(f"  current_end = {current_end}")

# 筛选
current_data = df[(df['日期'] >= current_start) & (df['日期'] <= current_end)]
print(f"  筛选结果: {len(current_data)}条")

# 查看09-30的实际数据
sept_30_data = df[df['日期'].dt.date == pd.Timestamp('2025-09-30').date()]
print(f"\n09-30实际数据: {len(sept_30_data)}条")
print(f"  时间范围: {sept_30_data['日期'].min()} 至 {sept_30_data['日期'].max()}")

# 测试：如果将current_start/current_end设置为当天的起始和结束时间
import pandas as pd
from datetime import datetime

current_date = pd.Timestamp('2025-09-30')
current_start_v2 = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
current_end_v2 = current_date.replace(hour=23, minute=59, second=59, microsecond=999999)

print(f"\n修正后的筛选:")
print(f"  current_start_v2 = {current_start_v2}")
print(f"  current_end_v2 = {current_end_v2}")

current_data_v2 = df[(df['日期'] >= current_start_v2) & (df['日期'] <= current_end_v2)]
print(f"  筛选结果: {len(current_data_v2)}条")
