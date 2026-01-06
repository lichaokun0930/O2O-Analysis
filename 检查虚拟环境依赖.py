#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查虚拟环境中的依赖安装情况
"""

import sys
import io

# 解决Windows PowerShell下emoji输出乱码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("="*70)
print("  虚拟环境依赖检查")
print("="*70)
print()

# 定义关键依赖包
CRITICAL_PACKAGES = {
    # V8.4 生产级新增
    'waitress': '生产服务器 (30-200人并发)',
    'psutil': '系统监控 (CPU/内存)',
    
    # 核心框架
    'dash': 'Web框架',
    'dash_bootstrap_components': 'UI组件',
    'plotly': '图表库',
    'pandas': '数据处理',
    'numpy': '数值计算',
    
    # 数据库
    'sqlalchemy': '数据库ORM',
    'psycopg2': 'PostgreSQL驱动',
    'alembic': '数据库迁移',
    
    # 缓存
    'redis': 'Redis客户端',
    'flask_caching': 'Flask缓存',
    
    # 可选但重要
    'dash_echarts': 'ECharts图表',
    'openpyxl': 'Excel读写',
}

OPTIONAL_PACKAGES = {
    'dash_mantine_components': 'Mantine UI组件',
    'dash_iconify': '图标库',
    'dash_ag_grid': 'AG Grid表格',
    'scikit_learn': '机器学习',
    'google.generativeai': 'Google AI',
    'openai': 'OpenAI API',
}

def check_package(package_name, description):
    """检查单个包是否安装"""
    try:
        # 特殊处理某些包名
        import_name = package_name
        if package_name == 'dash_bootstrap_components':
            import_name = 'dash_bootstrap_components'
        elif package_name == 'dash_echarts':
            import_name = 'dash_echarts'
        elif package_name == 'flask_caching':
            import_name = 'flask_caching'
        elif package_name == 'scikit_learn':
            import_name = 'sklearn'
        elif package_name == 'google.generativeai':
            import_name = 'google.generativeai'
        
        module = __import__(import_name)
        
        # 尝试获取版本
        version = 'unknown'
        if hasattr(module, '__version__'):
            version = module.__version__
        elif hasattr(module, 'VERSION'):
            version = module.VERSION
        
        return True, version
    except ImportError:
        return False, None
    except Exception as e:
        return False, str(e)

# 检查关键依赖
print("🔍 检查关键依赖 (必须安装)")
print("-" * 70)

critical_missing = []
critical_installed = []

for package, desc in CRITICAL_PACKAGES.items():
    installed, version = check_package(package, desc)
    
    if installed:
        status = "✅"
        critical_installed.append(package)
        version_str = f"({version})" if version != 'unknown' else ""
        print(f"{status} {package:30s} {version_str:15s} - {desc}")
    else:
        status = "❌"
        critical_missing.append(package)
        print(f"{status} {package:30s} {'未安装':15s} - {desc}")

print()
print("🔍 检查可选依赖 (增强功能)")
print("-" * 70)

optional_missing = []
optional_installed = []

for package, desc in OPTIONAL_PACKAGES.items():
    installed, version = check_package(package, desc)
    
    if installed:
        status = "✅"
        optional_installed.append(package)
        version_str = f"({version})" if version != 'unknown' else ""
        print(f"{status} {package:30s} {version_str:15s} - {desc}")
    else:
        status = "⚠️"
        optional_missing.append(package)
        print(f"{status} {package:30s} {'未安装':15s} - {desc}")

# 总结
print()
print("="*70)
print("  检查总结")
print("="*70)
print()

total_critical = len(CRITICAL_PACKAGES)
installed_critical = len(critical_installed)
total_optional = len(OPTIONAL_PACKAGES)
installed_optional = len(optional_installed)

print(f"📊 关键依赖: {installed_critical}/{total_critical} 已安装")
print(f"📊 可选依赖: {installed_optional}/{total_optional} 已安装")
print()

if critical_missing:
    print("❌ 缺少关键依赖:")
    for pkg in critical_missing:
        desc = CRITICAL_PACKAGES[pkg]
        print(f"   • {pkg} - {desc}")
    print()
    print("🔧 安装命令:")
    print(f"   pip install {' '.join(critical_missing)}")
    print()
elif installed_critical == total_critical:
    print("✅ 所有关键依赖已安装！")
    print()

if optional_missing:
    print("⚠️ 缺少可选依赖 (不影响核心功能):")
    for pkg in optional_missing:
        desc = OPTIONAL_PACKAGES[pkg]
        print(f"   • {pkg} - {desc}")
    print()
    print("🔧 安装命令 (可选):")
    print(f"   pip install {' '.join(optional_missing)}")
    print()

# 特别提示
print("="*70)
print("  特别提示")
print("="*70)
print()

if 'waitress' in critical_missing:
    print("⚠️ waitress 未安装:")
    print("   • 影响: 无法使用生产服务器，只能用Flask开发服务器")
    print("   • 后果: 仅支持5-10人并发，不适合生产环境")
    print("   • 安装: pip install waitress")
    print()

if 'psutil' in critical_missing:
    print("⚠️ psutil 未安装:")
    print("   • 影响: 系统监控面板无法显示")
    print("   • 后果: 无法监控CPU、内存、Redis状态")
    print("   • 安装: pip install psutil")
    print()

if 'redis' in critical_missing:
    print("⚠️ redis 未安装:")
    print("   • 影响: 无法使用Redis缓存")
    print("   • 后果: 性能大幅下降，响应时间增加")
    print("   • 安装: pip install redis")
    print()

if not critical_missing:
    print("✅ 所有关键依赖已就绪，可以启动看板！")
    print()
    print("📋 下一步:")
    print("   1. 运行: .\\启动看板-调试模式.ps1")
    print("   2. 访问: http://localhost:8051")
    print("   3. 查看监控面板和系统状态")

print()
print("="*70)
