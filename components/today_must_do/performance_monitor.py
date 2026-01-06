"""
性能监控模块 (V8.10.3)

功能：
1. 监控各个诊断看板的执行时间
2. 记录性能日志
3. 提供性能统计和分析

使用方法：
    from performance_monitor import PerformanceMonitor
    
    monitor = PerformanceMonitor()
    
    with monitor.measure('穿底止血分析'):
        # 执行分析逻辑
        result = analyze_overflow(...)
    
    # 获取性能报告
    report = monitor.get_report()
"""

import time
from typing import Dict, List, Optional
from contextlib import contextmanager
from datetime import datetime
import json


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, enabled: bool = True):
        """
        初始化性能监控器
        
        Args:
            enabled: 是否启用监控（默认启用）
        """
        self.enabled = enabled
        self.measurements: Dict[str, List[float]] = {}
        self.current_measurements: Dict[str, float] = {}
        self.start_time = time.time()
        
    @contextmanager
    def measure(self, name: str, print_result: bool = True):
        """
        测量代码块执行时间
        
        Args:
            name: 测量项名称
            print_result: 是否打印结果
        
        Example:
            with monitor.measure('数据加载'):
                df = load_data()
        """
        if not self.enabled:
            yield
            return
        
        start = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start
            
            # 记录测量结果
            if name not in self.measurements:
                self.measurements[name] = []
            self.measurements[name].append(elapsed)
            self.current_measurements[name] = elapsed
            
            # 打印结果
            if print_result:
                print(f"⏱️ [性能] {name}: {elapsed:.3f}秒")
    
    def get_report(self) -> Dict:
        """
        获取性能报告
        
        Returns:
            {
                'total_time': 总耗时,
                'measurements': {
                    '模块名': {
                        'current': 当前耗时,
                        'avg': 平均耗时,
                        'min': 最小耗时,
                        'max': 最大耗时,
                        'count': 调用次数
                    }
                },
                'timestamp': 时间戳
            }
        """
        total_time = time.time() - self.start_time
        
        report = {
            'total_time': round(total_time, 3),
            'measurements': {},
            'timestamp': datetime.now().isoformat()
        }
        
        for name, times in self.measurements.items():
            report['measurements'][name] = {
                'current': round(self.current_measurements.get(name, 0), 3),
                'avg': round(sum(times) / len(times), 3),
                'min': round(min(times), 3),
                'max': round(max(times), 3),
                'count': len(times)
            }
        
        return report
    
    def print_report(self):
        """打印性能报告"""
        report = self.get_report()
        
        print("\n" + "="*80)
        print("📊 性能监控报告")
        print("="*80)
        print(f"总耗时: {report['total_time']:.3f}秒")
        print(f"时间戳: {report['timestamp']}")
        print("\n各模块耗时:")
        print("-"*80)
        
        # 按当前耗时排序
        sorted_items = sorted(
            report['measurements'].items(),
            key=lambda x: x[1]['current'],
            reverse=True
        )
        
        for name, stats in sorted_items:
            print(f"  {name:30s} {stats['current']:6.3f}秒 "
                  f"(平均: {stats['avg']:.3f}秒, 调用: {stats['count']}次)")
        
        print("="*80 + "\n")
    
    def save_report(self, filepath: str = 'performance_report.json'):
        """
        保存性能报告到文件
        
        Args:
            filepath: 文件路径
        """
        report = self.get_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"✅ 性能报告已保存到: {filepath}")
    
    def reset(self):
        """重置监控数据"""
        self.measurements.clear()
        self.current_measurements.clear()
        self.start_time = time.time()


# 全局性能监控器实例
_global_monitor: Optional[PerformanceMonitor] = None


def get_global_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def enable_performance_monitoring():
    """启用性能监控"""
    monitor = get_global_monitor()
    monitor.enabled = True
    print("✅ 性能监控已启用")


def disable_performance_monitoring():
    """禁用性能监控"""
    monitor = get_global_monitor()
    monitor.enabled = False
    print("⚠️ 性能监控已禁用")


def get_performance_report() -> Dict:
    """获取全局性能报告"""
    return get_global_monitor().get_report()


def print_performance_report():
    """打印全局性能报告"""
    get_global_monitor().print_report()


# 测试代码
if __name__ == '__main__':
    # 测试性能监控
    monitor = PerformanceMonitor()
    
    # 模拟一些操作
    with monitor.measure('数据加载'):
        time.sleep(0.1)
    
    with monitor.measure('数据处理'):
        time.sleep(0.2)
    
    with monitor.measure('数据加载'):  # 第二次调用
        time.sleep(0.15)
    
    # 打印报告
    monitor.print_report()
    
    # 保存报告
    monitor.save_report('test_performance.json')
