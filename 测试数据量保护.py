#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据量保护功能
验证千万级数据不会卡死系统
"""
import sys
import io
from datetime import datetime, timedelta

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("="*70)
print("  测试数据量保护功能")
print("="*70)
print()

# 测试1: 检查数据总量
print("📊 [1/3] 检查数据总量...")
try:
    from database.connection import get_db
    from database.models import Order
    
    db = next(get_db())
    total_count = db.query(Order).count()
    
    print(f"   ✅ 订单总数: {total_count:,} 条")
    
    if total_count > 10000000:
        print(f"   🚨 数据量超过 1000 万，属于超大规模")
    elif total_count > 1000000:
        print(f"   ⚠️ 数据量超过 100 万，属于大规模")
    elif total_count > 100000:
        print(f"   ✅ 数据量超过 10 万，属于中等规模")
    else:
        print(f"   ✅ 数据量适中")
    
except Exception as e:
    print(f"   ❌ 检查失败: {e}")
    sys.exit(1)

print()

# 测试2: 测试数据量保护
print("🛡️ [2/3] 测试数据量保护...")
try:
    from database.data_source_manager import DataSourceManager
    
    manager = DataSourceManager()
    
    # 测试场景1: 查询全部数据（应该被拦截）
    print("   测试场景1: 查询全部数据（无过滤）")
    try:
        result = manager.load_from_database()
        print(f"   ❌ 未被拦截，返回了 {len(result.get('full', []))} 条")
    except ValueError as e:
        print(f"   ✅ 成功拦截: {str(e).split(chr(10))[0]}")
    except Exception as e:
        print(f"   ⚠️ 其他错误: {e}")
    
    print()
    
    # 测试场景2: 查询最近 30 天（应该通过）
    print("   测试场景2: 查询最近 30 天")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        result = manager.load_from_database(
            start_date=start_date,
            end_date=end_date
        )
        
        full_df = result.get('full')
        if full_df is not None and not full_df.empty:
            print(f"   ✅ 查询成功，返回 {len(full_df):,} 条记录")
        else:
            print(f"   ⚠️ 查询成功但无数据")
    except ValueError as e:
        print(f"   ⚠️ 被拦截: {str(e).split(chr(10))[0]}")
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
    
except Exception as e:
    print(f"   ❌ 测试失败: {e}")

print()

# 测试3: 显示保护阈值
print("📋 [3/3] 数据量保护配置...")
print("   最大允许: 500,000 条")
print("   警告阈值: 100,000 条")
print()
print("   💡 建议:")
print("      • < 10 万条: 可以全量查询")
print("      • 10-50 万条: 建议限制范围")
print("      • > 50 万条: 必须限制范围")
print("      • > 1000 万条: 禁止全量查询")

print()
print("="*70)
print("  测试完成")
print("="*70)
