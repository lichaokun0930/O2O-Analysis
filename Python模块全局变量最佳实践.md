# Python模块全局变量最佳实践

## 🎯 问题背景

### 典型场景
你有一个全局单例对象（如Redis缓存管理器），需要在多个模块中共享使用。

### 常见错误模式 ❌

```python
# redis_cache_manager.py
REDIS_CACHE_MANAGER = None  # 模块加载时是None

# 主程序稍后初始化
def init_app():
    global REDIS_CACHE_MANAGER
    REDIS_CACHE_MANAGER = RedisCacheManager()
```

```python
# callbacks.py
from redis_cache_manager import REDIS_CACHE_MANAGER  # 导入时是None

def some_function():
    if REDIS_CACHE_MANAGER:  # 永远是None！
        REDIS_CACHE_MANAGER.set(...)
```

**问题**：`callbacks.py`导入时，`REDIS_CACHE_MANAGER`还是`None`。即使主程序后来初始化了，已导入的引用也不会更新。

## ✅ 解决方案

### 方案1: 模块加载时初始化（推荐）⭐

```python
# redis_cache_manager.py
def get_cache_manager():
    """获取全局缓存管理器（单例）"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = RedisCacheManager()
    return _global_cache_manager

# ✅ 模块加载时就初始化
try:
    REDIS_CACHE_MANAGER = get_cache_manager()
    if REDIS_CACHE_MANAGER.enabled:
        logger.info("✅ 全局实例已初始化")
except Exception as e:
    logger.error(f"❌ 初始化失败: {e}")
    REDIS_CACHE_MANAGER = None
```

**优点**：
- 导入即可用，无需额外初始化
- 避免时序问题
- 代码简洁

**缺点**：
- 模块导入时就执行初始化（可能影响启动速度）
- 配置必须在导入前准备好

### 方案2: 使用工厂函数

```python
# redis_cache_manager.py
_global_cache_manager = None

def get_cache_manager():
    """获取全局缓存管理器（延迟初始化）"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = RedisCacheManager()
    return _global_cache_manager
```

```python
# callbacks.py
from redis_cache_manager import get_cache_manager

def some_function():
    cache = get_cache_manager()  # 每次调用时获取
    if cache and cache.enabled:
        cache.set(...)
```

**优点**：
- 延迟初始化，按需创建
- 灵活性高

**缺点**：
- 每次使用都要调用函数
- 代码稍显冗长

### 方案3: 使用类属性（单例模式）

```python
# redis_cache_manager.py
class RedisCacheManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, host='localhost', port=6379):
        if not hasattr(self, 'initialized'):
            # 只初始化一次
            self.host = host
            self.port = port
            self.client = redis.Redis(host=host, port=port)
            self.initialized = True

# 使用
cache = RedisCacheManager()  # 总是返回同一个实例
```

**优点**：
- 真正的单例模式
- 线程安全（可以加锁）

**缺点**：
- 代码复杂度高
- 不够Pythonic

### 方案4: 使用模块本身作为单例

```python
# redis_cache_manager.py
# 模块级别的变量和函数
_client = None
_enabled = False

def init(host='localhost', port=6379):
    """初始化Redis连接"""
    global _client, _enabled
    try:
        _client = redis.Redis(host=host, port=port)
        _client.ping()
        _enabled = True
    except Exception as e:
        _enabled = False

def set(key, value):
    """设置缓存"""
    if _enabled:
        _client.set(key, value)

def get(key):
    """获取缓存"""
    if _enabled:
        return _client.get(key)
    return None

# 模块加载时初始化
init()
```

```python
# callbacks.py
import redis_cache_manager as cache

def some_function():
    cache.set('key', 'value')  # 直接使用模块函数
```

**优点**：
- 最简洁
- 模块本身就是单例

**缺点**：
- 不够面向对象
- 难以扩展

## 🔍 如何检测这类问题

### 1. 启动时自检

```python
# 主程序启动时
def startup_check():
    """启动自检"""
    from redis_cache_manager import REDIS_CACHE_MANAGER
    
    if REDIS_CACHE_MANAGER is None:
        print("❌ Redis缓存管理器未初始化")
        return False
    
    if not REDIS_CACHE_MANAGER.enabled:
        print("⚠️ Redis缓存管理器已初始化但未启用")
        return False
    
    print("✅ Redis缓存管理器正常")
    return True

# 启动时调用
if not startup_check():
    print("⚠️ 系统启动异常，请检查配置")
```

### 2. 诊断工具

```python
# 诊断脚本
def diagnose_redis():
    """诊断Redis缓存状态"""
    print("检查Redis缓存...")
    
    # 1. 检查Redis服务
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        print("   ✅ Redis连接: 正常")
    except Exception as e:
        print(f"   ❌ Redis连接: 失败 ({e})")
        return
    
    # 2. 检查缓存管理器
    try:
        from redis_cache_manager import REDIS_CACHE_MANAGER
        if REDIS_CACHE_MANAGER is None:
            print("   ❌ Redis缓存管理器: 未初始化")
        elif not REDIS_CACHE_MANAGER.enabled:
            print("   ⚠️ Redis缓存管理器: 已初始化但未启用")
        else:
            print("   ✅ Redis缓存管理器: 已启用")
            stats = REDIS_CACHE_MANAGER.get_stats()
            print(f"   📊 缓存统计: {stats}")
    except Exception as e:
        print(f"   ❌ Redis缓存管理器: 导入失败 ({e})")

if __name__ == "__main__":
    diagnose_redis()
```

### 3. 单元测试

```python
# test_redis_cache.py
import unittest

class TestRedisCacheManager(unittest.TestCase):
    
    def test_global_instance_exists(self):
        """测试全局实例是否存在"""
        from redis_cache_manager import REDIS_CACHE_MANAGER
        self.assertIsNotNone(REDIS_CACHE_MANAGER, "全局实例不应该是None")
    
    def test_global_instance_enabled(self):
        """测试全局实例是否启用"""
        from redis_cache_manager import REDIS_CACHE_MANAGER
        self.assertTrue(REDIS_CACHE_MANAGER.enabled, "缓存管理器应该启用")
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        from redis_cache_manager import get_cache_manager
        instance1 = get_cache_manager()
        instance2 = get_cache_manager()
        self.assertIs(instance1, instance2, "应该返回同一个实例")
    
    def test_cache_operations(self):
        """测试缓存操作"""
        from redis_cache_manager import REDIS_CACHE_MANAGER
        
        # 设置缓存
        result = REDIS_CACHE_MANAGER.set('test_key', 'test_value')
        self.assertTrue(result, "设置缓存应该成功")
        
        # 获取缓存
        value = REDIS_CACHE_MANAGER.get('test_key')
        self.assertEqual(value, 'test_value', "获取的值应该匹配")
        
        # 清理
        REDIS_CACHE_MANAGER.delete('test_key')

if __name__ == '__main__':
    unittest.main()
```

## 📋 最佳实践清单

### 设计阶段
- [ ] 明确全局对象的生命周期（何时创建、何时销毁）
- [ ] 选择合适的初始化方案（模块加载时 vs 延迟初始化）
- [ ] 考虑线程安全（如果是多线程环境）
- [ ] 设计降级方案（如果初始化失败怎么办）

### 实现阶段
- [ ] 使用单例模式或工厂函数
- [ ] 添加详细的日志（初始化成功/失败）
- [ ] 提供状态检查方法（`is_enabled()`, `get_stats()`）
- [ ] 处理异常情况（连接失败、超时等）

### 测试阶段
- [ ] 编写单元测试（测试初始化、单例、操作）
- [ ] 编写集成测试（测试多模块协作）
- [ ] 编写诊断工具（快速排查问题）
- [ ] 添加启动自检（确保系统正常）

### 文档阶段
- [ ] 说明初始化时机和方式
- [ ] 提供使用示例
- [ ] 列出常见问题和解决方案
- [ ] 提供诊断工具使用说明

## 🛠️ 实用工具模板

### 通用诊断工具模板

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用模块诊断工具模板
"""

def diagnose_module(module_name, global_var_name, service_check_func=None):
    """
    通用模块诊断
    
    Args:
        module_name: 模块名（如'redis_cache_manager'）
        global_var_name: 全局变量名（如'REDIS_CACHE_MANAGER'）
        service_check_func: 服务检查函数（可选）
    """
    print(f"\n检查 {module_name}...")
    
    # 1. 检查服务（如果提供）
    if service_check_func:
        try:
            service_check_func()
            print(f"   ✅ 服务连接: 正常")
        except Exception as e:
            print(f"   ❌ 服务连接: 失败 ({e})")
            return False
    
    # 2. 检查全局变量
    try:
        module = __import__(module_name)
        global_var = getattr(module, global_var_name, None)
        
        if global_var is None:
            print(f"   ❌ {global_var_name}: 未初始化")
            return False
        
        # 检查enabled属性（如果有）
        if hasattr(global_var, 'enabled'):
            if not global_var.enabled:
                print(f"   ⚠️ {global_var_name}: 已初始化但未启用")
                return False
        
        print(f"   ✅ {global_var_name}: 已启用")
        
        # 显示统计信息（如果有）
        if hasattr(global_var, 'get_stats'):
            stats = global_var.get_stats()
            print(f"   📊 统计信息: {stats}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ {global_var_name}: 导入失败 ({e})")
        return False

# 使用示例
if __name__ == "__main__":
    def check_redis():
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
    
    diagnose_module(
        module_name='redis_cache_manager',
        global_var_name='REDIS_CACHE_MANAGER',
        service_check_func=check_redis
    )
```

## 💡 经验总结

### 核心原则
1. **尽早初始化**：模块加载时就初始化，避免时序问题
2. **明确状态**：提供清晰的状态检查方法
3. **优雅降级**：初始化失败时有备选方案
4. **充分测试**：单元测试 + 集成测试 + 诊断工具

### 常见陷阱
1. ❌ 在主程序中初始化，其他模块导入时还是None
2. ❌ 没有状态检查，不知道是否真正可用
3. ❌ 没有日志，出问题难以排查
4. ❌ 没有测试，上线才发现问题

### 推荐做法
1. ✅ 模块加载时初始化（方案1）
2. ✅ 提供工厂函数作为备选（方案2）
3. ✅ 添加启动自检
4. ✅ 编写诊断工具
5. ✅ 完善单元测试

## 📚 延伸阅读

- Python单例模式的5种实现方式
- Python模块导入机制详解
- 依赖注入vs全局变量
- 线程安全的单例实现

---

**创建时间**: 2025-12-11  
**适用场景**: 全局单例对象、缓存管理器、数据库连接池、配置管理器等  
**关键词**: 单例模式、全局变量、模块初始化、Python最佳实践
