"""
实时内存监控 - 看板运行时使用
在看板运行期间实时监控内存变化
"""

import psutil
import time
import os
from datetime import datetime

def monitor_dashboard_memory(interval=5, duration=60):
    """
    实时监控看板内存使用
    
    Args:
        interval: 监控间隔（秒）
        duration: 监控时长（秒），0表示持续监控
    """
    print("\n" + "="*70)
    print("🔍 实时内存监控启动")
    print("="*70)
    print(f"⏱️  监控间隔: {interval}秒")
    print(f"⏱️  监控时长: {'持续' if duration == 0 else f'{duration}秒'}")
    print("="*70)
    
    # 查找Python进程（看板进程）
    current_pid = os.getpid()
    python_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and any('智能门店看板' in str(cmd) for cmd in cmdline):
                    python_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if not python_processes:
        print("⚠️  未找到看板进程，监控当前进程")
        python_processes = [psutil.Process(current_pid)]
    
    print(f"📊 监控 {len(python_processes)} 个进程\n")
    
    start_time = time.time()
    baseline = {}
    max_memory = {}
    
    try:
        iteration = 0
        while True:
            iteration += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            
            print(f"[{current_time}] ", end="")
            
            total_memory = 0
            for proc in python_processes:
                try:
                    mem_info = proc.memory_info()
                    memory_mb = mem_info.rss / 1024 / 1024
                    total_memory += memory_mb
                    
                    pid = proc.pid
                    if pid not in baseline:
                        baseline[pid] = memory_mb
                        max_memory[pid] = memory_mb
                    
                    if memory_mb > max_memory[pid]:
                        max_memory[pid] = memory_mb
                    
                    increase = memory_mb - baseline[pid]
                    peak_increase = max_memory[pid] - baseline[pid]
                    
                    # 内存状态指示
                    if increase > 100:
                        status = "🔴"
                    elif increase > 50:
                        status = "🟡"
                    else:
                        status = "🟢"
                    
                    print(f"{status} PID:{pid} 当前:{memory_mb:.1f}MB "
                          f"(+{increase:+.1f}MB) 峰值:+{peak_increase:.1f}MB", end=" | ")
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            print(f"总计:{total_memory:.1f}MB")
            
            # 检查是否超时
            if duration > 0 and (time.time() - start_time) >= duration:
                break
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  监控已停止")
    
    print("\n" + "="*70)
    print("📈 监控摘要")
    print("="*70)
    
    for pid, mem in baseline.items():
        peak = max_memory[pid]
        increase = peak - mem
        print(f"PID {pid}:")
        print(f"  基线: {mem:.2f} MB")
        print(f"  峰值: {peak:.2f} MB")
        print(f"  增长: +{increase:.2f} MB ({increase/mem*100:.1f}%)")
    
    print("="*70)


def compare_before_after():
    """对比优化前后的内存快照"""
    print("\n" + "="*70)
    print("📸 内存快照对比工具")
    print("="*70)
    print("\n操作步骤：")
    print("1. 在优化前执行某个操作（如点击客单价异常卡片）")
    print("2. 按Enter记录内存快照")
    print("3. 重启看板后执行相同操作")
    print("4. 再次按Enter记录快照并对比")
    print("="*70 + "\n")
    
    snapshots = []
    
    for i in range(2):
        label = "优化前" if i == 0 else "优化后"
        input(f"准备记录 {label} 快照，按Enter继续...")
        
        total_memory = 0
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                if 'python' in proc.info['name'].lower():
                    mem_mb = proc.info['memory_info'].rss / 1024 / 1024
                    total_memory += mem_mb
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        snapshots.append({
            'label': label,
            'memory': total_memory,
            'time': datetime.now()
        })
        
        print(f"✅ {label} 内存: {total_memory:.2f} MB\n")
    
    # 对比
    diff = snapshots[1]['memory'] - snapshots[0]['memory']
    percent = (diff / snapshots[0]['memory']) * 100
    
    print("="*70)
    print("📊 对比结果")
    print("="*70)
    print(f"优化前: {snapshots[0]['memory']:.2f} MB")
    print(f"优化后: {snapshots[1]['memory']:.2f} MB")
    print(f"差异:   {diff:+.2f} MB ({percent:+.1f}%)")
    
    if diff < -10:
        print("🎉 优化效果显著！内存占用明显下降")
    elif diff < 0:
        print("✅ 有优化效果")
    else:
        print("⚠️  内存占用增加，可能需要进一步优化")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔧 内存监控工具")
    print("="*70)
    print("\n选择模式：")
    print("1. 实时监控 (持续监控，Ctrl+C停止)")
    print("2. 定时监控 (60秒)")
    print("3. 快照对比 (手动对比优化前后)")
    print("="*70)
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "1":
        monitor_dashboard_memory(interval=3, duration=0)
    elif choice == "2":
        monitor_dashboard_memory(interval=3, duration=60)
    elif choice == "3":
        compare_before_after()
    else:
        print("\n⚡ 默认运行实时监控...\n")
        monitor_dashboard_memory(interval=3, duration=0)
