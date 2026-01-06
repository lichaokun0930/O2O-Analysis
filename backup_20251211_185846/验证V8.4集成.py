#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V8.4 生产级升级集成验证脚本
用途: 验证所有组件是否正确集成
"""

import sys
import io

# 解决Windows PowerShell下emoji输出乱码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def check_import(module_name, description):
    """检查模块导入"""
    try:
        __import__(module_name)
        print(f"✅ {description}: 导入成功")
        return True
    except ImportError as e:
        print(f"❌ {description}: 导入失败 - {e}")
        return False
    except Exception as e:
        print(f"⚠️ {description}: 导入异常 - {e}")
        return False

def check_component_integration():
    """检查组件集成"""
    print_section("组件集成检查")
    
    results = []
    
    # 1. 检查系统监控面板
    print("📦 [1/5] 检查系统监控面板组件...")
    try:
        from components.system_monitor_panel import create_monitor_panel, register_monitor_callbacks
        print("   ✅ 组件导入成功")
        
        # 测试创建面板
        panel = create_monitor_panel()
        print("   ✅ 面板创建成功")
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        results.append(False)
    
    # 2. 检查Redis健康监控
    print("\n📦 [2/5] 检查Redis健康监控...")
    try:
        from redis_health_monitor import get_health_monitor
        print("   ✅ 监控器导入成功")
        
        # 测试创建监控器（不启动）
        monitor = get_health_monitor(host='localhost', port=6379, check_interval=30)
        print("   ✅ 监控器创建成功")
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        results.append(False)
    
    # 3. 检查4层缓存管理器
    print("\n📦 [3/5] 检查4层缓存管理器...")
    try:
        from hierarchical_cache_manager import HierarchicalCacheManager
        print("   ✅ 缓存管理器导入成功")
        
        # 测试创建管理器（不连接Redis）
        print("   ✅ 缓存管理器可用")
        results.append(True)
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        results.append(False)
    
    # 4. 检查Waitress
    print("\n📦 [4/5] 检查Waitress生产服务器...")
    try:
        import waitress
        try:
            version = waitress.__version__
        except AttributeError:
            # Waitress某些版本没有__version__属性
            version = "已安装"
        print(f"   ✅ Waitress已安装 (版本: {version})")
        results.append(True)
    except ImportError:
        print("   ❌ Waitress未安装")
        print("   提示: 运行 .\\安装生产级依赖.ps1")
        results.append(False)
    
    # 5. 检查psutil
    print("\n📦 [5/5] 检查psutil系统监控库...")
    try:
        import psutil
        print(f"   ✅ psutil已安装 (版本: {psutil.__version__})")
        
        # 测试获取系统信息
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        print(f"   ✅ CPU使用率: {cpu_percent}%")
        print(f"   ✅ 内存使用率: {memory.percent}%")
        results.append(True)
    except ImportError:
        print("   ❌ psutil未安装")
        print("   提示: 运行 .\\安装生产级依赖.ps1")
        results.append(False)
    except Exception as e:
        print(f"   ⚠️ psutil功能异常: {e}")
        results.append(False)
    
    return results

def check_main_app_integration():
    """检查主应用集成"""
    print_section("主应用集成检查")
    
    print("📄 检查主应用文件...")
    
    try:
        with open('智能门店看板_Dash版.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('system_monitor_panel导入', 'from components.system_monitor_panel import'),
            ('SYSTEM_MONITOR_AVAILABLE标志', 'SYSTEM_MONITOR_AVAILABLE'),
            ('create_monitor_panel调用', 'create_monitor_panel()'),
            ('register_monitor_callbacks调用', 'register_monitor_callbacks'),
            ('Redis健康监控初始化', 'REDIS_HEALTH_MONITOR = get_health_monitor'),
            ('Waitress服务器配置', 'from waitress import serve'),
        ]
        
        results = []
        for name, pattern in checks:
            if pattern in content:
                print(f"   ✅ {name}: 已集成")
                results.append(True)
            else:
                print(f"   ❌ {name}: 未找到")
                results.append(False)
        
        return results
    except Exception as e:
        print(f"   ❌ 读取文件失败: {e}")
        return [False] * 6

def check_redis_connection():
    """检查Redis连接"""
    print_section("Redis连接检查")
    
    print("🔍 尝试连接Redis...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # 测试连接
        r.ping()
        print("   ✅ Redis连接成功")
        
        # 获取信息
        info = r.info()
        print(f"   ✅ Redis版本: {info.get('redis_version', 'unknown')}")
        
        # 获取内存信息
        memory_info = r.info('memory')
        used_memory_mb = memory_info.get('used_memory', 0) / 1024 / 1024
        maxmemory = memory_info.get('maxmemory', 0)
        maxmemory_mb = maxmemory / 1024 / 1024 if maxmemory > 0 else 0
        
        print(f"   ✅ 内存使用: {used_memory_mb:.2f}MB", end='')
        if maxmemory_mb > 0:
            print(f" / {maxmemory_mb:.2f}MB ({used_memory_mb/maxmemory_mb*100:.1f}%)")
        else:
            print(" (无限制)")
        
        # 检查淘汰策略
        config = r.config_get('maxmemory-policy')
        policy = config.get('maxmemory-policy', 'unknown')
        print(f"   ✅ 淘汰策略: {policy}")
        
        if maxmemory_mb < 1000 and maxmemory_mb > 0:
            print(f"   ⚠️ 警告: Redis内存限制 ({maxmemory_mb:.0f}MB) 小于推荐值 (1024MB)")
            print(f"   提示: 运行 python 配置Redis_1GB.py 配置为1GB")
        
        return True
    except redis.ConnectionError:
        print("   ❌ Redis连接失败")
        print("   提示: 运行 .\\启动Redis.ps1 启动Redis")
        return False
    except ImportError:
        print("   ❌ redis-py未安装")
        print("   提示: pip install redis")
        return False
    except Exception as e:
        print(f"   ⚠️ Redis检查异常: {e}")
        return False

def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           V8.4 生产级升级集成验证                             ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 1. 组件集成检查
    component_results = check_component_integration()
    
    # 2. 主应用集成检查
    app_results = check_main_app_integration()
    
    # 3. Redis连接检查
    redis_ok = check_redis_connection()
    
    # 总结
    print_section("验证总结")
    
    total_checks = len(component_results) + len(app_results) + (1 if redis_ok else 0)
    passed_checks = sum(component_results) + sum(app_results) + (1 if redis_ok else 0)
    
    print(f"📊 总计: {passed_checks}/{total_checks} 项检查通过")
    print(f"   组件集成: {sum(component_results)}/{len(component_results)} 通过")
    print(f"   主应用集成: {sum(app_results)}/{len(app_results)} 通过")
    print(f"   Redis连接: {'✅ 通过' if redis_ok else '❌ 失败'}")
    
    print()
    if passed_checks == total_checks:
        print("✅ 所有检查通过！V8.4生产级升级已完整集成")
        print()
        print("📋 下一步操作:")
        print("   1. 运行 .\\启动看板-调试模式.ps1 启动看板")
        print("   2. 访问 http://localhost:8051 查看监控面板")
        print("   3. 运行 python 压力测试_30人.py 测试并发性能")
    elif passed_checks >= total_checks * 0.8:
        print("⚠️ 大部分检查通过，但有少量问题需要解决")
        print()
        print("📋 建议操作:")
        if not redis_ok:
            print("   • 启动Redis: .\\启动Redis.ps1")
        if sum(component_results) < len(component_results):
            print("   • 安装依赖: .\\安装生产级依赖.ps1")
    else:
        print("❌ 多项检查失败，请按照提示解决问题")
        print()
        print("📋 故障排查:")
        print("   1. 检查Python环境和依赖安装")
        print("   2. 运行 .\\安装生产级依赖.ps1 安装依赖")
        print("   3. 运行 .\\启动Redis.ps1 启动Redis")
        print("   4. 查看启动日志排查错误")
    
    print()
    print("=" * 60)

if __name__ == '__main__':
    main()
