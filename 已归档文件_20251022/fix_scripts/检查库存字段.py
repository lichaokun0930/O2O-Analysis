#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查订单数据中的库存字段
验证是否可以用库存判定售罄
"""

import pandas as pd
from pathlib import Path

def check_inventory_fields():
    """检查数据中的库存字段"""
    
    # 查找数据文件
    data_dir = Path("门店数据")
    excel_files = list(data_dir.glob("*.xlsx"))
    
    if not excel_files:
        print("❌ 未找到数据文件")
        return
    
    data_file = excel_files[0]
    print(f"📂 读取数据文件: {data_file.name}\n")
    
    # 读取数据
    df = pd.read_excel(data_file)
    
    print("=" * 80)
    print("📊 数据列名检查")
    print("=" * 80)
    print(f"总列数: {len(df.columns)}\n")
    
    # 显示所有列名
    print("所有列名:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    print("\n" + "=" * 80)
    print("🔍 查找库存相关字段")
    print("=" * 80)
    
    # 查找库存字段
    inventory_cols = [col for col in df.columns if '库存' in col]
    
    if inventory_cols:
        print(f"✅ 找到 {len(inventory_cols)} 个库存字段:\n")
        for col in inventory_cols:
            print(f"  📦 {col}")
            
            # 显示该字段的统计信息
            print(f"     - 非空值数量: {df[col].count()}")
            print(f"     - 空值数量: {df[col].isna().sum()}")
            print(f"     - 最小值: {df[col].min()}")
            print(f"     - 最大值: {df[col].max()}")
            print(f"     - 平均值: {df[col].mean():.2f}")
            
            # 显示示例数据
            print(f"     - 示例值: {df[col].dropna().head(5).tolist()}")
            print()
        
        print("=" * 80)
        print("📈 库存数据示例")
        print("=" * 80)
        
        # 显示包含库存字段的示例数据
        display_cols = ['商品名称', '日期'] + inventory_cols
        # 确保这些列都存在
        display_cols = [col for col in display_cols if col in df.columns]
        
        print(df[display_cols].head(10).to_string())
        
        print("\n" + "=" * 80)
        print("🔬 库存为0的商品示例")
        print("=" * 80)
        
        # 查找库存为0的商品
        for col in inventory_cols:
            zero_stock = df[df[col] == 0]
            if not zero_stock.empty:
                print(f"\n{col} = 0 的商品数量: {len(zero_stock)}")
                print(zero_stock[display_cols].head(5).to_string())
        
        print("\n" + "=" * 80)
        print("✅ 结论")
        print("=" * 80)
        print("数据中包含库存字段，可以使用库存判定售罄！")
        print("\n建议修改售罄判定逻辑:")
        print("  ❌ 旧逻辑: if 当前销量 == 0 and 之前销量 > 0")
        print("  ✅ 新逻辑: if 当前库存 == 0 and 之前库存 > 0")
        
    else:
        print("❌ 未找到库存字段\n")
        print("数据中缺少库存字段，无法准确判定售罄")
        print("\n可能的原因:")
        print("  1. 数据源本身不包含库存信息")
        print("  2. 库存字段使用了其他名称")
        print("\n建议:")
        print("  1. 检查数据源是否可以导出库存字段")
        print("  2. 如果无法获取库存数据，需要明确说明当前'售罄'判定基于销量，非真实库存")

if __name__ == "__main__":
    check_inventory_fields()
