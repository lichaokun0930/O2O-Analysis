#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证数据分离方案
检查GLOBAL_FULL_DATA和GLOBAL_DATA是否正确分离
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("="*80)
print("🔍 验证数据分离方案")
print("="*80)

# 测试数据库加载
print("\n【测试1: 数据库加载】")
print("-"*80)

from database.data_source_manager import DataSourceManager

dsm = DataSourceManager()
result = dsm.load_from_database(
    store_name='惠宜选超市（苏州枫瑞路店）',
    split_consumables=True
)

print(f"\n返回类型: {type(result)}")
if isinstance(result, dict):
    print(f"✅ 返回dict结构")
    print(f"   包含键: {list(result.keys())}")
    
    df_full = result['full']
    df_display = result['display']
    
    print(f"\n完整数据(full):")
    print(f"   行数: {len(df_full):,}")
    if '一级分类名' in df_full.columns:
        haocai_count = (df_full['一级分类名'] == '耗材').sum()
        print(f"   耗材数: {haocai_count:,}")
    
    print(f"\n展示数据(display):")
    print(f"   行数: {len(df_display):,}")
    if '一级分类名' in df_display.columns:
        haocai_count = (df_display['一级分类名'] == '耗材').sum()
        print(f"   耗材数: {haocai_count:,}")
        if haocai_count == 0:
            print(f"   ✅ 展示数据不包含耗材")
        else:
            print(f"   ❌ 展示数据仍包含耗材!")
    
    # 检查差异
    diff = len(df_full) - len(df_display)
    print(f"\n差异: {diff:,} 行 (应该等于耗材数)")
    
else:
    print(f"❌ 返回类型错误: {type(result)}")

# 测试利润计算
print("\n\n【测试2: 利润计算】")
print("-"*80)

if isinstance(result, dict):
    df_full = result['full']
    df_display = result['display']
    
    # 过滤美团共橙
    mt_full = df_full[df_full['渠道'] == '美团共橙'] if '渠道' in df_full.columns else df_full
    mt_display = df_display[df_display['渠道'] == '美团共橙'] if '渠道' in df_display.columns else df_display
    
    print(f"\n美团共橙数据:")
    print(f"   完整数据: {len(mt_full):,} 行")
    print(f"   展示数据: {len(mt_display):,} 行")
    
    # 计算利润
    print(f"\n利润计算:")
    full_profit = mt_full['利润额'].sum() if '利润额' in mt_full.columns else 0
    display_profit = mt_display['利润额'].sum() if '利润额' in mt_display.columns else 0
    
    print(f"   完整数据利润额: ¥{full_profit:,.2f}")
    print(f"   展示数据利润额: ¥{display_profit:,.2f}")
    print(f"   差异: ¥{full_profit - display_profit:,.2f}")
    
    # 使用calculate_order_metrics
    try:
        from 智能门店看板_Dash版 import calculate_order_metrics
        
        print(f"\n使用calculate_order_metrics计算:")
        
        # 完整数据计算
        order_agg_full = calculate_order_metrics(mt_full, calc_mode='all_no_fallback')
        profit_full = order_agg_full['订单实际利润'].sum()
        print(f"   完整数据(含耗材): ¥{profit_full:,.2f}")
        
        # 展示数据计算
        order_agg_display = calculate_order_metrics(mt_display, calc_mode='all_no_fallback')
        profit_display = order_agg_display['订单实际利润'].sum()
        print(f"   展示数据(不含耗材): ¥{profit_display:,.2f}")
        
        print(f"\n📊 最终验证:")
        if abs(profit_full - 652.06) < 10:
            print(f"   ✅ 完整数据利润正确: {profit_full:,.2f} ≈ 652.06")
        else:
            print(f"   ⚠️ 完整数据利润偏差: {profit_full:,.2f} (预期: 652.06)")
        
        if profit_display > profit_full:
            print(f"   ❌ 展示数据利润应该更小(剔除了耗材成本)")
        else:
            print(f"   ✅ 数据逻辑正确")
            
    except Exception as e:
        print(f"   ❌ calculate_order_metrics测试失败: {e}")

print("\n" + "="*80)
print("✅ 验证完成")
print("="*80)
