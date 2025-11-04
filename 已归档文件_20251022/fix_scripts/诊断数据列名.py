# -*- coding: utf-8 -*-
"""
诊断订单数据文件的列名
帮助确认耗材剔除字段名称
"""

import pandas as pd
import sys

def diagnose_excel_columns(file_path):
    """诊断Excel文件的列名"""
    try:
        print(f"\n正在读取文件: {file_path}\n")
        df = pd.read_excel(file_path)
        
        print("=" * 80)
        print(f"文件基本信息:")
        print("=" * 80)
        print(f"总行数: {len(df):,}")
        print(f"总列数: {len(df.columns)}")
        
        print("\n" + "=" * 80)
        print("所有列名列表:")
        print("=" * 80)
        for i, col in enumerate(df.columns, 1):
            print(f"{i:3d}. {col}")
        
        # 检查可能的分类列
        print("\n" + "=" * 80)
        print("包含'分类'的列名:")
        print("=" * 80)
        category_cols = [col for col in df.columns if '分类' in col]
        if category_cols:
            for col in category_cols:
                unique_values = df[col].unique()[:10]  # 只显示前10个
                print(f"\n列名: {col}")
                print(f"  唯一值数量: {df[col].nunique()}")
                print(f"  前10个唯一值: {list(unique_values)}")
        else:
            print("未找到包含'分类'的列")
        
        # 检查可能的商品名列
        print("\n" + "=" * 80)
        print("包含'商品'或'名称'的列名:")
        print("=" * 80)
        product_cols = [col for col in df.columns if '商品' in col or '名称' in col]
        for col in product_cols:
            print(f"\n列名: {col}")
            # 检查是否有购物袋
            shopping_bag_count = df[col].astype(str).str.contains('购物袋', na=False).sum()
            if shopping_bag_count > 0:
                print(f"  🔴 包含购物袋的行数: {shopping_bag_count}")
                print(f"  购物袋样例:")
                samples = df[df[col].astype(str).str.contains('购物袋', na=False)][col].head(5)
                for sample in samples:
                    print(f"    - {sample}")
        
        print("\n" + "=" * 80)
        print("建议:")
        print("=" * 80)
        if category_cols:
            print(f"✓ 找到 {len(category_cols)} 个分类列")
            print(f"  建议使用的列名: {category_cols[0]}")
            print(f"\n  请检查该列是否包含'耗材'值")
            if '耗材' in df[category_cols[0]].values:
                consumable_count = (df[category_cols[0]] == '耗材').sum()
                print(f"  ✓ 找到 {consumable_count} 行耗材数据")
            else:
                print(f"  ⚠️  未在 '{category_cols[0]}' 列中找到'耗材'值")
                print(f"  该列的所有唯一值:")
                for val in df[category_cols[0]].unique():
                    print(f"    - {val}")
        else:
            print("⚠️  未找到包含'分类'的列")
            print("  可能的原因:")
            print("  1. 列名不包含'分类'关键字")
            print("  2. 需要手动指定列名")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        print("请提供Excel文件路径作为参数")
        print("用法: python 诊断数据列名.py <Excel文件路径>")
        sys.exit(1)
    
    diagnose_excel_columns(file_path)
