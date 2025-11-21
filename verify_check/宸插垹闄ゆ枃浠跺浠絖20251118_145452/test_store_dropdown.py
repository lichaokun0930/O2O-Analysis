#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试门店下拉列表功能
"""

from database.data_lifecycle_manager import DataLifecycleManager
from sqlalchemy import text

def test_store_dropdown():
    """测试门店下拉列表查询"""
    print("=" * 60)
    print("测试门店下拉列表功能")
    print("=" * 60)
    
    try:
        manager = DataLifecycleManager()
        
        # 查询门店列表
        query = """
        SELECT DISTINCT store_name
        FROM orders
        ORDER BY store_name
        """
        
        print("\n执行查询...")
        results = manager.session.execute(text(query)).fetchall()
        
        # 构造下拉选项
        options = [{'label': r[0], 'value': r[0]} for r in results]
        
        print(f"\n✅ 查询成功！")
        print(f"找到 {len(options)} 个门店:")
        print("-" * 60)
        
        for i, opt in enumerate(options, 1):
            print(f"{i}. {opt['label']}")
        
        print("-" * 60)
        print(f"\nDropdown options 格式:")
        print(options)
        
        manager.close()
        
        return options
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    test_store_dropdown()
