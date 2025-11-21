# -*- coding: utf-8 -*-
"""
启动全栈服务 - 自动启动后端API和前端看板
"""

import subprocess
import time
import sys
import os

print("=" * 60)
print("🚀 启动智能门店经营看板 - 全栈服务")
print("=" * 60)

# 1. 测试数据库连接
print("\n[1/3] 测试数据库连接...")
try:
    from database.connection import check_connection
    if check_connection():
        print("✅ 数据库连接正常")
    else:
        print("❌ 数据库连接失败，请检查配置")
        sys.exit(1)
except Exception as e:
    print(f"❌ 数据库测试失败: {e}")
    sys.exit(1)

# 2. 启动后端API
print("\n[2/3] 启动后端 FastAPI 服务...")
print("端口: 8000")
print("文档: http://localhost:8000/docs")

try:
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", 
         "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )
    print("✅ 后端服务已启动 (新窗口)")
    time.sleep(3)  # 等待后端启动
except Exception as e:
    print(f"❌ 后端启动失败: {e}")
    sys.exit(1)

# 3. 启动前端Dash看板
print("\n[3/3] 启动前端 Dash 看板...")
print("端口: 8051")
print("访问: http://localhost:8051")

try:
    # 检查是否存在集成版本的看板
    if os.path.exists("dashboard_integrated.py"):
        dashboard_file = "dashboard_integrated.py"
    else:
        dashboard_file = "智能门店看板_Dash版.py"
    
    print(f"使用看板文件: {dashboard_file}")
    
    frontend_process = subprocess.Popen(
        [sys.executable, dashboard_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )
    print("✅ 前端看板已启动 (新窗口)")
    
except Exception as e:
    print(f"❌ 前端启动失败: {e}")
    backend_process.terminate()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅✅✅ 全栈服务启动成功！ ✅✅✅")
print("=" * 60)
print("\n服务地址:")
print(f"  🌐 前端看板: http://localhost:8051")
print(f"  🔧 后端API:  http://localhost:8000")
print(f"  📖 API文档:  http://localhost:8000/docs")
print("\n按 Ctrl+C 停止所有服务...")

try:
    # 保持运行
    backend_process.wait()
    frontend_process.wait()
except KeyboardInterrupt:
    print("\n\n停止服务...")
    backend_process.terminate()
    frontend_process.terminate()
    print("✅ 服务已停止")
