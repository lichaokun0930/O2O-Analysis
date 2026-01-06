"""
防抖工具模块 - V8.8前端体验优化

提供防抖装饰器和相关工具函数
避免快速点击时的重复请求

作者: GitHub Copilot
版本: V8.8
"""

import time
from functools import wraps
from dash.exceptions import PreventUpdate
from typing import Dict, Callable


# 全局防抖状态存储
_debounce_timers: Dict[int, float] = {}


def debounce(wait_ms: int = 300):
    """
    防抖装饰器
    
    在wait_ms毫秒内的重复调用会被忽略
    
    参数：
        wait_ms: 防抖等待时间（毫秒）
    
    使用示例：
        @app.callback(...)
        @debounce(wait_ms=300)
        def my_callback(...):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_id = id(func)
            current_time = time.time() * 1000  # 转换为毫秒
            
            # 检查是否在防抖期内
            if func_id in _debounce_timers:
                last_time = _debounce_timers[func_id]
                time_diff = current_time - last_time
                
                if time_diff < wait_ms:
                    print(f"⏱️ [防抖] 跳过重复请求（间隔{time_diff:.0f}ms < {wait_ms}ms）")
                    raise PreventUpdate
            
            # 更新时间戳
            _debounce_timers[func_id] = current_time
            
            # 执行原函数
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def throttle(wait_ms: int = 1000):
    """
    节流装饰器
    
    确保函数在wait_ms毫秒内最多执行一次
    与防抖不同，节流会立即执行第一次调用
    
    参数：
        wait_ms: 节流等待时间（毫秒）
    
    使用示例：
        @app.callback(...)
        @throttle(wait_ms=1000)
        def my_callback(...):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_id = id(func)
            current_time = time.time() * 1000
            
            # 检查是否在节流期内
            if func_id in _debounce_timers:
                last_time = _debounce_timers[func_id]
                time_diff = current_time - last_time
                
                if time_diff < wait_ms:
                    print(f"⏱️ [节流] 跳过频繁请求（间隔{time_diff:.0f}ms < {wait_ms}ms）")
                    raise PreventUpdate
            
            # 更新时间戳并执行
            _debounce_timers[func_id] = current_time
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def clear_debounce_timer(func: Callable):
    """
    清除指定函数的防抖计时器
    
    参数：
        func: 需要清除计时器的函数
    """
    func_id = id(func)
    if func_id in _debounce_timers:
        del _debounce_timers[func_id]
        print(f"🧹 [防抖] 已清除计时器")


def clear_all_debounce_timers():
    """清除所有防抖计时器"""
    global _debounce_timers
    count = len(_debounce_timers)
    _debounce_timers.clear()
    print(f"🧹 [防抖] 已清除所有计时器（共{count}个）")


def get_debounce_status() -> Dict[str, any]:
    """
    获取防抖状态信息
    
    返回：
        {
            'active_timers': int,  # 活跃的计时器数量
            'timers': dict  # 计时器详情
        }
    """
    return {
        'active_timers': len(_debounce_timers),
        'timers': {
            func_id: {
                'last_call': timestamp,
                'time_since_last': time.time() * 1000 - timestamp
            }
            for func_id, timestamp in _debounce_timers.items()
        }
    }


# 导出
__all__ = [
    'debounce',
    'throttle',
    'clear_debounce_timer',
    'clear_all_debounce_timers',
    'get_debounce_status'
]
