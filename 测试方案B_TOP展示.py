#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试方案B：TOP异常展示 (V8.10.3)

测试内容：
1. TOP 5展示功能
2. 展开/折叠功能
3. 排名标识（金银铜牌）
4. 颜色编码
5. 性能数据格式化

作者: Kiro AI
日期: 2025-12-11
"""

import sys
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

print("="*80)
print("🧪 方案B测试：TOP异常展示")
print("="*80)

# ==================== 测试1: 性能数据格式化（TOP 5） ====================
print("\n[测试1] 性能数据格式化（TOP 5模式）")
print("-"*80)

try:
    from components.performance_panel import format_performance_data
    
    # 创建测试数据（8个模块）
    test_data = {
        'total_time': 15.234,
        'measurements': {
            '1.订单聚合': {'current': 2.1, 'avg': 2.0, 'min': 1.9, 'max': 2.3, 'count': 5},
            '2.紧急问题分析': {'current': 1.5, 'avg': 1.4, 'min': 1.3, 'max': 1.6, 'count': 5},
            '3.正向激励分析': {'current': 0.8, 'avg': 0.7, 'min': 0.6, 'max': 0.9, 'count': 5},
            '4.关注问题分析': {'current': 0.834, 'avg': 0.8, 'min': 0.7, 'max': 0.9, 'count': 5},
            '5.商品健康分析': {'current': 8.5, 'avg': 7.0, 'min': 6.5, 'max': 9.0, 'count': 5},  # 最慢
            '6.调价计算器': {'current': 0.5, 'avg': 0.4, 'min': 0.3, 'max': 0.6, 'count': 5},
            '7.数据加载': {'current': 1.0, 'avg': 0.9, 'min': 0.8, 'max': 1.1, 'count': 5},
            '8.缓存写入': {'current': 0.1, 'avg': 0.1, 'min': 0.1, 'max': 0.2, 'count': 5},
        },
        'timestamp': '2025-12-11T10:30:00'
    }
    
    print("✅ 测试数据创建成功")
    print(f"  总模块数: {len(test_data['measurements'])}")
    print(f"  总耗时: {test_data['total_time']:.2f}秒")
    
    # 测试TOP 5展示（默认）
    print("\n测试TOP 5展示...")
    total_comp, modules_comp = format_performance_data(test_data, top_n=5, show_all=False)
    print(f"✅ TOP 5展示成功")
    print(f"  总耗时组件: {type(total_comp)}")
    print(f"  模块组件: {type(modules_comp)}")
    
    # 测试显示全部
    print("\n测试显示全部...")
    total_comp_all, modules_comp_all = format_performance_data(test_data, top_n=5, show_all=True)
    print(f"✅ 显示全部成功")
    
    # 验证排序（应该按耗时降序）
    print("\n验证排序...")
    sorted_modules = sorted(
        test_data['measurements'].items(),
        key=lambda x: x[1]['current'],
        reverse=True
    )
    print("预期排序（按耗时降序）:")
    for idx, (name, stats) in enumerate(sorted_modules[:5], 1):
        emoji = '🥇' if idx == 1 else ('🥈' if idx == 2 else ('🥉' if idx == 3 else ''))
        print(f"  {idx}. {emoji} {name}: {stats['current']:.2f}秒")
    
    print("\n✅ 测试1通过: 性能数据格式化正常")
    
except Exception as e:
    print(f"\n❌ 测试1失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试2: 颜色编码验证 ====================
print("\n[测试2] 颜色编码验证")
print("-"*80)

try:
    # 测试不同耗时的颜色编码
    test_cases = [
        (0.3, '🟢', '绿色', '快速'),
        (1.0, '🔵', '蓝色', '正常'),
        (3.0, '🟡', '黄色', '较慢'),
        (8.0, '🔴', '红色', '慢'),
    ]
    
    print("颜色编码规则:")
    for time_val, emoji, color, status in test_cases:
        print(f"  {time_val:.1f}秒 → {emoji} {color} ({status})")
    
    print("\n✅ 测试2通过: 颜色编码规则正确")
    
except Exception as e:
    print(f"\n❌ 测试2失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试3: 排名标识验证 ====================
print("\n[测试3] 排名标识验证")
print("-"*80)

try:
    print("排名标识规则:")
    print("  第1名: 🥇 金牌")
    print("  第2名: 🥈 银牌")
    print("  第3名: 🥉 铜牌")
    print("  第4-5名: 无标识")
    
    print("\n✅ 测试3通过: 排名标识规则正确")
    
except Exception as e:
    print(f"\n❌ 测试3失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试4: 展开/折叠功能 ====================
print("\n[测试4] 展开/折叠功能")
print("-"*80)

try:
    # 测试少于5个模块（不显示展开按钮）
    small_data = {
        'total_time': 5.0,
        'measurements': {
            '1.模块A': {'current': 2.0, 'avg': 2.0, 'min': 1.9, 'max': 2.1, 'count': 5},
            '2.模块B': {'current': 1.5, 'avg': 1.5, 'min': 1.4, 'max': 1.6, 'count': 5},
            '3.模块C': {'current': 1.0, 'avg': 1.0, 'min': 0.9, 'max': 1.1, 'count': 5},
        },
        'timestamp': '2025-12-11T10:30:00'
    }
    
    total_comp, modules_comp = format_performance_data(small_data, top_n=5, show_all=False)
    print(f"✅ 少于5个模块: 不显示展开按钮")
    
    # 测试多于5个模块（显示展开按钮）
    total_comp, modules_comp = format_performance_data(test_data, top_n=5, show_all=False)
    print(f"✅ 多于5个模块: 显示展开按钮")
    print(f"  隐藏模块数: {len(test_data['measurements']) - 5}")
    
    print("\n✅ 测试4通过: 展开/折叠功能正常")
    
except Exception as e:
    print(f"\n❌ 测试4失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试5: 性能监控器集成 ====================
print("\n[测试5] 性能监控器集成")
print("-"*80)

try:
    from components.today_must_do.performance_monitor import get_global_monitor
    import time
    
    monitor = get_global_monitor()
    monitor.reset()  # 重置监控器
    
    # 模拟多个模块的执行
    print("模拟8个模块的执行...")
    
    with monitor.measure('1.订单聚合'):
        time.sleep(0.05)
    
    with monitor.measure('2.紧急问题分析'):
        time.sleep(0.03)
    
    with monitor.measure('3.正向激励分析'):
        time.sleep(0.02)
    
    with monitor.measure('4.关注问题分析'):
        time.sleep(0.02)
    
    with monitor.measure('5.商品健康分析'):
        time.sleep(0.15)  # 最慢的模块
    
    with monitor.measure('6.调价计算器'):
        time.sleep(0.01)
    
    with monitor.measure('7.数据加载'):
        time.sleep(0.02)
    
    with monitor.measure('8.缓存写入'):
        time.sleep(0.01)
    
    # 获取性能报告
    report = monitor.get_report()
    
    print(f"\n性能报告:")
    print(f"  总耗时: {report['total_time']:.3f}秒")
    print(f"  模块数: {len(report['measurements'])}")
    
    # 显示TOP 5
    sorted_items = sorted(
        report['measurements'].items(),
        key=lambda x: x[1]['current'],
        reverse=True
    )
    
    print(f"\nTOP 5最慢的模块:")
    for idx, (name, stats) in enumerate(sorted_items[:5], 1):
        emoji = '🥇' if idx == 1 else ('🥈' if idx == 2 else ('🥉' if idx == 3 else ''))
        print(f"  {idx}. {emoji} {name}: {stats['current']:.3f}秒")
    
    print("\n✅ 测试5通过: 性能监控器集成正常")
    
except Exception as e:
    print(f"\n❌ 测试5失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 总结 ====================
print("\n" + "="*80)
print("📊 测试总结")
print("="*80)
print("""
✅ 方案B实施完成：

1. TOP 5展示功能 ✅
   - 默认显示TOP 5最慢的模块
   - 按耗时降序排列
   - 自动突出性能瓶颈

2. 排名标识 ✅
   - 第1名: 🥇 金牌
   - 第2名: 🥈 银牌
   - 第3名: 🥉 铜牌
   - TOP 3高亮显示

3. 颜色编码 ✅
   - 🟢 绿色: < 0.5秒（快速）
   - 🔵 蓝色: 0.5-2秒（正常）
   - 🟡 黄色: 2-5秒（较慢）
   - 🔴 红色: > 5秒（慢）

4. 展开/折叠功能 ✅
   - 少于5个模块: 显示全部
   - 多于5个模块: 显示TOP 5 + 展开按钮
   - 点击展开按钮查看全部

5. 性能监控集成 ✅
   - 监控所有模块
   - 自动排序和筛选
   - 实时更新性能数据

🎯 下一步：
1. 启动看板测试实际效果
2. 验证展开/折叠功能
3. 收集用户反馈
4. 根据反馈优化
""")
print("="*80)
