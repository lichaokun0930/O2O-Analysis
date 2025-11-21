#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试：门店下拉列表预加载
"""

print("=" * 60)
print("测试门店选项预加载")
print("=" * 60)

# 测试预加载函数
try:
    from database.data_lifecycle_manager import DataLifecycleManager
    from sqlalchemy import text
    
    print("\n1. 创建DataLifecycleManager...")
    manager = DataLifecycleManager()
    
    print("2. 查询门店列表...")
    query = "SELECT DISTINCT store_name FROM orders ORDER BY store_name"
    results = manager.session.execute(text(query)).fetchall()
    
    print("3. 构造下拉选项...")
    options = [{'label': r[0], 'value': r[0]} for r in results]
    
    manager.close()
    
    print(f"\n✅ 成功！预加载了 {len(options)} 个门店:")
    print("-" * 60)
    for i, opt in enumerate(options, 1):
        print(f"{i}. {opt['label']}")
    print("-" * 60)
    
    print(f"\n选项格式: {options}")
    
except Exception as e:
    print(f"\n❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
