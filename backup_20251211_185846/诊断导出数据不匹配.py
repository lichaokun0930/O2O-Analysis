"""
诊断商品健康分析导出数据不匹配问题

问题描述：
- 祥和路店，选择全部分类
- 看板显示：明星商品 218个
- 导出数据：明星商品 89个

可能原因：
1. 导出函数和看板显示使用了不同的计算逻辑
2. 日期范围参数传递有误
3. 数据筛选条件不一致
"""

import pandas as pd
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入必要的函数
from components.today_must_do.callbacks import (
    get_real_global_data,
    apply_filters_view,
    calculate_enhanced_product_scores,
    calculate_enhanced_product_scores_with_trend,
    get_product_scoring_export_data
)

def diagnose_export_mismatch():
    """诊断导出数据不匹配问题"""
    
    print("=" * 80)
    print("🔍 商品健康分析导出数据不匹配诊断")
    print("=" * 80)
    
    # 1. 获取全局数据
    print("\n📊 步骤1：获取全局数据")
    GLOBAL_DATA = get_real_global_data()
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        print("❌ 无法获取全局数据")
        return
    print(f"✅ 全局数据行数: {len(GLOBAL_DATA)}")
    
    # 2. 筛选祥和路店
    print("\n📊 步骤2：筛选祥和路店")
    selected_stores = ['祥和路店']
    df = apply_filters_view(GLOBAL_DATA, selected_stores=selected_stores)
    print(f"✅ 祥和路店数据行数: {len(df)}")
    
    # 3. 测试不同日期范围的计算结果
    print("\n📊 步骤3：测试不同日期范围的计算结果")
    
    # 测试全部数据（days_range=0）
    print("\n--- 测试1：全部数据（days_range=0）---")
    scores_all = calculate_enhanced_product_scores(df)
    if not scores_all.empty:
        quadrant_counts_all = scores_all['四象限分类'].value_counts()
        print(f"总商品数: {len(scores_all)}")
        print("六象限分布:")
        for quadrant, count in quadrant_counts_all.items():
            print(f"  {quadrant}: {count}个")
        star_count_all = quadrant_counts_all.get('🌟 明星商品', 0)
        print(f"\n🌟 明星商品数量: {star_count_all}")
    
    # 测试15天数据（days_range=15）
    print("\n--- 测试2：15天数据（days_range=15）---")
    scores_15 = calculate_enhanced_product_scores_with_trend(df, days=15)
    if not scores_15.empty:
        quadrant_counts_15 = scores_15['四象限分类'].value_counts()
        print(f"总商品数: {len(scores_15)}")
        print("六象限分布:")
        for quadrant, count in quadrant_counts_15.items():
            print(f"  {quadrant}: {count}个")
        star_count_15 = quadrant_counts_15.get('🌟 明星商品', 0)
        print(f"\n🌟 明星商品数量: {star_count_15}")
    
    # 测试30天数据（days_range=30）
    print("\n--- 测试3：30天数据（days_range=30）---")
    scores_30 = calculate_enhanced_product_scores_with_trend(df, days=30)
    if not scores_30.empty:
        quadrant_counts_30 = scores_30['四象限分类'].value_counts()
        print(f"总商品数: {len(scores_30)}")
        print("六象限分布:")
        for quadrant, count in quadrant_counts_30.items():
            print(f"  {quadrant}: {count}个")
        star_count_30 = quadrant_counts_30.get('🌟 明星商品', 0)
        print(f"\n🌟 明星商品数量: {star_count_30}")
    
    # 4. 对比导出数据
    print("\n📊 步骤4：测试导出数据函数")
    
    # 测试导出（15天）
    print("\n--- 导出数据测试（15天）---")
    export_df_15 = get_product_scoring_export_data(df, days_range=15)
    if not export_df_15.empty:
        export_quadrant_counts = export_df_15['四象限分类'].value_counts()
        print(f"导出数据总行数: {len(export_df_15)}")
        print("六象限分布:")
        for quadrant, count in export_quadrant_counts.items():
            print(f"  {quadrant}: {count}个")
        export_star_count = export_quadrant_counts.get('🌟 明星商品', 0)
        print(f"\n🌟 明星商品数量: {export_star_count}")
    
    # 5. 分析差异
    print("\n" + "=" * 80)
    print("📊 差异分析总结")
    print("=" * 80)
    
    if not scores_all.empty and not scores_15.empty:
        print(f"\n全部数据模式:")
        print(f"  - 总商品数: {len(scores_all)}")
        print(f"  - 明星商品: {star_count_all}个")
        
        print(f"\n15天对比模式:")
        print(f"  - 总商品数: {len(scores_15)}")
        print(f"  - 明星商品: {star_count_15}个")
        
        if not export_df_15.empty:
            print(f"\n导出数据（15天）:")
            print(f"  - 总商品数: {len(export_df_15)}")
            print(f"  - 明星商品: {export_star_count}个")
        
        # 检查是否一致
        if len(scores_15) == len(export_df_15) and star_count_15 == export_star_count:
            print("\n✅ 导出数据与15天对比模式一致")
        else:
            print("\n❌ 导出数据与15天对比模式不一致")
            print(f"   商品数差异: {len(scores_15)} vs {len(export_df_15)}")
            print(f"   明星商品差异: {star_count_15} vs {export_star_count}")
        
        # 检查看板显示的218是哪个模式
        if star_count_all == 218:
            print("\n💡 看板显示的218个明星商品来自【全部数据模式】")
            print("   问题原因：看板使用全部数据，导出使用15天对比数据")
        elif star_count_15 == 218:
            print("\n💡 看板显示的218个明星商品来自【15天对比模式】")
        
        if export_star_count == 89:
            print(f"\n💡 导出的89个明星商品可能是因为：")
            print(f"   1. 使用了不同的日期范围")
            print(f"   2. 数据筛选条件不同")
            print(f"   3. 计算逻辑有差异")
    
    print("\n" + "=" * 80)
    print("🔍 诊断完成")
    print("=" * 80)

if __name__ == '__main__':
    diagnose_export_mismatch()
