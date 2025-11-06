#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试诊断引擎输出"""

import pandas as pd
from 问题诊断引擎 import ProblemDiagnosticEngine
from 真实数据处理器 import RealDataProcessor

# 加载数据
from 智能门店看板_Dash版 import load_real_business_data

data = load_real_business_data()

print("="*80)
print("🔍 测试诊断引擎输出")
print("="*80)

# 初始化诊断引擎
engine = ProblemDiagnosticEngine(data)
print(f"\n✅ 诊断引擎初始化完成，数据量: {len(data)} 行")
print(f"📋 原始数据字段: {list(data.columns)[:20]}")
print(f"\n场景字段存在: {'场景' in data.columns}")
print(f"时段字段存在: {'时段' in data.columns}")

if '场景' in data.columns:
    print(f"场景唯一值: {data['场景'].unique().tolist()}")
if '时段' in data.columns:
    print(f"时段唯一值: {data['时段'].unique().tolist()}")

# 执行诊断
print("\n" + "="*80)
print("🔬 执行销量下滑诊断...")
print("="*80)

try:
    result = engine.diagnose_sales_decline(
        time_period='week',
        threshold=-20,
        scene_filter=None,
        time_slot_filter=None
    )
    
    print(f"\n✅ 诊断完成！")
    print(f"📊 诊断结果行数: {len(result)}")
    
    if not result.empty:
        print(f"\n📋 诊断结果字段 ({len(result.columns)} 个):")
        for i, col in enumerate(result.columns, 1):
            print(f"   {i:2d}. {col}")
        
        print(f"\n🔍 关键字段检查:")
        print(f"   - 场景字段存在: {'场景' in result.columns}")
        print(f"   - 时段字段存在: {'时段' in result.columns}")
        
        if '场景' in result.columns:
            print(f"\n   场景字段示例值:")
            print(result['场景'].head(10).tolist())
        else:
            print(f"\n   ❌ 场景字段缺失！")
        
        if '时段' in result.columns:
            print(f"\n   时段字段示例值:")
            print(result['时段'].head(10).tolist())
        else:
            print(f"\n   ❌ 时段字段缺失！")
        
        # 显示前5行数据
        print(f"\n📄 诊断结果前5行:")
        print(result.head())
    else:
        print("\n⚠️ 诊断结果为空")
        
except Exception as e:
    print(f"\n❌ 诊断失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("测试完成")
print("="*80)
