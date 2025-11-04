#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Tab 4.2客单价归因功能
"""

import sys
from pathlib import Path
import pandas as pd

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from 问题诊断引擎 import ProblemDiagnosticEngine

# 加载数据
def load_data():
    candidate_dirs = [
        APP_DIR / "实际数据",
        APP_DIR / "门店数据",
        APP_DIR.parent / "测算模型" / "门店数据" / "比价看板模块",
    ]
    
    for data_dir in candidate_dirs:
        if data_dir.exists():
            excel_files = sorted([f for f in data_dir.glob("*.xlsx") if not f.name.startswith("~$")])
            if excel_files:
                print(f"📂 加载数据: {excel_files[0].name}")
                return pd.read_excel(excel_files[0])
    
    return None

print("=" * 60)
print("🧪 Tab 4.2 客单价归因功能测试")
print("=" * 60)

# 1. 加载数据
print("\n✅ 步骤1: 加载数据")
df = load_data()
if df is None:
    print("❌ 数据加载失败")
    sys.exit(1)
print(f"   数据行数: {len(df)}")

# 2. 初始化诊断引擎
print("\n✅ 步骤2: 初始化诊断引擎")
engine = ProblemDiagnosticEngine(df)
print(f"   引擎类型: {type(engine).__name__}")

# 3. 检查方法是否存在
print("\n✅ 步骤3: 检查必要方法")
methods = [
    'get_available_price_periods',
    'diagnose_customer_price_decline',
    'diagnose_customer_price_decline_by_sheets'
]
for method in methods:
    has_method = hasattr(engine, method)
    status = "✅" if has_method else "❌"
    print(f"   {status} {method}: {has_method}")

# 4. 测试获取周期列表
print("\n✅ 步骤4: 测试获取周期列表")
try:
    periods = engine.get_available_price_periods(time_period='week')
    print(f"   可用周期数: {len(periods)}")
    if len(periods) > 0:
        print(f"   示例周期: {periods[0]}")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

# 5. 测试客单价归因分析（批量模式）
print("\n✅ 步骤5: 测试客单价归因分析（批量模式）")
try:
    result = engine.diagnose_customer_price_decline(
        time_period='week',
        threshold=-5.0,
        current_period_index=None,
        compare_period_index=None
    )
    print(f"   结果行数: {len(result)}")
    if len(result) > 0:
        print(f"   结果字段: {list(result.columns)[:10]}")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

# 6. 测试客单价归因分析（分Sheet）
print("\n✅ 步骤6: 测试客单价归因分析（分Sheet）")
try:
    sheets_data = engine.diagnose_customer_price_decline_by_sheets(
        time_period='week',
        threshold=-5.0,
        current_period_index=None,
        compare_period_index=None
    )
    print(f"   Sheet数量: {len(sheets_data)}")
    for sheet_name, df_sheet in sheets_data.items():
        print(f"   - {sheet_name}: {len(df_sheet)} 行")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

# 7. 测试精准对比模式
print("\n✅ 步骤7: 测试精准对比模式")
try:
    if len(periods) >= 2:
        result = engine.diagnose_customer_price_decline(
            time_period='week',
            threshold=-5.0,
            current_period_index=0,
            compare_period_index=1
        )
        print(f"   结果行数: {len(result)}")
    else:
        print(f"   ⚠️ 周期不足（需要≥2个，实际{len(periods)}个）")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("🎉 测试完成！")
print("=" * 60)
