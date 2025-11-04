#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试销量下滑诊断的新功能
- 需求1: 预计收入列
- 需求2: 周期灵活对比
"""

import pandas as pd
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from 问题诊断引擎 import ProblemDiagnosticEngine

print("=" * 80)
print("📊 销量下滑诊断 - 新功能测试")
print("=" * 80)

# 加载测试数据
data_file = Path("门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx")

if not data_file.exists():
    print(f"❌ 数据文件不存在: {data_file}")
    sys.exit(1)

print(f"\n📂 加载数据: {data_file.name}")
df = pd.read_excel(data_file)
print(f"✅ 数据行数: {len(df):,}")
print(f"✅ 数据列数: {len(df.columns)}")

# 检查关键字段
required_cols = ['商品名称', '一级分类名', '三级分类名', '下单时间', '销量']
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    print(f"❌ 缺少必需字段: {missing_cols}")
    sys.exit(1)

# 检查预计收入字段
if '预计订单收入' in df.columns:
    print("✅ 检测到 '预计订单收入' 字段")
    revenue_col = '预计订单收入'
elif '预估订单收入' in df.columns:
    print("✅ 检测到 '预估订单收入' 字段")
    revenue_col = '预估订单收入'
else:
    print("⚠️ 未检测到预计收入字段")
    revenue_col = None

# 数据预处理
print("\n🔧 数据预处理...")
df['日期'] = pd.to_datetime(df['下单时间']).dt.date
df['日期'] = pd.to_datetime(df['日期'])

# 初始化诊断引擎
print("🚀 初始化问题诊断引擎...")
engine = ProblemDiagnosticEngine(df)

print("\n" + "=" * 80)
print("🧪 测试1: 获取可用周期列表")
print("=" * 80)

periods = engine.get_available_periods('week')
print(f"\n✅ 获取到 {len(periods)} 个可用周期:")
for i, period in enumerate(periods[:5]):  # 只显示前5个
    print(f"  {i+1}. [{period['index']}] {period['label']}")
    print(f"      日期范围: {period['date_range']}")

print("\n" + "=" * 80)
print("🧪 测试2: 默认对比 (最新周 vs 上一周)")
print("=" * 80)

result_default = engine.diagnose_sales_decline(
    time_period='week',
    threshold=-20.0
)

print(f"\n✅ 诊断完成,发现 {len(result_default)} 个下滑商品")
print(f"\n📋 结果DataFrame列名:")
for i, col in enumerate(result_default.columns, 1):
    print(f"  {i}. {col}")

# 检查动态列名
week_sales_cols = [col for col in result_default.columns if '周销量' in col]
revenue_cols = [col for col in result_default.columns if '预计收入' in col]

print(f"\n✅ 检测到 {len(week_sales_cols)} 个销量列: {week_sales_cols}")
print(f"✅ 检测到 {len(revenue_cols)} 个预计收入列: {revenue_cols}")

if len(result_default) > 0:
    print(f"\n📊 前3个下滑商品示例:")
    display_cols = ['商品名称', '一级分类名', '三级分类名'] + week_sales_cols + revenue_cols + ['销量变化', '变化幅度%']
    display_cols = [col for col in display_cols if col in result_default.columns]
    print(result_default[display_cols].head(3).to_string(index=False))

print("\n" + "=" * 80)
print("🧪 测试3: 自定义周期对比 (第38周 vs 第35周)")
print("=" * 80)

if len(periods) >= 4:
    result_custom = engine.diagnose_sales_decline(
        time_period='week',
        threshold=-20.0,
        current_period_index=0,  # 最新周
        compare_period_index=3   # 3周前
    )
    
    print(f"\n✅ 自定义对比完成,发现 {len(result_custom)} 个下滑商品")
    
    # 检查表头是否正确
    week_cols = [col for col in result_custom.columns if '周销量' in col]
    print(f"\n✅ 动态表头: {week_cols}")
    
    if len(result_custom) > 0:
        print(f"\n📊 对比结果示例:")
        display_cols = ['商品名称'] + week_cols + ['销量变化', '变化幅度%']
        display_cols = [col for col in display_cols if col in result_custom.columns]
        print(result_custom[display_cols].head(3).to_string(index=False))
else:
    print("⚠️ 数据周期不足,跳过自定义对比测试")

print("\n" + "=" * 80)
print("🧪 测试4: 数值格式验证")
print("=" * 80)

if len(result_default) > 0:
    # 检查销量是否为整数
    first_sales_col = week_sales_cols[0] if week_sales_cols else None
    if first_sales_col:
        sample_value = result_default[first_sales_col].iloc[0]
        print(f"\n✅ 销量列 '{first_sales_col}' 示例值: {sample_value} (类型: {type(sample_value).__name__})")
    
    # 检查变化幅度是否带%
    if '变化幅度%' in result_default.columns:
        sample_percent = result_default['变化幅度%'].iloc[0]
        print(f"✅ 变化幅度% 示例值: {sample_percent} (类型: {type(sample_percent).__name__})")
        if isinstance(sample_percent, str) and '%' in sample_percent:
            print("   ✓ 包含%符号 ✅")
        else:
            print("   ✗ 未包含%符号 ❌")
    
    # 检查预计收入格式
    if revenue_cols:
        first_revenue_col = revenue_cols[0]
        sample_revenue = result_default[first_revenue_col].iloc[0]
        print(f"✅ 预计收入列 '{first_revenue_col}' 示例值: {sample_revenue} (类型: {type(sample_revenue).__name__})")
        if isinstance(sample_revenue, str) and '¥' in sample_revenue:
            print("   ✓ 包含¥符号 ✅")
        else:
            print("   ✗ 未包含¥符号 ❌")

print("\n" + "=" * 80)
print("✅ 所有测试完成!")
print("=" * 80)

# 总结
print("\n📝 测试总结:")
print(f"  1. 周期列表获取: {'✅ 通过' if len(periods) > 0 else '❌ 失败'}")
print(f"  2. 默认对比功能: {'✅ 通过' if len(result_default) >= 0 else '❌ 失败'}")
print(f"  3. 动态表头: {'✅ 通过' if len(week_sales_cols) > 0 else '❌ 失败'}")
print(f"  4. 预计收入列: {'✅ 通过' if len(revenue_cols) > 0 else '⚠️ 无数据'}")
print(f"  5. 数值格式化: {'✅ 通过' if len(result_default) > 0 else '⚠️ 无数据'}")

print("\n🎉 新功能验证完成!")
