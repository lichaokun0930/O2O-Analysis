#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试监控面板组件
"""

import sys
import io

# 解决Windows PowerShell下emoji输出乱码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("="*60)
print("  测试监控面板组件")
print("="*60)
print()

# 1. 测试导入
print("📦 [1/4] 测试组件导入...")
try:
    from components.system_monitor_panel import create_monitor_panel, register_monitor_callbacks
    print("   ✅ 组件导入成功")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    sys.exit(1)

# 2. 测试创建面板
print("\n📦 [2/4] 测试创建监控面板...")
try:
    panel = create_monitor_panel()
    print("   ✅ 面板创建成功")
    print(f"   类型: {type(panel)}")
except Exception as e:
    print(f"   ❌ 创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 测试Redis监控器
print("\n📦 [3/4] 测试Redis监控器...")
try:
    from redis_health_monitor import get_health_monitor
    monitor = get_health_monitor(host='localhost', port=6379, check_interval=30)
    print("   ✅ 监控器创建成功")
    
    # 测试连接
    result = monitor.initial_check()
    if result['connected']:
        print(f"   ✅ Redis连接成功")
        print(f"   版本: {result['version']}")
    else:
        print(f"   ⚠️ Redis连接失败")
except Exception as e:
    print(f"   ⚠️ 监控器测试失败: {e}")

# 4. 测试缓存管理器
print("\n📦 [4/4] 测试缓存管理器...")
try:
    from hierarchical_cache_manager import get_cache_manager
    cache_mgr = get_cache_manager(host='localhost', port=6379)
    
    if cache_mgr and cache_mgr.enabled:
        print("   ✅ 缓存管理器可用")
        stats = cache_mgr.get_stats()
        print(f"   命中率: {stats.get('hit_rate', 0):.1f}%")
    else:
        print("   ⚠️ 缓存管理器不可用")
except Exception as e:
    print(f"   ⚠️ 缓存管理器测试失败: {e}")

print()
print("="*60)
print("✅ 监控面板组件测试完成")
print()
print("📋 下一步:")
print("   1. 重启看板: .\\启动看板-调试模式.ps1")
print("   2. 访问: http://localhost:8051")
print("   3. 查看页面顶部的监控面板")
print("="*60)
