#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义导入示例
演示如何使用智能导入工具处理不同格式的门店数据
"""

import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from 智能导入门店数据 import SmartStoreDataImporter
import pandas as pd


def example_1_basic_import():
    """示例1: 基础导入 - 导入单个文件"""
    print("\n" + "="*60)
    print("示例1: 基础导入")
    print("="*60)
    
    importer = SmartStoreDataImporter(data_dir="门店数据")
    
    # 导入订单数据
    file_path = "门店数据/订单数据-本店.xlsx"
    df = importer.import_file(file_path)
    
    print(f"\n导入结果:")
    print(df.head())


def example_2_batch_import():
    """示例2: 批量导入 - 自动识别所有文件"""
    print("\n" + "="*60)
    print("示例2: 批量导入")
    print("="*60)
    
    importer = SmartStoreDataImporter(data_dir="门店数据")
    
    # 批量导入所有文件
    all_data = importer.import_all()
    
    # 显示摘要
    importer.print_summary()
    
    return all_data


def example_3_custom_processing():
    """示例3: 自定义处理 - 导入后进行业务处理"""
    print("\n" + "="*60)
    print("示例3: 自定义处理")
    print("="*60)
    
    importer = SmartStoreDataImporter(data_dir="门店数据")
    all_data = importer.import_all()
    
    # 如果有订单数据，进行分析
    if '订单数据' in all_data:
        df = all_data['订单数据']
        
        print("\n📊 订单数据分析:")
        
        # 销量统计
        if '商品名称' in df.columns and '销量' in df.columns:
            top_products = df.groupby('商品名称')['销量'].sum().sort_values(ascending=False).head(10)
            print("\n🏆 销量TOP10:")
            for idx, (product, qty) in enumerate(top_products.items(), 1):
                print(f"   {idx}. {product}: {qty:,.0f} 件")
        
        # 时间分析
        if '下单时间' in df.columns:
            df['下单时间'] = pd.to_datetime(df['下单时间'])
            df['日期'] = df['下单时间'].dt.date
            daily_orders = df.groupby('日期').size()
            print(f"\n📅 数据时间范围: {df['下单时间'].min()} ~ {df['下单时间'].max()}")
            print(f"📦 日均订单量: {daily_orders.mean():.0f} 单")


def example_4_data_validation():
    """示例4: 数据验证 - 检查数据质量"""
    print("\n" + "="*60)
    print("示例4: 数据验证")
    print("="*60)
    
    importer = SmartStoreDataImporter(data_dir="门店数据")
    all_data = importer.import_all()
    
    for data_type, df in all_data.items():
        print(f"\n📋 {data_type} 数据质量:")
        print(f"   总行数: {len(df):,}")
        print(f"   总列数: {len(df.columns)}")
        print(f"   缺失值: {df.isnull().sum().sum()}")
        print(f"   重复行: {df.duplicated().sum()}")
        
        # 显示字段信息
        print(f"   字段列表:")
        for col in df.columns:
            null_pct = (df[col].isnull().sum() / len(df)) * 100
            print(f"      - {col}: {df[col].dtype} (缺失率: {null_pct:.1f}%)")


def example_5_merge_data():
    """示例5: 数据合并 - 合并多个数据源"""
    print("\n" + "="*60)
    print("示例5: 数据合并")
    print("="*60)
    
    importer = SmartStoreDataImporter(data_dir="门店数据")
    all_data = importer.import_all()
    
    # 如果同时有订单数据和商品数据，进行合并
    if '订单数据' in all_data and '商品数据' in all_data:
        orders = all_data['订单数据']
        products = all_data['商品数据']
        
        # 按商品名称合并
        if '商品名称' in orders.columns and '商品名称' in products.columns:
            merged = orders.merge(
                products,
                on='商品名称',
                how='left',
                suffixes=('_订单', '_商品')
            )
            
            print(f"\n✅ 数据合并成功!")
            print(f"   订单数据: {len(orders)} 行")
            print(f"   商品数据: {len(products)} 行")
            print(f"   合并结果: {len(merged)} 行")
            print(f"   合并字段: {', '.join(merged.columns.tolist())}")
            
            return merged


def example_6_export_results():
    """示例6: 导出结果 - 保存处理后的数据"""
    print("\n" + "="*60)
    print("示例6: 导出结果")
    print("="*60)
    
    importer = SmartStoreDataImporter(data_dir="门店数据")
    all_data = importer.import_all()
    
    # 保存导入日志
    importer.save_logs("logs/import_logs.json")
    
    # 导出处理后的数据
    output_dir = "导出数据"
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    for data_type, df in all_data.items():
        output_file = f"{output_dir}/{data_type}_处理后.xlsx"
        df.to_excel(output_file, index=False)
        print(f"✅ 已导出: {output_file}")


def main():
    """运行所有示例"""
    print("\n" + "="*80)
    print("🎓 智能导入工具 - 使用示例")
    print("="*80)
    
    examples = [
        ("基础导入", example_1_basic_import),
        ("批量导入", example_2_batch_import),
        ("自定义处理", example_3_custom_processing),
        ("数据验证", example_4_data_validation),
        ("数据合并", example_5_merge_data),
        ("导出结果", example_6_export_results),
    ]
    
    for idx, (name, func) in enumerate(examples, 1):
        try:
            print(f"\n{'='*80}")
            print(f"运行示例 {idx}/{len(examples)}: {name}")
            print(f"{'='*80}")
            func()
        except Exception as e:
            print(f"❌ 示例执行失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ 所有示例运行完成!")
    print("="*80)


if __name__ == "__main__":
    # 可以选择运行单个示例或所有示例
    
    # 运行单个示例
    # example_2_batch_import()
    
    # 或运行所有示例
    main()
