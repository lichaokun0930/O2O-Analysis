#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试启动日志输出

模拟主程序的启动流程，检查日志是否正确输出

作者: AI Assistant
版本: V8.2
日期: 2025-12-11
"""

import sys
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

print("\n" + "="*80)
print("测试启动日志输出")
print("="*80)

# 测试1: Redis管理器
print("\n[测试1] Redis管理器日志...")
print("-"*80)

try:
    from redis_manager import ensure_redis_running, redis_health_check
    
    # 自动启动Redis（如果未运行）
    if ensure_redis_running():
        # 健康检查
        health = redis_health_check()
        if health['running']:
            print(f"✅ Redis服务正常 - 内存: {health['memory']}, 键数量: {health['keys']}")
        else:
            print(f"⚠️ Redis健康检查失败: {health.get('error', '未知错误')}")
    else:
        print("⚠️ Redis启动失败，缓存功能将不可用")
except Exception as e:
    print(f"⚠️ Redis管理器异常: {e}")
    import traceback
    traceback.print_exc()

# 强制刷新
sys.stdout.flush()
sys.stderr.flush()

# 测试2: 后台任务
print("\n[测试2] 后台任务日志...")
print("-"*80)

try:
    from background_tasks import start_background_tasks
    scheduler = start_background_tasks()
    print("✅ 后台任务调度器已启动 (每5分钟更新缓存)")
except Exception as e:
    print(f"⚠️ 后台任务启动失败: {e}")
    import traceback
    traceback.print_exc()

# 强制刷新
sys.stdout.flush()
sys.stderr.flush()

print("\n" + "="*80)
print("测试完成")
print("="*80)
print("\n如果你能看到上面的所有日志，说明日志输出正常。")
print("如果在启动脚本中看不到这些日志，可能是：")
print("1. 日志被其他输出淹没了")
print("2. PowerShell编码问题导致中文乱码")
print("3. 输出被重定向或缓冲了")
print("\n建议：")
print("1. 使用 python -u 智能门店看板_Dash版.py 直接启动")
print("2. 或者查看启动日志文件")
print("="*80)
