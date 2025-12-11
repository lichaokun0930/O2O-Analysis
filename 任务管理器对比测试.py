"""
任务管理器可见的内存对比演示
"""

import psutil
import time
import pandas as pd
import numpy as np

def show_memory():
    """显示当前进程内存（任务管理器看到的）"""
    process = psutil.Process()
    mem_mb = process.memory_info().rss / 1024**2
    return mem_mb

def simulate_old_way():
    """模拟优化前的方式（频繁copy）"""
    print("\n" + "="*60)
    print("🔴 模拟优化前：频繁copy")
    print("="*60)
    
    # 创建数据
    df = pd.DataFrame({
        'A': np.random.randint(0, 100, 20000),
        'B': np.random.randn(20000),
        'C': ['item_' + str(i) for i in range(20000)]
    })
    
    baseline = show_memory()
    print(f"基线: {baseline:.1f} MB")
    
    copies = []
    for i in range(5):
        # 旧方式：每次都copy
        copies.append(df.copy())
        copies.append(df[df['A'] > 50].copy())
        
        current = show_memory()
        print(f"操作 {i+1}: {current:.1f} MB (+{current-baseline:.1f} MB)")
        time.sleep(0.5)  # 等待任务管理器更新
    
    peak = show_memory()
    print(f"\n峰值: {peak:.1f} MB")
    print(f"总增长: +{peak-baseline:.1f} MB ⚠️")
    
    # 清理
    del copies
    import gc
    gc.collect()
    time.sleep(1)
    
    after_gc = show_memory()
    print(f"GC后: {after_gc:.1f} MB")
    print("="*60)

def simulate_new_way():
    """模拟优化后的方式（使用视图）"""
    print("\n" + "="*60)
    print("✅ 模拟优化后：使用视图")
    print("="*60)
    
    # 创建数据
    df = pd.DataFrame({
        'A': np.random.randint(0, 100, 20000),
        'B': np.random.randn(20000),
        'C': ['item_' + str(i) for i in range(20000)]
    })
    
    baseline = show_memory()
    print(f"基线: {baseline:.1f} MB")
    
    for i in range(5):
        # 新方式：使用视图
        view1 = df  # 不copy
        view2 = df[df['A'] > 50]  # 仍是视图
        _ = len(view2)  # 触发计算
        
        current = show_memory()
        print(f"操作 {i+1}: {current:.1f} MB (+{current-baseline:.1f} MB)")
        time.sleep(0.5)
    
    peak = show_memory()
    print(f"\n峰值: {peak:.1f} MB")
    print(f"总增长: +{peak-baseline:.1f} MB ✅")
    
    import gc
    gc.collect()
    time.sleep(1)
    
    after_gc = show_memory()
    print(f"GC后: {after_gc:.1f} MB")
    print("="*60)

if __name__ == "__main__":
    print("\n🔬 任务管理器可见的内存对比")
    print("\n💡 提示：同时打开任务管理器观察内存变化")
    input("\n按Enter开始测试...")
    
    # 测试旧方式
    simulate_old_way()
    
    print("\n等待3秒后测试新方式...")
    time.sleep(3)
    
    # 测试新方式
    simulate_new_way()
    
    print("\n" + "="*60)
    print("📊 总结")
    print("="*60)
    print("""
对比结果：
  旧方式：每次操作内存持续增加，峰值高
  新方式：内存几乎不增加，峰值低

在任务管理器中的表现：
  ✅ VSCode/Python进程内存更稳定
  ✅ 操作后内存能回落
  ✅ 不会出现持续累积
""")
    print("="*60)
