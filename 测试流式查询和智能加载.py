#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试流式查询和智能加载功能
验证千万级数据处理能力
"""
import sys
import io
from datetime import datetime, timedelta

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("="*70)
print("  测试流式查询和智能加载")
print("="*70)
print()

from database.data_source_manager import DataSourceManager

manager = DataSourceManager()

# 测试1: 智能加载（小数据量）
print("📊 [1/3] 测试智能加载 - 小数据量（最近7天）...")
try:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    result = manager.load_from_database_smart(
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"   ✅ 加载成功")
    print(f"   策略: {result.get('strategy')}")
    print(f"   预估数量: {result.get('estimated_count', 0):,}")
    print(f"   实际数量: {len(result['full']):,}")
    
except Exception as e:
    print(f"   ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试2: 流式加载（中等数据量）
print("📊 [2/3] 测试流式加载 - 中等数据量（最近30天）...")
try:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    result = manager.load_from_database_streaming(
        start_date=start_date,
        end_date=end_date,
        batch_size=5000,
        max_rows=50000
    )
    
    print(f"   ✅ 加载成功")
    print(f"   数量: {len(result['full']):,}")
    
except Exception as e:
    print(f"   ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试3: 智能加载（大数据量）
print("📊 [3/3] 测试智能加载 - 大数据量（全部数据）...")
try:
    result = manager.load_from_database_smart()
    
    print(f"   ✅ 加载成功")
    print(f"   策略: {result.get('strategy')}")
    print(f"   预估数量: {result.get('estimated_count', 0):,}")
    print(f"   实际数量: {len(result['full']):,}")
    
except Exception as e:
    print(f"   ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*70)
print("  测试完成")
print("="*70)
print()
print("💡 功能说明:")
print("   • 智能加载: 根据数据量自动选择最优策略")
print("   • 流式加载: 分批加载，避免内存溢出")
print("   • 内存保护: 限制最大加载行数")
