# -*- coding: utf-8 -*-
"""
V8.1 后台任务测试脚本

测试后台任务调度器是否正常工作
"""

import sys
from pathlib import Path
import time

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

print("="*80)
print("V8.1 后台任务测试")
print("="*80)

# 测试1: 导入后台任务模块
print("\n[测试1] 导入后台任务模块...")
try:
    from background_tasks import (
        start_background_tasks,
        stop_background_tasks,
        get_scheduler_status,
        update_diagnosis_cache
    )
    print("✅ 后台任务模块导入成功")
except Exception as e:
    print(f"❌ 后台任务模块导入失败: {e}")
    sys.exit(1)

# 测试2: 检查APScheduler
print("\n[测试2] 检查APScheduler...")
try:
    import apscheduler
    print(f"✅ APScheduler已安装，版本: {apscheduler.__version__}")
except Exception as e:
    print(f"❌ APScheduler未安装: {e}")
    sys.exit(1)

# 测试3: 检查Redis连接
print("\n[测试3] 检查Redis连接...")
try:
    from redis_cache_manager import REDIS_CACHE_MANAGER
    if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
        print("✅ Redis缓存已启用")
    else:
        print("⚠️ Redis缓存未启用")
except Exception as e:
    print(f"⚠️ Redis检查失败: {e}")

# 测试4: 手动执行一次缓存更新（不启动调度器）
print("\n[测试4] 手动执行缓存更新...")
print("提示: 这将需要70秒左右，请耐心等待...")
try:
    # 注意：这需要GLOBAL_DATA已加载
    print("⚠️ 跳过手动执行（需要完整应用环境）")
    print("   请启动完整应用后观察后台任务日志")
except Exception as e:
    print(f"⚠️ 手动执行失败: {e}")

# 测试5: 测试调度器启动和停止
print("\n[测试5] 测试调度器启动和停止...")
try:
    # 启动调度器
    print("启动调度器...")
    scheduler = start_background_tasks()
    print("✅ 调度器启动成功")
    
    # 获取状态
    status = get_scheduler_status()
    print(f"调度器状态: {'运行中' if status['running'] else '已停止'}")
    print(f"任务数量: {len(status['jobs'])}")
    for job in status['jobs']:
        print(f"  - {job['name']} (下次运行: {job['next_run']})")
    
    # 等待2秒
    print("\n等待2秒...")
    time.sleep(2)
    
    # 停止调度器
    print("停止调度器...")
    stop_background_tasks()
    print("✅ 调度器停止成功")
    
except Exception as e:
    print(f"❌ 调度器测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("🎉 V8.1 后台任务测试完成!")
print("="*80)
print("\n下一步:")
print("1. 运行: python 智能门店看板_Dash版.py")
print("2. 观察控制台输出，应该看到:")
print("   [后台任务] 🚀 启动后台任务调度器...")
print("   [后台任务] ✅ 已添加任务: 更新诊断数据缓存 (每5分钟)")
print("   [后台任务] 🔥 立即执行一次预热缓存...")
print("3. 访问看板，点击'今日必做'Tab")
print("4. 观察加载时间，应该<1秒（如果缓存命中）")
print("\n预期效果:")
print("   首次访问: 70秒（缓存未命中，实时计算）")
print("   后续访问: <1秒（从缓存读取） ⚡⚡⚡")
