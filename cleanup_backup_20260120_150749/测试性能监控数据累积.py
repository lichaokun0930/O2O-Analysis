"""
测试性能监控数据累积

验证：
1. 监控器在Tab切换时正确重置
2. 性能数据在两个异步回调之间正确累积
3. 所有监控项都能正确显示在性能面板中

预期结果：
- 0.数据获取
- 0.数据筛选
- 1.订单聚合
- 2.紧急问题分析
- 3.正向激励分析
- 4.关注问题分析
- 5.商品健康分析
- 6.卡片创建

日期: 2025-12-11
版本: V8.10.3
"""

import sys
import time
from components.today_must_do.performance_monitor import PerformanceMonitor

def test_monitor_accumulation():
    """测试监控器数据累积"""
    print("="*80)
    print("测试1: 监控器数据累积")
    print("="*80)
    
    monitor = PerformanceMonitor()
    
    # 模拟第一个回调（load_diagnosis_async）
    print("\n[模拟] 第一个回调开始...")
    monitor.reset()  # 重置监控器
    
    with monitor.measure('0.数据获取'):
        time.sleep(0.1)
    
    with monitor.measure('0.数据筛选'):
        time.sleep(0.05)
    
    with monitor.measure('1.订单聚合'):
        time.sleep(0.08)
    
    with monitor.measure('2.紧急问题分析'):
        time.sleep(0.06)
    
    with monitor.measure('3.正向激励分析'):
        time.sleep(0.04)
    
    with monitor.measure('4.关注问题分析'):
        time.sleep(0.03)
    
    with monitor.measure('6.卡片创建'):
        time.sleep(0.02)
    
    # 获取第一个回调的性能报告
    report1 = monitor.get_report()
    print(f"\n[第一个回调] 性能报告:")
    print(f"  - 总耗时: {report1['total_time']:.3f}秒")
    print(f"  - 监控项数量: {len(report1['measurements'])}")
    print(f"  - 监控项: {list(report1['measurements'].keys())}")
    
    # 模拟第二个回调（load_product_scoring_async）
    print("\n[模拟] 第二个回调开始...")
    # 注意：不重置监控器，继续累积数据
    
    with monitor.measure('5.商品健康分析'):
        time.sleep(0.15)
    
    # 获取第二个回调的性能报告（应该包含所有监控项）
    report2 = monitor.get_report()
    print(f"\n[第二个回调] 性能报告:")
    print(f"  - 总耗时: {report2['total_time']:.3f}秒")
    print(f"  - 监控项数量: {len(report2['measurements'])}")
    print(f"  - 监控项: {list(report2['measurements'].keys())}")
    
    # 验证
    expected_items = [
        '0.数据获取', '0.数据筛选', '1.订单聚合', '2.紧急问题分析',
        '3.正向激励分析', '4.关注问题分析', '5.商品健康分析', '6.卡片创建'
    ]
    
    print("\n" + "="*80)
    print("验证结果:")
    print("="*80)
    
    all_present = True
    for item in expected_items:
        if item in report2['measurements']:
            print(f"  ✅ {item}: {report2['measurements'][item]['current']:.3f}秒")
        else:
            print(f"  ❌ {item}: 缺失")
            all_present = False
    
    if all_present:
        print("\n✅ 测试通过！所有监控项都正确累积。")
    else:
        print("\n❌ 测试失败！部分监控项缺失。")
    
    return all_present


def test_monitor_reset():
    """测试监控器重置"""
    print("\n" + "="*80)
    print("测试2: 监控器重置")
    print("="*80)
    
    monitor = PerformanceMonitor()
    
    # 第一次测量
    with monitor.measure('测试项1'):
        time.sleep(0.1)
    
    report1 = monitor.get_report()
    print(f"\n[重置前] 监控项数量: {len(report1['measurements'])}")
    
    # 重置
    monitor.reset()
    print("[执行] 监控器已重置")
    
    # 第二次测量
    with monitor.measure('测试项2'):
        time.sleep(0.1)
    
    report2 = monitor.get_report()
    print(f"[重置后] 监控项数量: {len(report2['measurements'])}")
    
    # 验证
    if len(report2['measurements']) == 1 and '测试项2' in report2['measurements']:
        print("\n✅ 测试通过！监控器重置正常。")
        return True
    else:
        print("\n❌ 测试失败！监控器重置异常。")
        return False


def test_global_monitor():
    """测试全局监控器"""
    print("\n" + "="*80)
    print("测试3: 全局监控器")
    print("="*80)
    
    from components.today_must_do.performance_monitor import get_global_monitor
    
    # 获取两次全局监控器，应该是同一个实例
    monitor1 = get_global_monitor()
    monitor2 = get_global_monitor()
    
    if monitor1 is monitor2:
        print("✅ 测试通过！全局监控器是单例。")
        return True
    else:
        print("❌ 测试失败！全局监控器不是单例。")
        return False


if __name__ == '__main__':
    print("\n" + "="*80)
    print("V8.10.3 性能监控数据累积测试")
    print("="*80)
    
    results = []
    
    # 测试1: 数据累积
    results.append(test_monitor_accumulation())
    
    # 测试2: 监控器重置
    results.append(test_monitor_reset())
    
    # 测试3: 全局监控器
    results.append(test_global_monitor())
    
    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    print(f"通过: {sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 所有测试通过！性能监控数据累积功能正常。")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败，请检查代码。")
        sys.exit(1)
