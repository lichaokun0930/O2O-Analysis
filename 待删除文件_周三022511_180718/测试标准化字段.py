# -*- coding: utf-8 -*-
"""测试标准化后的字段"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from pathlib import Path
from 真实数据处理器 import RealDataProcessor

excel_file = Path("实际数据/2025-10-19 00_00_00至2025-11-17 23_59_59订单明细数据导出汇总.xlsx")

if excel_file.exists():
    print(f"读取Excel: {excel_file.name}")
    df = pd.read_excel(excel_file)
    
    print(f"\n原始数据: {len(df):,}行")
    print(f"原始字段: {list(df.columns)[:10]}")
    
    # 标准化
    processor = RealDataProcessor()
    df_std = processor.standardize_sales_data(df)
    
    print(f"\n标准化后: {len(df_std):,}行")
    print(f"\n标准化后的字段:")
    for i, col in enumerate(df_std.columns, 1):
        print(f"  {i}. {col}")
    
    # 检查关键字段
    print(f"\n关键字段检查:")
    for field in ['库存', '剩余库存', '商品采购成本', '成本', '条码']:
        if field in df_std.columns:
            non_zero = (df_std[field] != 0).sum() if pd.api.types.is_numeric_dtype(df_std[field]) else len(df_std)
            print(f"  ✅ {field}: 存在, 非零行数 {non_zero:,}/{len(df_std):,}")
        else:
            print(f"  ❌ {field}: 不存在")
