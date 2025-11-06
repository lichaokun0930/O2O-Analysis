#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理器整合验证脚本
验证真实数据处理器与问题诊断引擎的字段匹配
"""

import pandas as pd
import sys
from pathlib import Path

# 添加路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

print("=" * 80)
print("📋 数据处理器整合验证")
print("=" * 80)

# 步骤1: 测试数据处理器导入
print("\n【步骤1】测试模块导入...")
try:
    from 真实数据处理器 import RealDataProcessor
    print("✅ 真实数据处理器导入成功")
except ImportError as e:
    print(f"❌ 真实数据处理器导入失败: {e}")
    sys.exit(1)

try:
    from 问题诊断引擎 import ProblemDiagnosticEngine
    print("✅ 问题诊断引擎导入成功")
except ImportError as e:
    print(f"❌ 问题诊断引擎导入失败: {e}")
    sys.exit(1)

# 步骤2: 查找数据文件
print("\n【步骤2】查找数据文件...")
candidate_dirs = [
    APP_DIR / "实际数据",
    APP_DIR.parent / "实际数据",
    APP_DIR / "门店数据",
    APP_DIR / "门店数据" / "比价看板模块",
]

data_file = None
for data_dir in candidate_dirs:
    if data_dir.exists():
        excel_files = sorted([f for f in data_dir.glob("*.xlsx") if not f.name.startswith("~$")])
        if excel_files:
            data_file = excel_files[0]
            print(f"✅ 找到数据文件: {data_file}")
            break

if not data_file:
    print("⚠️ 未找到真实数据文件，使用测试数据")
    # 创建测试数据
    df = pd.DataFrame({
        '商品名称': ['可口可乐', '雪碧', '芬达'],
        '售价': [3.5, 3.0, 3.2],
        '原价': [3.0, 2.5, 2.7],
        '月售': [1500, 1200, 800],
        '美团一级分类': ['饮料', '饮料', '饮料'],
        '美团三级分类': ['碳酸饮料', '碳酸饮料', '碳酸饮料'],
        '订单ID': ['ORD001', 'ORD001', 'ORD002'],
        '日期': pd.date_range('2025-10-01', periods=3),
        '物流配送费': [5, 5, 6],
        '平台佣金': [0.5, 0.4, 0.4]
    })
    print(f"📊 测试数据: {len(df)} 行")
else:
    # 加载真实数据
    print("\n【步骤3】加载真实数据...")
    try:
        df = pd.read_excel(data_file, sheet_name=0)
        print(f"✅ 数据加载成功: {len(df)} 行 × {len(df.columns)} 列")
        print(f"📋 原始字段名（前15个）:")
        for i, col in enumerate(df.columns[:15], 1):
            print(f"   {i:2d}. {col}")
        if len(df.columns) > 15:
            print(f"   ... (还有 {len(df.columns) - 15} 个字段)")
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        sys.exit(1)

# 步骤4: 数据标准化
print("\n【步骤4】执行数据标准化...")
try:
    processor = RealDataProcessor()
    df_standardized = processor.standardize_sales_data(df)
    print(f"✅ 标准化完成: {len(df_standardized)} 行 × {len(df_standardized.columns)} 列")
    print(f"📋 标准化字段名（前15个）:")
    for i, col in enumerate(df_standardized.columns[:15], 1):
        print(f"   {i:2d}. {col}")
    if len(df_standardized.columns) > 15:
        print(f"   ... (还有 {len(df_standardized.columns) - 15} 个字段)")
except Exception as e:
    print(f"❌ 标准化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 步骤5: 字段匹配检查
print("\n【步骤5】检查诊断引擎所需字段...")
required_fields = {
    '必需字段': ['日期', '订单ID', '商品实售价', '商品名称'],
    '毛利计算': ['商品采购成本'],
    '配送费分析': ['物流配送费'],
    '分类分析': ['一级分类名', '三级分类名'],
    '时段分析': ['时段', '场景'],
    '角色分析': ['商品角色']
}

field_check_results = {}
for category, fields in required_fields.items():
    missing = [f for f in fields if f not in df_standardized.columns]
    existing = [f for f in fields if f in df_standardized.columns]
    
    field_check_results[category] = {
        'existing': existing,
        'missing': missing,
        'status': '✅' if len(existing) == len(fields) else '⚠️' if existing else '❌'
    }
    
    print(f"\n{field_check_results[category]['status']} {category}:")
    if existing:
        print(f"   ✅ 存在: {', '.join(existing)}")
    if missing:
        print(f"   ❌ 缺失: {', '.join(missing)}")

# 步骤6: 测试诊断引擎初始化
print("\n【步骤6】测试诊断引擎初始化...")
try:
    diagnostic_engine = ProblemDiagnosticEngine(df_standardized)
    print("✅ 诊断引擎初始化成功")
    
    # 检查引擎内部数据
    print(f"📊 引擎数据形状: {diagnostic_engine.df.shape}")
    
    # 检查衍生字段
    derived_fields = ['单品毛利', '单品毛利率', '配送费占比']
    existing_derived = [f for f in derived_fields if f in diagnostic_engine.df.columns]
    missing_derived = [f for f in derived_fields if f not in diagnostic_engine.df.columns]
    
    if existing_derived:
        print(f"✅ 衍生字段存在: {', '.join(existing_derived)}")
    if missing_derived:
        print(f"⚠️ 衍生字段缺失: {', '.join(missing_derived)}")
    
except Exception as e:
    print(f"❌ 诊断引擎初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 步骤7: 测试诊断功能
print("\n【步骤7】测试诊断功能...")
test_functions = [
    ('获取可用周期', lambda: diagnostic_engine.get_available_periods('week')),
    ('负毛利诊断', lambda: diagnostic_engine.diagnose_negative_margin_products()),
]

for func_name, func in test_functions:
    try:
        result = func()
        if isinstance(result, list):
            print(f"✅ {func_name}: 返回 {len(result)} 条记录")
        elif isinstance(result, pd.DataFrame):
            print(f"✅ {func_name}: 返回 {len(result)} 行数据")
        else:
            print(f"✅ {func_name}: 返回 {type(result).__name__}")
    except Exception as e:
        print(f"❌ {func_name} 失败: {e}")

# 步骤8: 数据类型检查
print("\n【步骤8】数据类型检查...")
type_checks = {
    '商品实售价': 'numeric',
    '商品采购成本': 'numeric',
    '日期': 'datetime',
    '月售': 'numeric'
}

for field, expected_type in type_checks.items():
    if field in df_standardized.columns:
        actual_type = df_standardized[field].dtype
        is_numeric = pd.api.types.is_numeric_dtype(actual_type)
        is_datetime = pd.api.types.is_datetime64_any_dtype(actual_type)
        
        if expected_type == 'numeric' and is_numeric:
            print(f"✅ {field}: {actual_type} (数值类型)")
        elif expected_type == 'datetime' and is_datetime:
            print(f"✅ {field}: {actual_type} (日期类型)")
        else:
            print(f"⚠️ {field}: {actual_type} (期望: {expected_type})")
    else:
        print(f"⚠️ {field}: 字段不存在")

# 总结
print("\n" + "=" * 80)
print("📊 验证总结")
print("=" * 80)

total_categories = len(field_check_results)
passed_categories = sum(1 for r in field_check_results.values() if r['status'] == '✅')
partial_categories = sum(1 for r in field_check_results.values() if r['status'] == '⚠️')
failed_categories = sum(1 for r in field_check_results.values() if r['status'] == '❌')

print(f"\n字段匹配结果:")
print(f"  ✅ 完全匹配: {passed_categories}/{total_categories}")
print(f"  ⚠️ 部分匹配: {partial_categories}/{total_categories}")
print(f"  ❌ 完全缺失: {failed_categories}/{total_categories}")

if passed_categories == total_categories:
    print("\n🎉 整合验证通过！所有字段完全匹配，可以正常使用诊断引擎。")
elif passed_categories + partial_categories == total_categories:
    print("\n⚠️ 整合基本可用，但部分功能可能受限。")
    print("建议: 补充缺失字段以启用完整功能。")
else:
    print("\n❌ 整合存在问题，需要补充必需字段。")
    print("请检查数据文件是否包含所需字段。")

print("\n" + "=" * 80)
print("验证完成！")
print("=" * 80)
