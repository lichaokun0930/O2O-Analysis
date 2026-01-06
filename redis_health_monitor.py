# -*- coding: utf-8 -*-
"""
Redis健康监控模块 - 生产级

功能:
1. 启动时健康检查
2. 运行时定期检查（每30秒）
3. 断开时自动重连
4. 监控指标收集

作者: AI Assistant
版本: V1.0
日期: 2025-12-11
"""

import redis
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedisHealthMonitor:
    """Redis健康监控器"""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        check_interval: int = 30,  # 检查间隔（秒）
        max_retry: int = 3  # 最大重连次数
    ):
        """
        初始化监控器
        
        Args:
            host: Redis主机
            port: Redis端口
            db: 数据库编号
            password: 密码
            check_interval: 健康检查间隔（秒）
            max_retry: 最大重连次数
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.check_interval = check_interval
        self.max_retry = max_retry
        
        self.client: Optional[redis.Redis] = None
        self.is_healthy = False
        self.last_check_time = None
        self.consecutive_failures = 0
        
        # 监控指标
        self.metrics = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'reconnect_attempts': 0,
            'last_error': None,
            'uptime_start': datetime.now()
        }
        
        # 后台监控线程
        self._monitor_thread = None
        self._stop_monitor = False
    
    def initial_check(self) -> Dict[str, Any]:
        """
        启动时完整健康检查
        
        Returns:
            检查结果字典
        """
        result = {
            'connected': False,
            'version': None,
            'memory': None,
            'config': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # 1. 连接测试
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 2. Ping测试
            self.client.ping()
            result['connected'] = True
            self.is_healthy = True
            logger.info(f"✅ Redis连接成功: {self.host}:{self.port}")
            
            # 3. 获取版本信息
            info = self.client.info('server')
            result['version'] = info.get('redis_version', 'unknown')
            logger.info(f"📌 Redis版本: {result['version']}")
            
            # 4. 检查内存配置
            memory_info = self.client.info('memory')
            maxmemory = self.client.config_get('maxmemory')['maxmemory']
            maxmemory_policy = self.client.config_get('maxmemory-policy')['maxmemory-policy']
            
            result['memory'] = {
                'used_mb': round(memory_info['used_memory'] / 1024 / 1024, 2),
                'max_mb': round(int(maxmemory) / 1024 / 1024, 2) if maxmemory != '0' else 0,
                'policy': maxmemory_policy
            }
            
            result['config'] = {
                'maxmemory': maxmemory,
                'maxmemory_policy': maxmemory_policy
            }
            
            # 5. 配置检查和警告
            if maxmemory == '0':
                warning = "⚠️ Redis未设置内存限制，建议设置为1GB"
                result['warnings'].append(warning)
                logger.warning(warning)
            
            if maxmemory_policy not in ['allkeys-lru', 'volatile-lru']:
                warning = f"⚠️ Redis淘汰策略为{maxmemory_policy}，建议使用allkeys-lru"
                result['warnings'].append(warning)
                logger.warning(warning)
            
            # 6. 性能测试
            start = time.time()
            self.client.set('health_check_test', 'ok', ex=10)
            self.client.get('health_check_test')
            latency = (time.time() - start) * 1000
            
            result['latency_ms'] = round(latency, 2)
            
            if latency > 100:
                warning = f"⚠️ Redis延迟较高: {latency:.2f}ms"
                result['warnings'].append(warning)
                logger.warning(warning)
            else:
                logger.info(f"✅ Redis延迟: {latency:.2f}ms")
            
            logger.info(f"✅ Redis健康检查完成")
            
        except redis.ConnectionError as e:
            error = f"❌ Redis连接失败: {e}"
            result['errors'].append(error)
            logger.error(error)
            self.is_healthy = False
            
        except Exception as e:
            error = f"❌ Redis检查失败: {e}"
            result['errors'].append(error)
            logger.error(error)
            self.is_healthy = False
        
        self.last_check_time = datetime.now()
        return result
    
    def quick_check(self) -> bool:
        """
        快速健康检查（ping）
        
        Returns:
            是否健康
        """
        self.metrics['total_checks'] += 1
        
        try:
            if self.client is None:
                raise redis.ConnectionError("Client not initialized")
            
            # Ping测试
            self.client.ping()
            
            self.is_healthy = True
            self.consecutive_failures = 0
            self.metrics['successful_checks'] += 1
            self.last_check_time = datetime.now()
            
            return True
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            self.is_healthy = False
            self.consecutive_failures += 1
            self.metrics['failed_checks'] += 1
            self.metrics['last_error'] = str(e)
            self.last_check_time = datetime.now()
            
            logger.warning(f"⚠️ Redis健康检查失败 (连续{self.consecutive_failures}次): {e}")
            
            # 尝试重连
            if self.consecutive_failures <= self.max_retry:
                logger.info(f"🔄 尝试重连Redis ({self.consecutive_failures}/{self.max_retry})...")
                if self._reconnect():
                    logger.info("✅ Redis重连成功")
                    return True
            else:
                logger.error(f"❌ Redis重连失败，已达最大重试次数({self.max_retry})")
            
            return False
    
    def _reconnect(self) -> bool:
        """
        重新连接Redis
        
        Returns:
            是否成功
        """
        self.metrics['reconnect_attempts'] += 1
        
        try:
            # 关闭旧连接
            if self.client:
                try:
                    self.client.close()
                except:
                    pass
            
            # 创建新连接
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 测试连接
            self.client.ping()
            
            self.is_healthy = True
            self.consecutive_failures = 0
            return True
            
        except Exception as e:
            logger.error(f"❌ 重连失败: {e}")
            return False
    
    def start_monitoring(self):
        """启动后台监控线程"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("⚠️ 监控线程已在运行")
            return
        
        self._stop_monitor = False
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="RedisHealthMonitor"
        )
        self._monitor_thread.start()
        logger.info(f"✅ Redis健康监控已启动（间隔{self.check_interval}秒）")
    
    def stop_monitoring(self):
        """停止后台监控"""
        self._stop_monitor = True
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("🛑 Redis健康监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while not self._stop_monitor:
            try:
                self.quick_check()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"❌ 监控循环错误: {e}")
                time.sleep(self.check_interval)
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取当前状态
        
        Returns:
            状态字典
        """
        uptime = (datetime.now() - self.metrics['uptime_start']).total_seconds()
        
        return {
            'healthy': self.is_healthy,
            'host': f"{self.host}:{self.port}",
            'last_check': self.last_check_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_check_time else None,
            'consecutive_failures': self.consecutive_failures,
            'metrics': {
                'total_checks': self.metrics['total_checks'],
                'successful_checks': self.metrics['successful_checks'],
                'failed_checks': self.metrics['failed_checks'],
                'success_rate': round(
                    self.metrics['successful_checks'] / max(self.metrics['total_checks'], 1) * 100,
                    2
                ),
                'reconnect_attempts': self.metrics['reconnect_attempts'],
                'uptime_seconds': round(uptime, 0),
                'uptime_hours': round(uptime / 3600, 2)
            },
            'last_error': self.metrics['last_error']
        }
    
    def get_metrics_summary(self) -> str:
        """获取指标摘要（用于日志）"""
        status = self.get_status()
        
        if status['healthy']:
            return f"✅ Redis健康 | 成功率: {status['metrics']['success_rate']}% | 运行时间: {status['metrics']['uptime_hours']}h"
        else:
            return f"❌ Redis异常 | 连续失败: {status['consecutive_failures']}次 | 错误: {status['last_error']}"


# 全局实例
_global_monitor: Optional[RedisHealthMonitor] = None


def get_health_monitor(**kwargs) -> RedisHealthMonitor:
    """获取全局监控器实例"""
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = RedisHealthMonitor(**kwargs)
    
    return _global_monitor


# 导出
__all__ = [
    'RedisHealthMonitor',
    'get_health_monitor'
]


if __name__ == "__main__":
    print("=" * 70)
    print(" Redis健康监控测试")
    print("=" * 70)
    print()
    
    # 创建监控器
    monitor = RedisHealthMonitor(
        host='localhost',
        port=6379,
        check_interval=5  # 测试用5秒
    )
    
    # 初始检查
    print("1️⃣ 启动时完整检查:")
    result = monitor.initial_check()
    
    if result['connected']:
        print(f"   ✅ 连接成功")
        print(f"   版本: {result['version']}")
        print(f"   内存: {result['memory']['used_mb']}MB / {result['memory']['max_mb']}MB")
        print(f"   延迟: {result.get('latency_ms', 0)}ms")
        
        if result['warnings']:
            print(f"   警告:")
            for warning in result['warnings']:
                print(f"      {warning}")
    else:
        print(f"   ❌ 连接失败")
        for error in result['errors']:
            print(f"      {error}")
    
    print()
    print("2️⃣ 启动后台监控（10秒）:")
    monitor.start_monitoring()
    
    # 等待10秒
    for i in range(10):
        time.sleep(1)
        if i % 5 == 4:
            status = monitor.get_status()
            print(f"   {monitor.get_metrics_summary()}")
    
    # 停止监控
    monitor.stop_monitoring()
    
    print()
    print("3️⃣ 最终状态:")
    status = monitor.get_status()
    print(f"   健康: {status['healthy']}")
    print(f"   总检查: {status['metrics']['total_checks']}")
    print(f"   成功率: {status['metrics']['success_rate']}%")
    print(f"   运行时间: {status['metrics']['uptime_hours']}小时")
    
    print()
    print("=" * 70)
