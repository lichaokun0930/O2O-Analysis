#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查标准化后的数据字段
"""

import pandas as pd
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent

# 导入真实数据处理器
sys.path.insert(0, str(APP_DIR))
from 真实数据处理器 import RealDataProcessor

# 加载Excel文件
excel_file = APP_DIR / "门店数据" / "2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"

print(f"📄 读取文件: {excel_file.name}")
df = pd.read_excel(excel_file)
print(f"📊 原始数据加载: {len(df):,} 行 × {len(df.columns)} 列\n")

print("原始字段:")
print(df.columns.tolist())

# 使用RealDataProcessor标准化
processor = RealDataProcessor("实际数据")
df_standardized = processor.standardize_sales_data(df)

print("\n标准化后的字段:")
print(df_standardized.columns.tolist())

print("\n字段映射对比:")
for col in df_standardized.columns:
    print(f"  - {col}")
