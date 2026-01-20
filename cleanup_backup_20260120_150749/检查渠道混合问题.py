"""
检查同一商品在不同渠道的价格差异

验证店内码52183在不同渠道的表现
"""

import pandas as pd
import numpy as np

# 加载原始数据
data_file = r"d:\Python\订单数据看板\O2O-Analysis\实际数据\2025-11-04 00_00_00至2025-12-03 23_59_59订单明细数据导出汇总.xlsx"
df = pd.read_excel(data_file)

print("=" * 120)
print("检查店内码52183在不同渠道的价格差异")
print("=" * 120)

# 筛选店内码52183的数据
target_code = 52183
product_data = df[df['店内码'] == target_code].copy()

if product_data.empty:
    print(f"\n❌ 未找到店内码为 {target_code} 的商品")
else:
    print(f"\n✅ 找到店内码 {target_code} 的数据，共 {len(product_data)} 条记录")
    print(f"\n商品名称: {product_data['商品名称'].iloc[0]}")
    print(f"一级分类: {product_data['一级分类名'].iloc[0]}")
    
    # 按渠道分组统计
    if '渠道' in product_data.columns:
        agg_dict = {
            '销量': 'sum',
            '订单ID': 'nunique',
            '商品原价': 'mean',
            '商品实售价': 'mean',
            '实收价格': 'mean',
            '成本': 'mean',
            '利润额': 'sum'
        }
        
        # 只有字段存在时才添加聚合
        if '订单总收入' in product_data.columns:
            agg_dict['订单总收入'] = 'sum'
        
        channel_stats = product_data.groupby('渠道').agg(agg_dict).reset_index()
        
        # 计算聚合后的销售额（如果没有订单总收入字段）
        if '订单总收入' not in product_data.columns or channel_stats['订单总收入'].sum() == 0:
            channel_stats['销售额'] = channel_stats['实收价格'] * channel_stats['销量']
        else:
            channel_stats['销售额'] = channel_stats['订单总收入']
        
        # 计算利润率
        channel_stats['综合利润率'] = (channel_stats['利润额'] / channel_stats['销售额'] * 100).fillna(0)
        channel_stats['定价利润率'] = ((channel_stats['商品原价'] - channel_stats['成本']) / channel_stats['商品原价'] * 100).fillna(0)
        
        print("\n" + "=" * 120)
        print("按渠道分组统计")
        print("=" * 120)
        print(channel_stats.to_string(index=False))
        
        # 计算混合后的数据（不分渠道）
        print("\n" + "=" * 120)
        print("混合统计（不区分渠道）")
        print("=" * 120)
        
        total_stats = {
            '销量': product_data['销量'].sum(),
            '订单数': product_data['订单ID'].nunique(),
            '商品原价': product_data['商品原价'].mean(),
            '商品实售价': product_data['商品实售价'].mean(),
            '实收价格': product_data['实收价格'].mean(),
            '成本': product_data['成本'].mean(),
            '利润额': product_data['利润额'].sum(),
        }
        
        # 计算销售额
        if '订单总收入' in product_data.columns:
            total_stats['销售额'] = product_data['订单总收入'].sum()
        else:
            total_stats['销售额'] = total_stats['实收价格'] * total_stats['销量']
        
        # 计算利润率
        total_stats['综合利润率'] = (total_stats['利润额'] / total_stats['销售额'] * 100) if total_stats['销售额'] > 0 else 0
        total_stats['定价利润率'] = ((total_stats['商品原价'] - total_stats['成本']) / total_stats['商品原价'] * 100) if total_stats['商品原价'] > 0 else 0
        
        print("\n混合后的统计数据:")
        for key, value in total_stats.items():
            if key in ['商品原价', '商品实售价', '实收价格', '成本', '利润额', '销售额']:
                print(f"  {key:<15} ¥{value:>10.2f}")
            elif key in ['综合利润率', '定价利润率']:
                print(f"  {key:<15} {value:>10.2f}%")
            else:
                print(f"  {key:<15} {value:>10}")
        
        # 对比分析
        print("\n" + "=" * 120)
        print("⚠️ 问题分析")
        print("=" * 120)
        
        if len(channel_stats) > 1:
            print("\n🔍 发现该商品在多个渠道销售，价格存在差异：")
            for idx, row in channel_stats.iterrows():
                print(f"\n  {row['渠道']}:")
                print(f"    商品原价: ¥{row['商品原价']:.2f}")
                print(f"    实收价格: ¥{row['实收价格']:.2f}")
                print(f"    成本: ¥{row['成本']:.2f}")
                print(f"    定价利润率: {row['定价利润率']:.2f}%")
                print(f"    综合利润率: {row['综合利润率']:.2f}%")
            
            print("\n❌ 问题：如果不区分渠道聚合，会导致：")
            print(f"    1. 商品原价被平均为 ¥{total_stats['商品原价']:.2f}（实际各渠道不同）")
            print(f"    2. 定价利润率计算错误：{total_stats['定价利润率']:.2f}%（基于平均原价）")
            print(f"    3. 无法区分各渠道的真实利润表现")
            
            print("\n✅ 建议解决方案：")
            print("    在 calculate_enhanced_product_scores 函数中，group_cols 应包含 '渠道' 字段")
            print("    group_cols = ['店内码', '商品名称', '渠道', '一级分类名']")
        else:
            print("\n✅ 该商品仅在单一渠道销售，不存在混合问题")
    else:
        print("\n❌ 数据中没有'渠道'字段")

print("\n" + "=" * 120)
