# -*- coding: utf-8 -*-
"""
Redis管理模块 - 自动启动和健康检查

功能:
- 自动检测Redis是否运行
- 自动启动Redis服务
- 健康检查和自动恢复
- 状态监控和告警

作者: AI Assistant
版本: V8.2
日期: 2025-12-11
"""

import subprocess
import time
import sys
import os
from pathlib import Path


class RedisManager:
    """Redis服务管理器"""
    
    def __init__(self, host='localhost', port=6379):
        self.host = host
        self.port = port
        self.redis_process = None
        
    def is_redis_running(self):
        """
        检查Redis是否正在运行
        
        Returns:
            bool: True表示运行中，False表示未运行
        """
        try:
            import redis
            r = redis.Redis(host=self.host, port=self.port, socket_connect_timeout=2)
            r.ping()
            return True
        except Exception:
            return False
    
    def check_memurai_service(self):
        """
        检查Memurai服务是否运行（Windows专用）
        
        Returns:
            dict: {'installed': bool, 'running': bool, 'type': str}
        """
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-Service -Name "Memurai" -ErrorAction SilentlyContinue | Select-Object Status'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if 'Running' in result.stdout:
                return {'installed': True, 'running': True, 'type': 'Memurai'}
            elif result.stdout.strip():
                return {'installed': True, 'running': False, 'type': 'Memurai'}
            else:
                return {'installed': False, 'running': False, 'type': None}
        except Exception:
            return {'installed': False, 'running': False, 'type': None}
    
    def find_redis_executable(self):
        """
        查找Redis可执行文件
        
        Returns:
            str: Redis可执行文件路径，如果未找到返回None
        """
        # 方法1: 检查PATH环境变量
        try:
            result = subprocess.run(
                ['where', 'redis-server'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                redis_path = result.stdout.strip().split('\n')[0]
                return redis_path
        except Exception:
            pass
        
        # 方法2: 检查常见安装位置
        common_paths = [
            r"C:\Program Files\Redis\redis-server.exe",
            r"C:\Redis\redis-server.exe",
            r"C:\Program Files (x86)\Redis\redis-server.exe",
            os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Redis.Redis_*\redis-server.exe")
        ]
        
        for path in common_paths:
            if '*' in path:
                # 处理通配符路径
                import glob
                matches = glob.glob(path)
                if matches:
                    return matches[0]
            elif os.path.exists(path):
                return path
        
        return None
    
    def start_redis(self):
        """
        启动Redis服务
        
        Returns:
            bool: True表示启动成功，False表示启动失败
        """
        print(f"\n{'='*80}")
        print("[Redis管理器] 🚀 正在启动Redis服务...")
        print(f"{'='*80}")
        
        # 检查是否已经运行
        if self.is_redis_running():
            print("[Redis管理器] ✅ Redis已在运行")
            return True
        
        # 查找Redis可执行文件
        redis_exe = self.find_redis_executable()
        
        if not redis_exe:
            print("[Redis管理器] ❌ 未找到Redis可执行文件")
            print("[Redis管理器] 请先安装Redis:")
            print("   方式1: winget install Redis.Redis")
            print("   方式2: choco install redis-64")
            print("   方式3: 手动下载 https://github.com/microsoftarchive/redis/releases")
            return False
        
        print(f"[Redis管理器] 找到Redis: {redis_exe}")
        
        # 启动Redis
        try:
            # 使用CREATE_NO_WINDOW标志在后台启动
            CREATE_NO_WINDOW = 0x08000000
            
            self.redis_process = subprocess.Popen(
                [redis_exe],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=CREATE_NO_WINDOW
            )
            
            print("[Redis管理器] Redis进程已启动，等待服务就绪...")
            
            # 等待Redis启动（最多10秒）
            for i in range(10):
                time.sleep(1)
                if self.is_redis_running():
                    print(f"[Redis管理器] ✅ Redis启动成功! (耗时{i+1}秒)")
                    print(f"[Redis管理器] 服务地址: {self.host}:{self.port}")
                    print(f"[Redis管理器] 进程ID: {self.redis_process.pid}")
                    print(f"{'='*80}\n")
                    return True
                print(f"[Redis管理器] 等待中... ({i+1}/10)")
            
            print("[Redis管理器] ⚠️ Redis启动超时")
            return False
            
        except Exception as e:
            print(f"[Redis管理器] ❌ 启动失败: {e}")
            return False
    
    def ensure_redis_running(self):
        """
        确保Redis正在运行（自动启动）
        
        Returns:
            bool: True表示Redis可用，False表示不可用
        """
        # 检查是否运行
        if self.is_redis_running():
            # 检查是Memurai还是redis-server
            memurai_status = self.check_memurai_service()
            if memurai_status['running']:
                print("[Redis管理器] ✅ Redis服务正常运行 (Memurai)")
            else:
                print("[Redis管理器] ✅ Redis服务正常运行 (redis-server)")
            return True
        
        # 检查Memurai服务
        memurai_status = self.check_memurai_service()
        if memurai_status['installed'] and not memurai_status['running']:
            print("[Redis管理器] ⚠️ 检测到Memurai服务但未运行")
            print("[Redis管理器] 提示: 启动脚本会自动启动Memurai服务")
            return False
        
        # 尝试启动redis-server
        print("[Redis管理器] ⚠️ Redis未运行，尝试自动启动...")
        return self.start_redis()
    
    def health_check(self):
        """
        健康检查
        
        Returns:
            dict: 健康状态信息
        """
        status = {
            'running': False,
            'host': self.host,
            'port': self.port,
            'memory': None,
            'keys': None,
            'error': None
        }
        
        try:
            import redis
            r = redis.Redis(host=self.host, port=self.port, socket_connect_timeout=2)
            
            # 测试连接
            r.ping()
            status['running'] = True
            
            # 获取信息
            info = r.info()
            status['memory'] = info.get('used_memory_human', 'N/A')
            
            # 获取键数量
            db_info = info.get('db0', {})
            if isinstance(db_info, dict):
                status['keys'] = db_info.get('keys', 0)
            else:
                status['keys'] = 0
                
        except Exception as e:
            status['error'] = str(e)
        
        return status
    
    def stop_redis(self):
        """停止Redis服务"""
        if self.redis_process:
            print("[Redis管理器] 🛑 停止Redis服务...")
            self.redis_process.terminate()
            self.redis_process.wait(timeout=5)
            print("[Redis管理器] ✅ Redis已停止")


# 全局Redis管理器实例
_redis_manager = None


def get_redis_manager():
    """获取Redis管理器单例"""
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager


def ensure_redis_running():
    """
    确保Redis正在运行（便捷函数）
    
    Returns:
        bool: True表示Redis可用，False表示不可用
    """
    manager = get_redis_manager()
    return manager.ensure_redis_running()


def redis_health_check():
    """
    Redis健康检查（便捷函数）
    
    Returns:
        dict: 健康状态信息
    """
    manager = get_redis_manager()
    return manager.health_check()


# 导出
__all__ = [
    'RedisManager',
    'get_redis_manager',
    'ensure_redis_running',
    'redis_health_check'
]


# 测试代码
if __name__ == "__main__":
    print("="*80)
    print("Redis管理器测试")
    print("="*80)
    
    manager = RedisManager()
    
    # 测试1: 检查Redis状态
    print("\n[测试1] 检查Redis状态...")
    if manager.is_redis_running():
        print("✅ Redis正在运行")
    else:
        print("❌ Redis未运行")
    
    # 测试2: 确保Redis运行
    print("\n[测试2] 确保Redis运行...")
    if manager.ensure_redis_running():
        print("✅ Redis可用")
    else:
        print("❌ Redis不可用")
    
    # 测试3: 健康检查
    print("\n[测试3] 健康检查...")
    status = manager.health_check()
    print(f"运行状态: {status['running']}")
    print(f"服务地址: {status['host']}:{status['port']}")
    print(f"内存使用: {status['memory']}")
    print(f"键数量: {status['keys']}")
    if status['error']:
        print(f"错误信息: {status['error']}")
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)
