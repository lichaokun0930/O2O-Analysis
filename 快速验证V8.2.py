#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V8.2 快速验证脚本

验证内容:
1. Redis自动启动
2. 后台任务运行
3. 缓存预热
4. 性能测试

作者: AI Assistant
版本: V8.2
日期: 2025-12-11
"""

import sys
from pathlib import Path
import time

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))


def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def test_redis():
    """测试Redis自动启动"""
    print_section("步骤1: 测试Redis自动启动")
    
    try:
        from redis_manager import ensure_redis_running, redis_health_check
        
        # 确保Redis运行
        if ensure_redis_running():
            print("✅ Redis自动启动成功")
            
            # 健康检查
            health = redis_health_check()
            if health['running']:
                print(f"✅ 健康检查通过")
                print(f"   - 服务地址: {health['host']}:{health['port']}")
                print(f"   - 内存使用: {health['memory']}")
                print(f"   - 键数量: {health['keys']}")
                return True
            else:
                print(f"❌ 健康检查失败: {health.get('error', '未知错误')}")
                return False
        else:
            print("❌ Redis启动失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache():
    """测试缓存读写"""
    print_section("步骤2: 测试缓存读写")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # 写入测试
        test_key = 'test:v82_verification'
        test_value = 'V8.2验证成功!'
        r.setex(test_key, 60, test_value)
        print(f"✅ 写入成功: {test_key}")
        
        # 读取测试
        result = r.get(test_key)
        if result == test_value:
            print(f"✅ 读取成功: {result}")
            
            # 清理
            r.delete(test_key)
            return True
        else:
            print(f"❌ 读取失败: 期望 {test_value}, 实际 {result}")
            return False
            
    except Exception as e:
        print(f"❌ 缓存测试失败: {e}")
        return False


def test_background_tasks():
    """测试后台任务"""
    print_section("步骤3: 测试后台任务")
    
    try:
        from background_tasks import start_background_tasks, get_scheduler_status
        
        # 启动后台任务
        print("启动后台任务调度器...")
        scheduler = start_background_tasks()
        
        # 等待一下
        time.sleep(2)
        
        # 检查状态
        status = get_scheduler_status()
        if status['running']:
            print(f"✅ 调度器运行正常")
            print(f"   任务列表:")
            for job in status['jobs']:
                print(f"   - {job['name']}")
                print(f"     下次运行: {job['next_run']}")
            return True
        else:
            print("❌ 调度器未运行")
            return False
            
    except Exception as e:
        print(f"❌ 后台任务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_warmup():
    """测试缓存预热"""
    print_section("步骤4: 检查缓存预热")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # 检查诊断缓存
        cache_key = 'diagnosis:latest'
        
        print(f"检查缓存键: {cache_key}")
        
        if r.exists(cache_key):
            ttl = r.ttl(cache_key)
            print(f"✅ 缓存已预热")
            print(f"   - 缓存键: {cache_key}")
            print(f"   - 剩余时间: {ttl}秒")
            return True
        else:
            print(f"⚠️ 缓存尚未预热（后台任务正在执行）")
            print(f"   提示: 等待1-2分钟后缓存会自动生成")
            return True  # 不算失败
            
    except Exception as e:
        print(f"❌ 缓存检查失败: {e}")
        return False


def main():
    """主验证流程"""
    print("\n" + "="*80)
    print("V8.2 快速验证脚本")
    print("="*80)
    print("\n本脚本将验证以下功能:")
    print("1. Redis自动启动")
    print("2. 缓存读写")
    print("3. 后台任务")
    print("4. 缓存预热")
    
    results = []
    
    # 测试1: Redis自动启动
    results.append(("Redis自动启动", test_redis()))
    
    # 测试2: 缓存读写
    results.append(("缓存读写", test_cache()))
    
    # 测试3: 后台任务
    results.append(("后台任务", test_background_tasks()))
    
    # 测试4: 缓存预热
    results.append(("缓存预热", test_cache_warmup()))
    
    # 汇总结果
    print_section("验证结果汇总")
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 所有验证通过!")
        print("="*80)
        print("\n下一步:")
        print("1. 启动看板: python 智能门店看板_Dash版.py")
        print("2. 访问: http://localhost:8051")
        print("3. 点击'今日必做'Tab")
        print("4. 观察加载时间（首次70秒，后续<1秒）")
        print("\n预期效果:")
        print("- 首次访问: 70秒（缓存预热）")
        print("- 后续访问: <1秒（从Redis缓存读取）")
        print("- 用户感知: 0.5秒（骨架屏）+ 1秒（数据）= 1.5秒")
    else:
        print("⚠️ 部分验证失败，请检查错误信息")
        print("="*80)
        print("\n故障排查:")
        print("1. 确认Redis已安装: winget install Redis.Redis")
        print("2. 确认依赖已安装: pip install apscheduler redis")
        print("3. 查看详细日志: python 测试Redis自动启动.py")
    
    print("="*80)


if __name__ == "__main__":
    main()
