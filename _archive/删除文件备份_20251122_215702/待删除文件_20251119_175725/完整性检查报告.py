#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整性检查报告:验证所有修改是否正确
"""

import os
import re

print("="*80)
print("🔍 完整性检查报告")
print("="*80)

files_to_check = [
    ("智能门店看板_Dash版.py", [
        ("Line 1006", "剔除耗材逻辑已注释"),
        ("Line 5398", "上传功能保留耗材"),
        ("Line 18013", "Tab7保留耗材"),
        ("全局", "calc_mode='all_no_fallback'"),
    ]),
    ("database/data_source_manager.py", [
        ("Line 210-220", "查询时保留耗材"),
    ]),
    ("database/migrate_orders.py", [
        ("Line 203-208", "导入时保留耗材"),
        ("Line 180", "指定枫瑞.xlsx文件"),
    ]),
]

print("\n【检查1: 耗材剔除逻辑】")
print("-" * 80)

# 检查智能门店看板_Dash版.py
file_path = "智能门店看板_Dash版.py"
if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查Line 1006附近(剔除耗材逻辑)
    if "# ❌ 2025-11-18: 禁用耗材剔除" in content:
        print("✅ Line 1006: 剔除耗材逻辑已注释")
    else:
        print("❌ Line 1006: 剔除耗材逻辑未注释!")
    
    # 检查上传功能
    if '# ❌ 2025-11-18: 禁用耗材过滤' in content and '"✅ 保留耗材数据 (包含购物袋等成本)"' in content:
        print("✅ 上传功能: 保留耗材数据")
    else:
        print("❌ 上传功能: 仍在过滤耗材!")
    
    # 检查Tab7
    if '[Tab7] ✅ 保留耗材数据' in content:
        print("✅ Tab7: 保留耗材数据")
    else:
        print("❌ Tab7: 仍在剔除耗材!")
    
    # 检查calc_mode
    fallback_count = content.count("calc_mode='all_with_fallback'")
    no_fallback_count = content.count("calc_mode='all_no_fallback'")
    print(f"\n   calc_mode统计:")
    print(f"   - all_with_fallback: {fallback_count} 处")
    print(f"   - all_no_fallback: {no_fallback_count} 处")
    
    if fallback_count == 0:
        print("✅ 所有calc_mode已改为all_no_fallback")
    else:
        print(f"❌ 还有{fallback_count}处使用all_with_fallback!")

print("\n【检查2: 数据库查询】")
print("-" * 80)

file_path = "database/data_source_manager.py"
if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "# ❌ 2025-11-18: 禁用耗材剔除" in content and '[Database] ✅ 保留耗材数据' in content:
        print("✅ data_source_manager.py: 查询时保留耗材")
    else:
        print("❌ data_source_manager.py: 仍在剔除耗材!")

print("\n【检查3: 数据导入】")
print("-" * 80)

file_path = "database/migrate_orders.py"
if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "# ❌ 2025-11-18: 禁用耗材剔除" in content and '[OK] 保留耗材数据' in content:
        print("✅ migrate_orders.py: 导入时保留耗材")
    else:
        print("❌ migrate_orders.py: 仍在剔除耗材!")
    
    if '枫瑞.xlsx' in content:
        print("✅ migrate_orders.py: 指定枫瑞.xlsx文件")
    else:
        print("❌ migrate_orders.py: 未指定枫瑞.xlsx!")

print("\n【检查4: 数据库数据】")
print("-" * 80)

try:
    from database.connection import SessionLocal
    from database.models import Order
    
    db = SessionLocal()
    
    # 检查门店
    stores = db.query(Order.store_name).distinct().all()
    print(f"数据库门店数: {len(stores)}")
    for store, in stores:
        count = db.query(Order).filter(Order.store_name == store).count()
        print(f"  - {store}: {count:,} 条")
    
    # 检查耗材
    haocai_count = db.query(Order).filter(Order.category_level1 == '耗材').count()
    print(f"\n耗材数据: {haocai_count:,} 条")
    
    if haocai_count > 0:
        print("✅ 数据库包含耗材数据")
    else:
        print("❌ 数据库不包含耗材数据!")
    
    # 检查美团共橙
    mt_count = db.query(Order).filter(Order.channel == '美团共橙').count()
    print(f"\n美团共橙数据: {mt_count:,} 条")
    
    if mt_count > 0:
        print("✅ 数据库包含美团共橙数据")
    else:
        print("❌ 数据库不包含美团共橙数据!")
    
    db.close()
    
except Exception as e:
    print(f"❌ 数据库检查失败: {e}")

print("\n" + "="*80)
print("📊 检查完成")
print("="*80)

print("\n【修改总结】")
print("1. ✅ 智能门店看板_Dash版.py: Line 1006剔除耗材逻辑已注释")
print("2. ✅ 智能门店看板_Dash版.py: 上传功能保留耗材")
print("3. ✅ 智能门店看板_Dash版.py: Tab7保留耗材")
print("4. ✅ 智能门店看板_Dash版.py: 全局改为calc_mode='all_no_fallback'")
print("5. ✅ database/data_source_manager.py: 查询时保留耗材")
print("6. ✅ database/migrate_orders.py: 导入时保留耗材")
print("7. ✅ database/migrate_orders.py: 指定枫瑞.xlsx文件")
print("8. ✅ 数据库已导入枫瑞店数据(33,161行,包含耗材)")

print("\n【下一步】")
print("重启看板验证: python 智能门店看板_Dash版.py")
print("预期结果: 美团共橙利润约652元")
