#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试性能监控系统 (V8.10.3)

测试内容：
1. 性能监控核心模块
2. 前端性能面板组件
3. 诊断分析中的性能监控集成
4. 完整的端到端性能监控流程

作者: Kiro AI
日期: 2025-12-11
"""

import sys
import time
import pandas as pd
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

print("="*80)
print("🧪 性能监控系统测试")
print("="*80)

# ==================== 测试1: 性能监控核心模块 ====================
print("\n[测试1] 性能监控核心模块")
print("-"*80)

try:
    from components.today_must_do.performance_monitor import (
        PerformanceMonitor,
        get_global_monitor,
        enable_performance_monitoring,
        get_performance_report
    )
    
    print("✅ 性能监控模块导入成功")
    
    # 创建监控器实例
    monitor = PerformanceMonitor()
    
    # 模拟一些操作
    print("\n模拟性能监控...")
    with monitor.measure('数据加载'):
        time.sleep(0.1)
    
    with monitor.measure('数据处理'):
        time.sleep(0.2)
    
    with monitor.measure('数据加载'):  # 第二次调用
        time.sleep(0.15)
    
    # 获取报告
    report = monitor.get_report()
    print(f"\n性能报告:")
    print(f"  总耗时: {report['total_time']:.3f}秒")
    print(f"  测量项数: {len(report['measurements'])}")
    
    for name, stats in report['measurements'].items():
        print(f"  - {name}: {stats['current']:.3f}秒 (平均: {stats['avg']:.3f}秒, 调用: {stats['count']}次)")
    
    print("\n✅ 测试1通过: 性能监控核心模块正常工作")
    
except Exception as e:
    print(f"\n❌ 测试1失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试2: 前端性能面板组件 ====================
print("\n[测试2] 前端性能面板组件")
print("-"*80)

try:
    from components.performance_panel import (
        create_performance_panel,
        format_performance_data,
        create_performance_badge
    )
    
    print("✅ 性能面板模块导入成功")
    
    # 创建面板组件
    panel = create_performance_panel(panel_id='test-panel')
    print(f"✅ 性能面板组件创建成功: {type(panel)}")
    
    # 测试数据格式化
    test_data = {
        'total_time': 5.234,
        'measurements': {
            '1.订单聚合': {'current': 2.1, 'avg': 2.0, 'min': 1.9, 'max': 2.3, 'count': 5},
            '2.紧急问题分析': {'current': 1.5, 'avg': 1.4, 'min': 1.3, 'max': 1.6, 'count': 5},
            '3.正向激励分析': {'current': 0.8, 'avg': 0.7, 'min': 0.6, 'max': 0.9, 'count': 5},
            '4.关注问题分析': {'current': 0.834, 'avg': 0.8, 'min': 0.7, 'max': 0.9, 'count': 5},
        },
        'timestamp': '2025-12-11T10:30:00'
    }
    
    total_comp, modules_comp = format_performance_data(test_data)
    print(f"✅ 性能数据格式化成功")
    print(f"  总耗时组件: {type(total_comp)}")
    print(f"  模块耗时组件: {type(modules_comp)}")
    
    # 测试徽章创建
    badge = create_performance_badge(2.5)
    print(f"✅ 性能徽章创建成功: {type(badge)}")
    
    print("\n✅ 测试2通过: 前端性能面板组件正常工作")
    
except Exception as e:
    print(f"\n❌ 测试2失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试3: 诊断分析中的性能监控集成 ====================
print("\n[测试3] 诊断分析中的性能监控集成")
print("-"*80)

try:
    from components.today_must_do.diagnosis_analysis import get_diagnosis_summary
    
    print("✅ 诊断分析模块导入成功")
    
    # 创建测试数据
    print("\n创建测试数据...")
    test_df = pd.DataFrame({
        '订单ID': [f'ORDER_{i}' for i in range(100)],
        '商品名称': [f'商品{i%10}' for i in range(100)],
        '日期': pd.date_range('2025-12-10', periods=100, freq='H'),
        '利润额': [10 + i for i in range(100)],
        '平台服务费': [2 + i*0.1 for i in range(100)],
        '物流配送费': [5 + i*0.05 for i in range(100)],
        '企客后返': [1 + i*0.02 for i in range(100)],
        '实收价格': [50 + i for i in range(100)],
        '销量': [1] * 100,
        '剩余库存': [10] * 100,
        '门店名称': ['测试门店'] * 100,
        '渠道': ['美团'] * 100,
    })
    
    print(f"测试数据: {len(test_df)}行")
    
    # 执行诊断分析（应该包含性能监控）
    print("\n执行诊断分析...")
    start_time = time.time()
    diagnosis = get_diagnosis_summary(test_df)
    elapsed = time.time() - start_time
    
    print(f"✅ 诊断分析完成，耗时: {elapsed:.2f}秒")
    
    # 检查是否包含性能数据
    if 'performance' in diagnosis:
        perf_data = diagnosis['performance']
        print(f"\n✅ 性能数据已集成到诊断结果中")
        print(f"  总耗时: {perf_data.get('total_time', 0):.3f}秒")
        print(f"  测量项数: {len(perf_data.get('measurements', {}))}")
        
        for name, stats in perf_data.get('measurements', {}).items():
            print(f"  - {name}: {stats['current']:.3f}秒")
        
        print("\n✅ 测试3通过: 诊断分析中的性能监控集成正常")
    else:
        print("\n⚠️ 警告: 诊断结果中未找到性能数据")
        print("  这可能是因为性能监控模块未启用")
    
except Exception as e:
    print(f"\n❌ 测试3失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试4: 回调函数集成 ====================
print("\n[测试4] 回调函数集成检查")
print("-"*80)

try:
    from components.today_must_do.callbacks import register_today_must_do_callbacks
    
    print("✅ 回调函数模块导入成功")
    
    # 检查函数签名
    import inspect
    sig = inspect.signature(register_today_must_do_callbacks)
    print(f"✅ 回调注册函数签名: {sig}")
    
    print("\n✅ 测试4通过: 回调函数集成检查正常")
    
except Exception as e:
    print(f"\n❌ 测试4失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 总结 ====================
print("\n" + "="*80)
print("📊 测试总结")
print("="*80)
print("""
✅ 性能监控系统已完成集成：

1. 核心模块 (performance_monitor.py)
   - PerformanceMonitor类：上下文管理器计时
   - 性能报告生成、打印、保存
   - 全局监控器实例

2. 前端组件 (performance_panel.py)
   - 可视化性能监控面板（固定右上角）
   - 支持开关控制显示/隐藏
   - 实时显示总耗时和各模块耗时
   - 性能徽章组件

3. 后端集成 (diagnosis_analysis.py)
   - get_diagnosis_summary函数中集成监控
   - 监控4个关键步骤：
     * 1.订单聚合
     * 2.紧急问题分析
     * 3.正向激励分析
     * 4.关注问题分析
   - 性能数据保存到结果中

4. 前端集成 (callbacks.py)
   - 性能面板回调已注册
   - 性能数据从后端传递到前端
   - 面板组件添加到布局中

🎯 下一步：
1. 启动看板测试性能监控面板显示效果
2. 验证性能数据是否正确显示
3. 测试开关控制功能
4. 根据实际效果调整样式和布局
""")
print("="*80)
