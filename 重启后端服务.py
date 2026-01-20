"""
重启后端服务
"""
import subprocess
import time
import requests
import psutil
import sys

print("=" * 80)
print("重启后端服务")
print("=" * 80)

# 1. 查找并停止占用8080端口的进程
print("\n步骤1: 查找占用8080端口的进程...")
killed_any = False
for proc in psutil.process_iter(['pid', 'name']):
    try:
        # 获取进程的连接信息
        connections = proc.connections()
        for conn in connections:
            if hasattr(conn, 'laddr') and conn.laddr.port == 8080:
                print(f"找到进程: PID={proc.pid}, Name={proc.name()}")
                print(f"正在停止进程 {proc.pid}...")
                proc.kill()
                killed_any = True
                print(f"✅ 进程 {proc.pid} 已停止")
                break
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

if not killed_any:
    print("⚠️ 未找到占用8080端口的进程")

# 等待端口释放
print("\n等待端口释放...")
time.sleep(2)

# 2. 启动后端服务
print("\n步骤2: 启动后端服务...")
print("提示: 后端服务将在后台运行")
print("如需查看日志，请手动运行: python backend/app/main.py")
print()

# 注意：这里不实际启动服务，因为需要在虚拟环境中运行
print("⚠️ 请手动启动后端服务:")
print("   cd 订单数据看板/订单数据看板/O2O-Analysis")
print("   .venv\\Scripts\\activate")
print("   python backend/app/main.py")
print()
print("或者在已激活虚拟环境的终端中运行:")
print("   python backend/app/main.py")

print()
print("=" * 80)
print("完成")
print("=" * 80)
