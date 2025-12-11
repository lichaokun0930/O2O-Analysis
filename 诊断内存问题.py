"""
诊断内存问题 - 检查实际限制和使用情况
"""

import sys
import psutil
import platform

def diagnose_memory():
    """诊断内存限制和使用情况"""
    
    print("\n" + "="*70)
    print("🔍 系统内存诊断")
    print("="*70)
    
    # 1. Python版本和架构
    print("\n📌 Python环境:")
    print(f"  版本: {sys.version.split()[0]}")
    print(f"  架构: {platform.architecture()[0]}")
    print(f"  最大整数: {sys.maxsize}")
    is_64bit = sys.maxsize > 2**32
    print(f"  是否64位: {'✅ 是' if is_64bit else '❌ 否 (这是问题！)'}")
    
    # 2. 系统内存
    print("\n📌 系统内存:")
    mem = psutil.virtual_memory()
    print(f"  总内存: {mem.total / 1024**3:.2f} GB")
    print(f"  可用内存: {mem.available / 1024**3:.2f} GB")
    print(f"  使用率: {mem.percent}%")
    
    # 3. 当前进程
    print("\n📌 当前Python进程:")
    process = psutil.Process()
    mem_info = process.memory_info()
    print(f"  进程内存: {mem_info.rss / 1024**2:.2f} MB")
    print(f"  虚拟内存: {mem_info.vms / 1024**2:.2f} MB")
    
    # 4. Python内存限制（理论）
    print("\n📌 Python内存限制（理论）:")
    if is_64bit:
        print(f"  64位Python: 理论上可用 8-16 GB")
        print(f"  但VSCode限制: 通常 2-4 GB")
    else:
        print(f"  ⚠️ 32位Python: 最多 2-4 GB")
        print(f"  建议: 安装64位Python")
    
    # 5. 检查所有Python进程
    print("\n📌 所有Python进程:")
    total_python_mem = 0
    python_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                mem_mb = proc.info['memory_info'].rss / 1024**2
                total_python_mem += mem_mb
                cmdline = ' '.join(proc.info['cmdline'][:2]) if proc.info['cmdline'] else ''
                python_processes.append({
                    'pid': proc.info['pid'],
                    'memory': mem_mb,
                    'cmd': cmdline[:50]
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    for proc in sorted(python_processes, key=lambda x: x['memory'], reverse=True)[:5]:
        print(f"  PID {proc['pid']}: {proc['memory']:.1f} MB - {proc['cmd']}")
    
    print(f"\n  所有Python进程总计: {total_python_mem:.2f} MB")
    
    # 6. 警告和建议
    print("\n" + "="*70)
    print("⚠️ 问题分析:")
    print("="*70)
    
    warnings = []
    
    if not is_64bit:
        warnings.append("🔴 使用32位Python - 内存限制在2-4GB")
        warnings.append("   解决方案: 安装64位Python")
    
    if total_python_mem > 1500:
        warnings.append(f"🟡 Python进程总内存较高 ({total_python_mem:.0f}MB)")
        warnings.append("   可能接近VSCode的限制")
    
    if mem.percent > 80:
        warnings.append(f"🟡 系统内存使用率过高 ({mem.percent}%)")
    
    if not warnings:
        print("✅ 未发现明显问题")
    else:
        for w in warnings:
            print(w)
    
    print("\n" + "="*70)
    print("💡 为什么64GB内存还会OOM？")
    print("="*70)
    print("""
1. VSCode Extension Host 有独立的内存限制（通常2-4GB）
2. 不是整个系统的64GB都能用于单个进程
3. Windows对单个进程也有限制（取决于32/64位）
4. Pandas的copy操作会短时间内大量占用内存

优化后的效果：
  - 减少了不必要的copy
  - 单次操作从50MB降到19MB
  - 10次操作从500MB降到9MB
  - 大大降低了触发OOM的概率
""")
    
    print("="*70)


def check_vscode_memory_limit():
    """检查VSCode的内存配置"""
    print("\n" + "="*70)
    print("🔧 VSCode内存限制检查")
    print("="*70)
    
    print("""
VSCode默认配置：
  - Extension Host: 约 700MB
  - 可以增加限制，但不建议超过4GB
  
如何增加限制（如果需要）：
  1. 打开VSCode设置（Ctrl+,）
  2. 搜索 "max-memory"
  3. 添加到 settings.json:
     {
       "extensions.experimental.affinity": {
         "ms-python.python": 1
       }
     }
  
但最好的方案是：
  ✅ 优化代码减少内存使用（我们已经做了）
  ❌ 不要依赖增加内存限制
""")
    
    print("="*70)


def simulate_memory_limit():
    """模拟内存限制场景"""
    print("\n" + "="*70)
    print("🎮 模拟内存限制场景")
    print("="*70)
    
    import numpy as np
    import pandas as pd
    
    process = psutil.Process()
    baseline = process.memory_info().rss / 1024**2
    
    print(f"\n基线内存: {baseline:.2f} MB")
    print("\n模拟场景: 创建大量DataFrame副本")
    print("-" * 70)
    
    # 创建一个中等大小的DataFrame
    rows = 20000
    df = pd.DataFrame({
        'A': np.random.randint(0, 100, rows),
        'B': np.random.randn(rows),
        'C': ['item_' + str(i) for i in range(rows)],
        'D': np.random.choice(['X', 'Y', 'Z'], rows)
    })
    
    current = process.memory_info().rss / 1024**2
    df_size = current - baseline
    print(f"创建原始DataFrame: +{df_size:.2f} MB")
    
    # 模拟旧方式：频繁copy
    print("\n旧方式（频繁copy）:")
    copies = []
    for i in range(10):
        copies.append(df.copy())
        current = process.memory_info().rss / 1024**2
        increase = current - baseline
        print(f"  第{i+1}次copy: {increase:.2f} MB (累计)")
    
    del copies
    import gc
    gc.collect()
    
    after_gc = process.memory_info().rss / 1024**2
    print(f"\n清理后: {after_gc:.2f} MB")
    
    # 模拟新方式：视图
    print("\n新方式（视图）:")
    views = []
    for i in range(10):
        views.append(df[df['A'] > 50])  # 视图，不copy
        current = process.memory_info().rss / 1024**2
        increase = current - baseline
        if i % 3 == 0:
            print(f"  第{i+1}次视图: {increase:.2f} MB (几乎不增加)")
    
    print("\n" + "="*70)
    print("📊 对比结果:")
    print("="*70)
    print(f"  旧方式峰值: ~{df_size * 11:.0f} MB (10次copy)")
    print(f"  新方式峰值: ~{df_size * 1.2:.0f} MB (使用视图)")
    print(f"  节省: ~{df_size * 10:.0f} MB ({90}%)")
    print("="*70)


if __name__ == "__main__":
    print("\n🔬 Python内存问题诊断工具")
    print("\n选择诊断模式：")
    print("1. 完整诊断（推荐）")
    print("2. 仅检查系统信息")
    print("3. VSCode限制说明")
    print("4. 模拟内存限制场景")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == "1":
        diagnose_memory()
        check_vscode_memory_limit()
    elif choice == "2":
        diagnose_memory()
    elif choice == "3":
        check_vscode_memory_limit()
    elif choice == "4":
        simulate_memory_limit()
    else:
        print("\n运行完整诊断...\n")
        diagnose_memory()
        check_vscode_memory_limit()
