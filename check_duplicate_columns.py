#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查Excel文件中的重复列名"""

import pandas as pd
import os
from collections import Counter

def check_duplicate_columns(file_path):
    """检查Excel文件中的重复列名"""
    print(f"\n{'='*80}")
    print(f"📋 检查文件: {os.path.basename(file_path)}")
    print(f"{'='*80}\n")
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        print(f"✅ 文件读取成功")
        print(f"📊 数据维度: {df.shape[0]} 行 × {df.shape[1]} 列\n")
        
        # 获取所有列名
        all_columns = df.columns.tolist()
        
        # 统计列名出现次数
        column_counts = Counter(all_columns)
        
        # 找出重复的列名
        duplicates = {col: count for col, count in column_counts.items() if count > 1}
        
        if duplicates:
            print("⚠️  发现重复列名！\n")
            print(f"{'列名':<30} {'出现次数':>10}")
            print("-" * 42)
            for col, count in duplicates.items():
                print(f"{col:<30} {count:>10}")
            
            print(f"\n📍 重复列名在列表中的位置:")
            for col in duplicates.keys():
                positions = [i for i, c in enumerate(all_columns) if c == col]
                print(f"  '{col}': 索引位置 {positions}")
        else:
            print("✅ 没有发现重复列名")
        
        print(f"\n📝 完整列名列表 (共{len(all_columns)}列):")
        print("-" * 80)
        for i, col in enumerate(all_columns, 1):
            marker = " ⚠️ " if column_counts[col] > 1 else ""
            print(f"{i:3d}. {col}{marker}")
        
        # 显示前几行数据
        print(f"\n📄 数据预览 (前5行):")
        print("-" * 80)
        print(df.head())
        
    except Exception as e:
        print(f"❌ 读取文件失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 递归查找所有Excel文件
    excel_files = []
    
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(('.xlsx', '.xls')):
                excel_files.append(os.path.join(root, file))
    
    if not excel_files:
        print(f"❌ 没有找到Excel文件")
        exit(1)
    
    print(f"\n找到 {len(excel_files)} 个Excel文件:")
    for i, f in enumerate(excel_files, 1):
        print(f"  {i}. {f}")
    
    # 检查每个文件
    for file_path in excel_files:
        check_duplicate_columns(file_path)
        print("\n")
