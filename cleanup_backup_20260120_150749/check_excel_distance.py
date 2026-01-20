# -*- coding: utf-8 -*-
"""检查原始Excel中的配送距离字段"""
import pandas as pd
from pathlib import Path

STORE_NAME = "厉臣便利（镇江平昌路店）"
DATA_DIR = Path(__file__).parent / "实际数据"

# 读取Excel文件
excel_files = list(DATA_DIR.glob("*.xlsx"))
print(f"找到 {len(excel_files)} 个Excel文件")

for f in excel_files:
    if f.name.startswith("~$"):
        continue
    print(f"\n检查文件: {f.name}")
    try:
        df = pd.read_excel(f)
        print(f"  总行数: {len(df)}")
        print(f"  列名: {list(df.columns)}")
        
        # 查找配送距离相关列
        dist_cols = [c for c in df.columns if '距离' in c or 'distance' in c.lower()]
        print(f"  配送距离相关列: {dist_cols}")
        
        # 筛选该门店
        if '门店名称' in df.columns:
            store_df = df[df['门店名称'] == STORE_NAME]
            print(f"  {STORE_NAME} 行数: {len(store_df)}")
            if dist_cols and len(store_df) > 0:
                for col in dist_cols:
                    print(f"    {col} 非零值: {(store_df[col] > 0).sum()}")
                    print(f"    {col} 样本: {store_df[col].head(10).tolist()}")
    except Exception as e:
        print(f"  错误: {e}")
