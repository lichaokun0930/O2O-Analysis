#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Redis自动启动机制

测试流程:
1. 检查Redis是否运行
2. 如果未运行，自动启动
3. 验证健康状态
4. 测试缓存读写

作者: AI Assistant
版本: V8.2
日期: 2025-12-11
"""

import sys
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))


def test_redis_auto_start():
    """测试Redis自动启动"""
    print("="*80)
    print("Redis自动启动机制测试")
    print("="*80)
    
    # 测试1: 导入Redis管理器
    print("\n[测试1] 导入Redis管理器...")
    try:
        from redis_manager import ensure_redis_running, redis_health_check
        print("✅ 导入成功")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False
    
    # 测试2: 确保Redis运行
    print("\n[测试2] 确保Redis运行...")
    try:
        if ensure_redis_running():
            print("✅ Redis可用")
        else:
            print("❌ Redis不可用")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试3: 健康检查
    print("\n[测试3] 健康检查...")
    try:
        health = redis_health_check()
        print(f"运行状态: {health['running']}")
        print(f"服务地址: {health['host']}:{health['port']}")
        print(f"内存使用: {health['memory']}")
        print(f"键数量: {health['keys']}")
        
        if health['running']:
            print("✅ 健康检查通过")
        else:
            print(f"❌ 健康检查失败: {health.get('error', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False
    
    # 测试4: 缓存读写
    print("\n[测试4] 测试缓存读写...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # 写入测试
        test_key = 'test:auto_start'
        test_value = 'Redis自动启动测试成功!'
        r.setex(test_key, 60, test_value)
        print(f"写入: {test_key} = {test_value}")
        
        # 读取测试
        result = r.get(test_key)
        print(f"读取: {test_key} = {result}")
        
        if result == test_value:
            print("✅ 缓存读写正常")
        else:
            print("❌ 缓存读写异常")
            return False
        
        # 清理测试数据
        r.delete(test_key)
        
    except Exception as e:
        print(f"❌ 缓存测试失败: {e}")
        return False
    
    print("\n" + "="*80)
    print("✅ 所有测试通过!")
    print("="*80)
    return True


def test_background_tasks():
    """测试后台任务"""
    print("\n" + "="*80)
    print("后台任务测试")
    print("="*80)
    
    # 测试1: 导入后台任务模块
    print("\n[测试1] 导入后台任务模块...")
    try:
        from background_tasks import start_background_tasks, get_scheduler_status
        print("✅ 导入成功")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False
    
    # 测试2: 启动后台任务
    print("\n[测试2] 启动后台任务...")
    try:
        scheduler = start_background_tasks()
        print("✅ 后台任务已启动")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试3: 检查调度器状态
    print("\n[测试3] 检查调度器状态...")
    try:
        status = get_scheduler_status()
        print(f"运行状态: {status['running']}")
        print(f"任务列表:")
        for job in status['jobs']:
            print(f"  - {job['name']} (下次运行: {job['next_run']})")
        
        if status['running']:
            print("✅ 调度器运行正常")
        else:
            print("❌ 调度器未运行")
            return False
    except Exception as e:
        print(f"❌ 状态检查失败: {e}")
        return False
    
    print("\n" + "="*80)
    print("✅ 后台任务测试通过!")
    print("="*80)
    return True


def main():
    """主测试流程"""
    print("\n" + "="*80)
    print("V8.2 Redis自动启动 + 后台任务 完整测试")
    print("="*80)
    
    # 步骤1: 测试Redis自动启动
    if not test_redis_auto_start():
        print("\n❌ Redis自动启动测试失败")
        return
    
    # 步骤2: 测试后台任务
    if not test_background_tasks():
        print("\n❌ 后台任务测试失败")
        return
    
    # 测试完成
    print("\n" + "="*80)
    print("🎉 所有测试通过!")
    print("="*80)
    print("\n下一步:")
    print("1. 启动看板: python 智能门店看板_Dash版.py")
    print("2. 访问: http://localhost:8051")
    print("3. 点击'今日必做'Tab，观察加载时间")
    print("4. 等待5分钟后再次访问，应该<1秒加载")
    print("\n预期效果:")
    print("- 首次访问: 70秒（缓存预热）")
    print("- 后续访问: <1秒（从Redis缓存读取）")
    print("- 用户感知: 0.5秒（骨架屏）+ 1秒（数据）= 1.5秒")
    print("="*80)


if __name__ == "__main__":
    main()
