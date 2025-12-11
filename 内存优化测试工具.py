"""
内存优化测试工具
用于对比优化前后的内存使用情况
"""

import psutil
import os
import time
import pandas as pd
from datetime import datetime

class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.baseline = None
        self.checkpoints = []
    
    def set_baseline(self):
        """设置基线内存"""
        self.baseline = self.get_current_memory()
        print(f"📊 基线内存: {self.baseline:.2f} MB")
        return self.baseline
    
    def get_current_memory(self):
        """获取当前内存使用（MB）"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def checkpoint(self, label=""):
        """记录检查点"""
        current = self.get_current_memory()
        if self.baseline:
            increase = current - self.baseline
            self.checkpoints.append({
                'time': datetime.now(),
                'label': label,
                'memory_mb': current,
                'increase_mb': increase
            })
            print(f"🔍 {label}: {current:.2f} MB (增加 {increase:+.2f} MB)")
        else:
            print(f"⚠️ 请先设置基线: monitor.set_baseline()")
        return current
    
    def report(self):
        """生成内存使用报告"""
        if not self.checkpoints:
            print("⚠️ 暂无检查点数据")
            return
        
        print("\n" + "="*60)
        print("📋 内存使用报告")
        print("="*60)
        
        df = pd.DataFrame(self.checkpoints)
        print(df[['label', 'memory_mb', 'increase_mb']].to_string(index=False))
        
        max_checkpoint = df.loc[df['increase_mb'].idxmax()]
        print(f"\n🔴 峰值内存: {max_checkpoint['label']} ({max_checkpoint['memory_mb']:.2f} MB)")
        print(f"📈 总增长: {df['increase_mb'].iloc[-1]:.2f} MB")
        print("="*60 + "\n")


# 测试场景1：对比copy vs 视图
def test_copy_vs_view():
    """测试1：对比全量copy和视图模式的内存差异"""
    print("\n" + "="*60)
    print("🧪 测试1: Copy vs 视图模式")
    print("="*60)
    
    monitor = MemoryMonitor()
    monitor.set_baseline()
    
    # 加载数据
    from 智能门店看板_Dash版 import GLOBAL_DATA
    if GLOBAL_DATA is None:
        print("❌ 数据未加载，请先启动看板")
        return
    
    monitor.checkpoint("1. 数据加载完成")
    
    # 方式1：全量copy（旧方式）
    df_copy = GLOBAL_DATA.copy()
    monitor.checkpoint("2. 全量copy (旧方式)")
    
    # 筛选操作
    df_filtered_copy = df_copy[df_copy['渠道'] == '美团'].copy()
    monitor.checkpoint("3. 筛选后再copy (旧方式)")
    
    del df_copy, df_filtered_copy
    import gc
    gc.collect()
    monitor.checkpoint("4. 清理旧方式数据")
    
    # 方式2：视图模式（新方式）
    df_view = GLOBAL_DATA  # 不copy
    monitor.checkpoint("5. 使用视图 (新方式)")
    
    df_filtered_view = df_view[df_view['渠道'] == '美团']  # 仍然是视图
    monitor.checkpoint("6. 筛选后视图 (新方式)")
    
    del df_view, df_filtered_view
    gc.collect()
    monitor.checkpoint("7. 清理新方式数据")
    
    monitor.report()


# 测试场景2：多层筛选
def test_multiple_filters():
    """测试2：多层筛选的内存差异"""
    print("\n" + "="*60)
    print("🧪 测试2: 多层筛选")
    print("="*60)
    
    monitor = MemoryMonitor()
    monitor.set_baseline()
    
    from 智能门店看板_Dash版 import GLOBAL_DATA
    if GLOBAL_DATA is None:
        print("❌ 数据未加载，请先启动看板")
        return
    
    monitor.checkpoint("1. 初始状态")
    
    # 旧方式：每次都copy
    df1 = GLOBAL_DATA.copy()
    monitor.checkpoint("2. 第1次copy")
    
    df2 = df1[df1['渠道'] == '美团'].copy()
    monitor.checkpoint("3. 第2次copy (渠道筛选)")
    
    if '门店名称' in df2.columns:
        store = df2['门店名称'].iloc[0] if len(df2) > 0 else None
        if store:
            df3 = df2[df2['门店名称'] == store].copy()
            monitor.checkpoint("4. 第3次copy (门店筛选)")
    
    del df1, df2
    try:
        del df3
    except:
        pass
    import gc
    gc.collect()
    monitor.checkpoint("5. 清理旧方式")
    
    # 新方式：链式视图
    df = GLOBAL_DATA  # 视图
    monitor.checkpoint("6. 使用视图")
    
    df = df[df['渠道'] == '美团']  # 仍是视图
    monitor.checkpoint("7. 链式筛选1")
    
    if '门店名称' in df.columns:
        store = df['门店名称'].iloc[0] if len(df) > 0 else None
        if store:
            df = df[df['门店名称'] == store]  # 仍是视图
            monitor.checkpoint("8. 链式筛选2")
    
    del df
    gc.collect()
    monitor.checkpoint("9. 清理新方式")
    
    monitor.report()


# 测试场景3：实际回调模拟
def test_callback_simulation():
    """测试3：模拟实际回调的内存使用"""
    print("\n" + "="*60)
    print("🧪 测试3: 实际回调模拟")
    print("="*60)
    
    monitor = MemoryMonitor()
    monitor.set_baseline()
    
    from 智能门店看板_Dash版 import GLOBAL_DATA
    if GLOBAL_DATA is None:
        print("❌ 数据未加载，请先启动看板")
        return
    
    monitor.checkpoint("1. 回调开始")
    
    # 模拟客单价异常分析
    df = GLOBAL_DATA
    monitor.checkpoint("2. 获取数据(视图)")
    
    # 筛选渠道
    if '渠道' in df.columns:
        df = df[df['渠道'].notna()]
        monitor.checkpoint("3. 筛选渠道(视图)")
    
    # 按日期分组
    if '日期' in df.columns:
        daily_agg = df.groupby('日期')['实收价格'].agg(['sum', 'count'])
        monitor.checkpoint("4. 聚合计算(新对象)")
        
        del daily_agg
    
    import gc
    gc.collect()
    monitor.checkpoint("5. 回调结束")
    
    monitor.report()


# 测试场景4：压力测试
def test_stress():
    """测试4：压力测试 - 连续多次操作"""
    print("\n" + "="*60)
    print("🧪 测试4: 压力测试 (10次操作)")
    print("="*60)
    
    monitor = MemoryMonitor()
    monitor.set_baseline()
    
    from 智能门店看板_Dash版 import GLOBAL_DATA
    if GLOBAL_DATA is None:
        print("❌ 数据未加载，请先启动看板")
        return
    
    # 新方式：视图模式
    for i in range(10):
        df = GLOBAL_DATA
        if '渠道' in df.columns:
            channels = df['渠道'].unique()[:3]  # 取前3个渠道
            for ch in channels:
                df_filtered = df[df['渠道'] == ch]  # 视图
                _ = len(df_filtered)  # 触发计算
        
        if i % 2 == 0:
            monitor.checkpoint(f"迭代 {i+1}/10")
    
    import gc
    gc.collect()
    monitor.checkpoint("压力测试完成")
    
    monitor.report()


# 主测试函数
def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀 " + "="*58)
    print("🚀 内存优化效果测试开始")
    print("🚀 " + "="*58)
    
    tests = [
        ("Copy vs 视图", test_copy_vs_view),
        ("多层筛选", test_multiple_filters),
        ("回调模拟", test_callback_simulation),
        ("压力测试", test_stress)
    ]
    
    for name, test_func in tests:
        try:
            test_func()
            time.sleep(1)  # 给GC时间清理
        except Exception as e:
            print(f"\n❌ {name} 测试失败: {e}\n")
    
    print("\n" + "✅ " + "="*58)
    print("✅ 所有测试完成！")
    print("✅ " + "="*58 + "\n")


# 快速测试函数（不需要启动看板）
def quick_test():
    """快速测试：生成模拟数据"""
    print("\n" + "="*60)
    print("⚡ 快速测试 (模拟数据)")
    print("="*60)
    
    monitor = MemoryMonitor()
    monitor.set_baseline()
    
    # 生成模拟数据
    import numpy as np
    rows = 50000
    df = pd.DataFrame({
        '订单ID': [f'ORDER{i:06d}' for i in range(rows)],
        '渠道': np.random.choice(['美团', '饿了么', '抖音'], rows),
        '门店名称': np.random.choice(['A店', 'B店', 'C店'], rows),
        '实收价格': np.random.uniform(10, 100, rows),
        '日期': pd.date_range('2025-01-01', periods=rows, freq='1H')
    })
    
    monitor.checkpoint("1. 生成50000行数据")
    
    # 旧方式
    df_copy = df.copy()
    monitor.checkpoint("2. 全量copy (旧)")
    
    df_filtered = df_copy[df_copy['渠道'] == '美团'].copy()
    monitor.checkpoint("3. 筛选+copy (旧)")
    
    del df_copy, df_filtered
    import gc
    gc.collect()
    monitor.checkpoint("4. 清理")
    
    # 新方式
    df_view = df
    monitor.checkpoint("5. 视图模式 (新)")
    
    df_filtered = df_view[df_view['渠道'] == '美团']
    monitor.checkpoint("6. 筛选(视图) (新)")
    
    del df_view, df_filtered
    gc.collect()
    monitor.checkpoint("7. 清理")
    
    monitor.report()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 内存优化测试工具")
    print("="*60)
    print("\n选择测试模式：")
    print("1. 快速测试 (不需要启动看板)")
    print("2. 完整测试 (需要先启动看板)")
    print("="*60)
    
    choice = input("\n请选择 (1/2): ").strip()
    
    if choice == "1":
        quick_test()
    elif choice == "2":
        run_all_tests()
    else:
        print("\n⚡ 默认运行快速测试...\n")
        quick_test()
    
    print("\n💡 提示：")
    print("  - 内存增长 < 10MB = 优化效果显著")
    print("  - 内存增长 > 50MB = 可能存在不必要的copy")
    print("  - 对比 '旧方式' vs '新方式' 的内存差异\n")
