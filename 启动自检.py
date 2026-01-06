#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动自检模块
在看板启动时自动运行，检测关键模块状态
"""

import sys
from typing import List, Tuple, Callable, Optional


class StartupCheck:
    """启动自检"""
    
    def __init__(self):
        self.checks = []
        self.results = []
        self.failed_checks = []
    
    def add_check(
        self, 
        name: str, 
        check_func: Callable, 
        critical: bool = False,
        fix_hint: Optional[str] = None
    ):
        """
        添加检查项
        
        Args:
            name: 检查项名称
            check_func: 检查函数，返回(bool, str)，bool表示是否通过，str是详细信息
            critical: 是否关键（关键检查失败会阻止启动）
            fix_hint: 修复提示
        """
        self.checks.append({
            'name': name,
            'func': check_func,
            'critical': critical,
            'fix_hint': fix_hint
        })
    
    def run(self, verbose: bool = True) -> bool:
        """
        运行所有检查
        
        Args:
            verbose: 是否显示详细信息
            
        Returns:
            是否全部通过（或非关键检查失败）
        """
        if verbose:
            print("\n" + "=" * 80)
            print(" 🔍 系统启动自检")
            print("=" * 80)
        
        all_passed = True
        critical_failed = False
        
        for i, check in enumerate(self.checks, 1):
            if verbose:
                print(f"\n[{i}/{len(self.checks)}] {check['name']}...")
            
            try:
                passed, message = check['func']()
                
                if passed:
                    if verbose:
                        print(f"   ✅ {message}")
                    self.results.append({
                        'name': check['name'],
                        'status': 'passed',
                        'message': message
                    })
                else:
                    status_icon = "❌" if check['critical'] else "⚠️"
                    if verbose:
                        print(f"   {status_icon} {message}")
                        if check['fix_hint']:
                            print(f"   💡 修复建议: {check['fix_hint']}")
                    
                    self.results.append({
                        'name': check['name'],
                        'status': 'failed',
                        'message': message,
                        'critical': check['critical'],
                        'fix_hint': check['fix_hint']
                    })
                    
                    self.failed_checks.append(check['name'])
                    
                    if check['critical']:
                        critical_failed = True
                    
                    all_passed = False
                    
            except Exception as e:
                status_icon = "❌" if check['critical'] else "⚠️"
                if verbose:
                    print(f"   {status_icon} 检查失败: {e}")
                
                self.results.append({
                    'name': check['name'],
                    'status': 'error',
                    'message': str(e),
                    'critical': check['critical']
                })
                
                self.failed_checks.append(check['name'])
                
                if check['critical']:
                    critical_failed = True
                
                all_passed = False
        
        # 打印总结
        if verbose:
            self._print_summary(critical_failed)
        
        return not critical_failed
    
    def _print_summary(self, critical_failed: bool):
        """打印总结"""
        print("\n" + "=" * 80)
        print(" 📊 自检总结")
        print("=" * 80)
        
        passed_count = sum(1 for r in self.results if r['status'] == 'passed')
        failed_count = len(self.failed_checks)
        
        print(f"\n   通过: {passed_count}/{len(self.checks)}")
        
        if failed_count > 0:
            print(f"   失败: {failed_count}/{len(self.checks)}")
            print(f"\n   失败项目:")
            for result in self.results:
                if result['status'] != 'passed':
                    critical_mark = " [关键]" if result.get('critical') else ""
                    print(f"      - {result['name']}{critical_mark}")
                    if result.get('fix_hint'):
                        print(f"        💡 {result['fix_hint']}")
        
        if critical_failed:
            print(f"\n   ❌ 关键检查失败，系统无法启动")
            print(f"   请修复上述问题后重试")
        elif failed_count > 0:
            print(f"\n   ⚠️  部分检查失败，系统可以启动但功能受限")
        else:
            print(f"\n   ✅ 所有检查通过，系统正常")
        
        print("=" * 80 + "\n")


# =============================================================================
# 预定义检查函数
# =============================================================================

def check_redis_cache() -> Tuple[bool, str]:
    """检查Redis缓存"""
    try:
        # 1. 检查Redis服务
        try:
            import redis
        except ImportError:
            return False, "Redis模块未安装"
        
        try:
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
            r.ping()
        except redis.ConnectionError:
            return False, "Redis服务未启动（Memurai未运行）"
        except Exception as e:
            return False, f"Redis连接失败: {e}"
        
        # 2. 检查缓存管理器（使用子进程避免导入问题）
        import subprocess
        import sys
        
        check_script = """
import sys
try:
    from redis_cache_manager import REDIS_CACHE_MANAGER
    if REDIS_CACHE_MANAGER is None:
        print("NOT_INITIALIZED")
        sys.exit(1)
    if not REDIS_CACHE_MANAGER.enabled:
        print("NOT_ENABLED")
        sys.exit(1)
    
    # 测试基本操作
    test_key = '_startup_check_test'
    REDIS_CACHE_MANAGER.set(test_key, 'test', ttl=10)
    value = REDIS_CACHE_MANAGER.get(test_key)
    REDIS_CACHE_MANAGER.delete(test_key)
    
    if value != 'test':
        print("TEST_FAILED")
        sys.exit(1)
    
    # 获取统计信息
    stats = REDIS_CACHE_MANAGER.get_stats()
    print(f"OK:{stats.get('total_keys', 0)}:{stats.get('hit_rate', 0)}")
    sys.exit(0)
except ImportError as e:
    print(f"IMPORT_ERROR:{e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR:{e}")
    sys.exit(1)
"""
        
        try:
            result = subprocess.run(
                [sys.executable, '-c', check_script],
                capture_output=True,
                text=True,
                timeout=10,
                cwd='.'
            )
            
            output = result.stdout.strip()
            
            if result.returncode == 0 and output.startswith('OK:'):
                parts = output.split(':')
                if len(parts) >= 3:
                    keys = parts[1]
                    hit_rate = parts[2]
                    return True, f"Redis缓存正常（{keys}个键，命中率{hit_rate}%）"
                else:
                    return True, "Redis缓存正常"
            elif output == "NOT_INITIALIZED":
                return False, "Redis缓存管理器未初始化"
            elif output == "NOT_ENABLED":
                return False, "Redis缓存管理器已初始化但未启用"
            elif output == "TEST_FAILED":
                return False, "Redis缓存读写测试失败"
            elif output.startswith("IMPORT_ERROR:"):
                return False, f"缓存管理器模块导入失败"
            elif output.startswith("ERROR:"):
                return False, "Redis缓存检查失败"
            else:
                return False, f"Redis缓存检查失败（未知错误）"
                
        except subprocess.TimeoutExpired:
            return False, "Redis缓存检查超时"
        except Exception as e:
            return False, f"Redis缓存检查失败: {e}"
        
    except Exception as e:
        return False, f"Redis检查异常: {e}"


def check_database() -> Tuple[bool, str]:
    """检查数据库连接"""
    try:
        from sqlalchemy import create_engine, text
        
        # 尝试导入数据库配置
        try:
            from database.connection import DATABASE_URL
        except ImportError:
            return False, "数据库配置模块未找到"
        
        engine = create_engine(
            DATABASE_URL.replace('postgresql://', 'postgresql+pg8000://'),
            pool_pre_ping=True,
            connect_args={'timeout': 5}
        )
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM orders"))
            count = result.scalar()
            
            if count is None:
                return False, "数据库查询失败"
            
            return True, f"数据库连接正常（{count:,}条订单）"
    
    except ImportError as e:
        return False, f"缺少必需模块: {e}"
    except Exception as e:
        error_msg = str(e)
        # 简化错误信息
        if "does not exist" in error_msg or "不存在" in error_msg:
            return False, "数据库未启动或连接失败"
        elif "timeout" in error_msg.lower():
            return False, "数据库连接超时"
        else:
            return False, f"数据库连接失败"


def check_python_version() -> Tuple[bool, str]:
    """检查Python版本"""
    import sys
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        return False, f"Python版本过低（{version.major}.{version.minor}），需要3.8+）"
    
    return True, f"Python版本正常（{version.major}.{version.minor}.{version.micro}）"


def check_required_packages() -> Tuple[bool, str]:
    """检查必需的包"""
    required = [
        ('dash', 'Dash'),
        ('pandas', 'Pandas'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('redis', 'Redis'),
        ('pg8000', 'pg8000'),
        ('plotly', 'Plotly')
    ]
    
    missing = []
    for package, display_name in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(display_name)
    
    if missing:
        return False, f"缺少必需包: {', '.join(missing)}"
    
    return True, f"所有必需包已安装（{len(required)}个）"


def check_data_files() -> Tuple[bool, str]:
    """检查数据文件"""
    import os
    
    data_dir = '实际数据'
    if not os.path.exists(data_dir):
        return False, f"数据目录不存在: {data_dir}"
    
    files = [f for f in os.listdir(data_dir) if f.endswith(('.xlsx', '.xls', '.csv'))]
    
    if len(files) == 0:
        return False, f"数据目录为空: {data_dir}"
    
    return True, f"数据文件正常（{len(files)}个文件）"


def check_disk_space() -> Tuple[bool, str]:
    """检查磁盘空间"""
    import shutil
    
    try:
        stat = shutil.disk_usage('.')
        free_gb = stat.free / (1024**3)
        
        if free_gb < 1:
            return False, f"磁盘空间不足（剩余{free_gb:.1f}GB）"
        
        return True, f"磁盘空间充足（剩余{free_gb:.1f}GB）"
    except Exception as e:
        return False, f"磁盘空间检查失败: {e}"


def check_memory() -> Tuple[bool, str]:
    """检查内存"""
    try:
        import psutil
        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024**3)
        
        if available_gb < 1:
            return False, f"可用内存不足（剩余{available_gb:.1f}GB）"
        
        return True, f"可用内存充足（剩余{available_gb:.1f}GB）"
    except ImportError:
        return True, "psutil未安装，跳过内存检查"
    except Exception as e:
        return False, f"内存检查失败: {e}"


# =============================================================================
# 预定义自检配置
# =============================================================================

def create_standard_checks() -> StartupCheck:
    """创建标准自检配置"""
    checker = StartupCheck()
    
    # 关键检查（失败会阻止启动）
    checker.add_check(
        name="Python版本",
        check_func=check_python_version,
        critical=True,
        fix_hint="请升级到Python 3.8或更高版本"
    )
    
    checker.add_check(
        name="必需包",
        check_func=check_required_packages,
        critical=True,
        fix_hint="运行: pip install -r requirements.txt"
    )
    
    checker.add_check(
        name="数据库连接",
        check_func=check_database,
        critical=True,
        fix_hint="运行: .\\启动数据库.ps1"
    )
    
    # 非关键检查（失败不阻止启动）
    checker.add_check(
        name="Redis缓存",
        check_func=check_redis_cache,
        critical=False,
        fix_hint="运行: Get-Service Memurai | Start-Service"
    )
    
    checker.add_check(
        name="数据文件",
        check_func=check_data_files,
        critical=False,
        fix_hint="请将Excel数据文件放入'实际数据'目录"
    )
    
    checker.add_check(
        name="磁盘空间",
        check_func=check_disk_space,
        critical=False,
        fix_hint="请清理磁盘空间"
    )
    
    checker.add_check(
        name="可用内存",
        check_func=check_memory,
        critical=False,
        fix_hint="请关闭其他程序释放内存"
    )
    
    return checker


# =============================================================================
# 快速使用接口
# =============================================================================

def run_startup_check(verbose: bool = True) -> bool:
    """
    运行标准启动自检
    
    Args:
        verbose: 是否显示详细信息
        
    Returns:
        是否可以启动（关键检查全部通过）
    """
    checker = create_standard_checks()
    return checker.run(verbose=verbose)


# =============================================================================
# 命令行接口
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='系统启动自检')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式（只显示失败项）')
    
    args = parser.parse_args()
    
    success = run_startup_check(verbose=not args.quiet)
    
    sys.exit(0 if success else 1)
