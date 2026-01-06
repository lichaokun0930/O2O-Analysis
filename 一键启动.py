#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
订单数据看板 - 一键启动脚本
支持开发模式和生产模式
"""

import os
import sys
import subprocess
import socket
import time
import signal
from pathlib import Path

# ==========================================
# 配置
# ==========================================
FRONTEND_DEV_PORT = 5173
FRONTEND_PROD_PORT = 4173
BACKEND_PORT = 8080

# 颜色定义
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def colored(text, color):
    """带颜色的文本"""
    return f"{color}{text}{Colors.ENDC}"

def print_ok(msg):
    print(colored(f"[OK] {msg}", Colors.GREEN))

def print_warn(msg):
    print(colored(f"[WARN] {msg}", Colors.YELLOW))

def print_error(msg):
    print(colored(f"[ERROR] {msg}", Colors.RED))

def print_info(msg):
    print(colored(f"[*] {msg}", Colors.CYAN))

def print_header(title):
    print()
    print(colored("=" * 60, Colors.CYAN))
    print(colored(f"  {title}", Colors.BOLD))
    print(colored("=" * 60, Colors.CYAN))

# ==========================================
# 工具函数
# ==========================================
def get_project_root():
    """获取项目根目录"""
    return Path(__file__).parent.absolute()

def find_python():
    """查找虚拟环境中的 Python"""
    root = get_project_root()
    
    # 查找虚拟环境
    venv_paths = [
        root.parent / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "Scripts" / "python.exe",
    ]
    
    for venv_python in venv_paths:
        if venv_python.exists():
            return str(venv_python)
    
    return sys.executable

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    """终止占用指定端口的进程"""
    try:
        if sys.platform == 'win32':
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True, capture_output=True, text=True
            )
            for line in result.stdout.strip().split('\n'):
                if 'LISTENING' in line:
                    parts = line.split()
                    pid = parts[-1]
                    subprocess.run(f'taskkill /PID {pid} /F', shell=True, 
                                 capture_output=True)
                    return True
    except:
        pass
    return False

# ==========================================
# 环境检查
# ==========================================
def check_redis():
    """检查 Redis/Memurai 服务"""
    print_info("检查 Redis 缓存服务 ...")
    try:
        import redis
        r = redis.Redis()
        r.ping()
        print_ok("Redis 已运行 (Memurai)")
        return True
    except:
        # 尝试启动 Memurai 服务
        try:
            subprocess.run('net start Memurai', shell=True, 
                         capture_output=True, check=True)
            time.sleep(2)
            import redis
            r = redis.Redis()
            r.ping()
            print_ok("Redis 已启动 (Memurai)")
            return True
        except:
            print_warn("Redis 未运行，缓存功能不可用")
            return False

def check_postgresql():
    """检查 PostgreSQL 数据库"""
    print_info("检查 PostgreSQL 数据库 ...")
    
    try:
        # 使用老版本相同的连接方式
        sys.path.insert(0, str(get_project_root()))
        from database.connection import engine, check_connection
        from sqlalchemy import text
        
        result = check_connection()
        if result['connected']:
            print_ok("PostgreSQL 数据库已连接")
            
            # 获取数据统计
            try:
                with engine.connect() as conn:
                    count = conn.execute(text("SELECT COUNT(*) FROM orders")).scalar()
                    print(colored(f"    订单数据: {count:,} 条", Colors.CYAN))
            except:
                pass
            
            return True
        else:
            raise Exception(result['message'])
            
    except Exception as e:
        # 尝试启动 PostgreSQL 服务
        print_warn(f"PostgreSQL 未连接: {e}")
        print_info("尝试启动 PostgreSQL 服务 ...")
        
        services = ['postgresql-x64-16', 'postgresql-x64-15', 'postgresql-x64-14', 'postgresql']
        for svc in services:
            try:
                subprocess.run(f'net start {svc}', shell=True, 
                             capture_output=True, check=True)
                time.sleep(3)
                
                # 重新检查
                from database.connection import check_connection
                if check_connection()['connected']:
                    print_ok(f"PostgreSQL 已启动 ({svc})")
                    return True
            except:
                continue
        
        print_warn("PostgreSQL 启动失败，请手动运行 启动数据库.ps1")
        return False

def check_node():
    """检查 Node.js"""
    try:
        result = subprocess.run(['node', '-v'], capture_output=True, text=True)
        version = result.stdout.strip()
        print_ok(f"Node.js: {version}")
        return True
    except:
        print_error("Node.js 未安装")
        return False

def check_backend_api():
    """检查后端 API 服务"""
    print_info("检查 API 服务 ...")
    if is_port_in_use(BACKEND_PORT):
        print_ok(f"API 服务已运行 (http://localhost:{BACKEND_PORT})")
        return True
    else:
        print_warn(f"API 服务未运行 (端口 {BACKEND_PORT})")
        return False

def check_old_processes():
    """检查并清理旧进程"""
    cleaned = False
    
    if is_port_in_use(FRONTEND_DEV_PORT):
        print_warn(f"端口 {FRONTEND_DEV_PORT} 被占用，正在清理...")
        kill_process_on_port(FRONTEND_DEV_PORT)
        cleaned = True
    
    if is_port_in_use(BACKEND_PORT):
        print_warn(f"端口 {BACKEND_PORT} 被占用，正在清理...")
        kill_process_on_port(BACKEND_PORT)
        cleaned = True
    
    if cleaned:
        time.sleep(2)
        print_ok("旧进程已清理")
    
    return True

# ==========================================
# 启动函数
# ==========================================
def install_frontend_deps():
    """安装前端依赖"""
    root = get_project_root()
    node_modules = root / "frontend" / "node_modules"
    
    if not node_modules.exists():
        print_info("安装前端依赖 ...")
        subprocess.run(['npm', 'install'], cwd=root / "frontend", shell=True)
        print_ok("前端依赖安装完成")

def start_backend_dev():
    """启动后端开发服务器"""
    root = get_project_root()
    python_exe = find_python()
    
    env = os.environ.copy()
    env['ENVIRONMENT'] = 'development'
    env['DEBUG'] = 'true'
    env['LOG_LEVEL'] = 'DEBUG'
    
    cmd = [
        python_exe, '-m', 'uvicorn', 
        'app.main:app',
        '--host', '0.0.0.0',
        '--port', str(BACKEND_PORT),
        '--reload',
        '--reload-dir', 'app',
        '--log-level', 'debug'
    ]
    
    return subprocess.Popen(
        cmd,
        cwd=root / "backend",
        env=env,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )

def start_frontend_dev():
    """启动前端开发服务器"""
    root = get_project_root()
    
    cmd = ['npm', 'run', 'dev', '--', '--port', str(FRONTEND_DEV_PORT)]
    
    return subprocess.Popen(
        cmd,
        cwd=root / "frontend",
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )

def run_dev_mode():
    """运行开发模式"""
    print_header("开发模式 (支持热重载)")
    print(colored("[*] 代码修改后会自动刷新，无需手动重启", Colors.CYAN))
    print()
    
    # 安装依赖
    install_frontend_deps()
    
    # 启动后端
    print_info("启动后端 API 服务器 ...")
    backend_proc = start_backend_dev()
    time.sleep(3)
    
    # 显示访问地址
    print()
    print(f"    本机访问: {colored(f'http://localhost:{FRONTEND_DEV_PORT}', Colors.GREEN)}")
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"    局域网访问: {colored(f'http://{local_ip}:{FRONTEND_DEV_PORT}', Colors.GREEN)}")
    except:
        pass
    print(f"    API 地址: {colored(f'http://localhost:{BACKEND_PORT}', Colors.GREEN)}")
    print(f"    API 文档: {colored(f'http://localhost:{BACKEND_PORT}/docs', Colors.GREEN)}")
    print()
    print(colored("    按 Ctrl+C 停止服务", Colors.YELLOW))
    print(colored("=" * 60, Colors.CYAN))
    print()
    
    # 启动前端（在当前终端运行，这样可以看到 Vite 输出）
    root = get_project_root()
    os.chdir(root / "frontend")
    os.system(f'npm run dev -- --port {FRONTEND_DEV_PORT}')

def run_prod_mode():
    """运行生产模式"""
    print_header("生产模式")
    
    root = get_project_root()
    
    # 构建前端
    print_info("构建前端生产版本 ...")
    result = subprocess.run(['npm', 'run', 'build'], cwd=root / "frontend", shell=True)
    if result.returncode != 0:
        print_error("前端构建失败")
        return
    print_ok("前端构建完成")
    
    # 计算 workers 数量
    workers = min(os.cpu_count() * 2 + 1, 8)
    
    # 启动后端
    print_info(f"启动后端生产服务器 ({workers} workers) ...")
    python_exe = find_python()
    
    env = os.environ.copy()
    env['ENVIRONMENT'] = 'production'
    env['DEBUG'] = 'false'
    
    backend_cmd = [
        python_exe, '-m', 'uvicorn',
        'app.main:app',
        '--host', '0.0.0.0',
        '--port', str(BACKEND_PORT),
        '--workers', str(workers),
        '--log-level', 'info'
    ]
    
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=root / "backend",
        env=env,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )
    
    time.sleep(3)
    
    # 启动前端预览
    print_info("启动前端预览服务器 ...")
    os.chdir(root / "frontend")
    os.system(f'npm run preview -- --port {FRONTEND_PROD_PORT}')

# ==========================================
# 主程序
# ==========================================
def show_menu():
    """显示菜单"""
    print()
    print("  " + "-" * 40)
    print("  1 - 开发模式 (前后端热重载)")
    print("  2 - 生产模式 (构建+多进程)")
    print("  3 - 仅启动后端")
    print("  4 - 仅启动前端")
    print("  5 - 清理旧进程")
    print("  0 - 退出")
    print("  " + "-" * 40)
    print()

def main():
    # 设置控制台编码
    if sys.platform == 'win32':
        os.system('chcp 65001 > nul')
    
    # 切换到项目目录
    os.chdir(get_project_root())
    
    # 显示标题
    print()
    print(colored("=" * 60, Colors.CYAN))
    print(colored("        订单数据看板 - 一键启动", Colors.BOLD))
    print(colored("     Frontend: Vue 3   Backend: FastAPI", Colors.CYAN))
    print(colored("=" * 60, Colors.CYAN))
    print()
    
    # 环境检查
    print(colored(f"    环境: Development", Colors.GREEN))
    print(colored("=" * 60, Colors.CYAN))
    print()
    
    check_redis()
    print()
    check_postgresql()
    print()
    check_node()
    print()
    
    # 检查旧进程
    check_old_processes()
    
    # 显示菜单
    show_menu()
    
    while True:
        try:
            choice = input("请选择 (0-5): ").strip()
            
            if choice == '1':
                run_dev_mode()
                break
            elif choice == '2':
                run_prod_mode()
                break
            elif choice == '3':
                print_info("启动后端服务 ...")
                start_backend_dev()
                print_ok(f"后端已启动: http://localhost:{BACKEND_PORT}")
                input("按回车键退出...")
                break
            elif choice == '4':
                print_info("启动前端服务 ...")
                install_frontend_deps()
                run_dev_mode()
                break
            elif choice == '5':
                check_old_processes()
                show_menu()
            elif choice == '0':
                print("退出")
                break
            else:
                print_warn("无效选项，请重新选择")
                
        except KeyboardInterrupt:
            print("\n退出")
            break

if __name__ == '__main__':
    main()

