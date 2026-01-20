"""
停止所有占用8080端口的后端服务
"""
import subprocess
import time
import sys

print("=" * 80)
print("停止后端服务")
print("=" * 80)
print()

# 查找占用8080端口的进程
print("查找占用8080端口的进程...")
try:
    result = subprocess.run(
        ['netstat', '-ano'],
        capture_output=True,
        text=True,
        encoding='gbk'
    )
    
    lines = result.stdout.split('\n')
    pids = set()
    
    for line in lines:
        if ':8080' in line and 'LISTENING' in line:
            parts = line.split()
            if parts:
                pid = parts[-1]
                try:
                    pids.add(int(pid))
                except ValueError:
                    pass
    
    if pids:
        print(f"找到 {len(pids)} 个进程: {pids}")
        print()
        
        for pid in pids:
            print(f"停止进程 PID={pid}...")
            try:
                subprocess.run(
                    ['taskkill', '/F', '/PID', str(pid)],
                    capture_output=True,
                    text=True,
                    encoding='gbk'
                )
                print(f"✅ 进程 {pid} 已停止")
            except Exception as e:
                print(f"⚠️ 停止进程 {pid} 失败: {e}")
        
        print()
        print("等待端口释放...")
        time.sleep(2)
        
        # 再次检查
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            encoding='gbk'
        )
        
        still_running = False
        for line in result.stdout.split('\n'):
            if ':8080' in line and 'LISTENING' in line:
                still_running = True
                break
        
        if still_running:
            print("⚠️ 端口8080仍被占用，可能需要手动停止")
        else:
            print("✅ 端口8080已释放")
    else:
        print("⚠️ 未找到占用8080端口的进程")
        
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("完成")
print("=" * 80)
print()
print("下一步: 启动后端服务")
print("  方法1: 运行 启动后端.bat")
print("  方法2: 手动运行以下命令:")
print("    cd 订单数据看板\\订单数据看板\\O2O-Analysis")
print("    .venv\\Scripts\\activate")
print("    python backend/app/main.py")
