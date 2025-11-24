# -*- coding: utf-8 -*-
"""检查Excel原始数据"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from pathlib import Path

excel_file = Path("实际数据/2025-10-19 00_00_00至2025-11-17 23_59_59订单明细数据导出汇总.xlsx")

if excel_file.exists():
    print(f"读取Excel: {excel_file.name}")
    df = pd.read_excel(excel_file)
    
    print(f"\n数据行数: {len(df):,}")
    print(f"\n字段列表:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    
    # 检查关键字段
    key_fields = ['库存', '剩余库存', '成本', '商品采购成本']
    print(f"\n关键字段检查:")
    for field in key_fields:
        if field in df.columns:
            non_zero = (df[field] != 0).sum()
            print(f"  ✅ {field}: 非零行数 {non_zero:,}/{len(df):,}")
            if non_zero > 0:
                print(f"      范围: {df[field].min():.2f} ~ {df[field].max():.2f}, 均值: {df[field].mean():.2f}")
        else:
            print(f"  ❌ {field}: 不存在")
else:
    print(f"❌ Excel文件不存在: {excel_file}")
