#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用模块诊断工具
用于检测全局变量初始化问题
"""

import sys
import importlib
from typing import Callable, Optional, Dict, Any


class ModuleDiagnostic:
    """模块诊断工具"""
    
    def __init__(self, module_name: str, global_var_name: str):
        """
        初始化诊断工具
        
        Args:
            module_name: 模块名（如'redis_cache_manager'）
            global_var_name: 全局变量名（如'REDIS_CACHE_MANAGER'）
        """
        self.module_name = module_name
        self.global_var_name = global_var_name
        self.results = {}
    
    def check_service(self, check_func: Callable) -> bool:
        """
        检查底层服务
        
        Args:
            check_func: 服务检查函数，抛出异常表示失败
            
        Returns:
            是否正常
        """
        print(f"\n[1/4] 检查底层服务...")
        try:
            check_func()
            print(f"   ✅ 服务连接: 正常")
            self.results['service'] = 'ok'
            return True
        except Exception as e:
            print(f"   ❌ 服务连接: 失败")
            print(f"   错误: {e}")
            self.results['service'] = f'failed: {e}'
            return False
    
    def check_module_import(self) -> bool:
        """
        检查模块是否可以导入
        
        Returns:
            是否成功
        """
        print(f"\n[2/4] 检查模块导入...")
        try:
            module = importlib.import_module(self.module_name)
            print(f"   ✅ 模块导入: 成功")
            self.results['import'] = 'ok'
            self.module = module
            return True
        except Exception as e:
            print(f"   ❌ 模块导入: 失败")
            print(f"   错误: {e}")
            self.results['import'] = f'failed: {e}'
            return False
    
    def check_global_var(self) -> bool:
        """
        检查全局变量是否存在且已初始化
        
        Returns:
            是否正常
        """
        print(f"\n[3/4] 检查全局变量...")
        
        if not hasattr(self, 'module'):
            print(f"   ⏭️  跳过（模块未导入）")
            return False
        
        try:
            global_var = getattr(self.module, self.global_var_name, None)
            
            if global_var is None:
                print(f"   ❌ {self.global_var_name}: 未初始化（None）")
                self.results['global_var'] = 'not_initialized'
                return False
            
            print(f"   ✅ {self.global_var_name}: 已初始化")
            print(f"   类型: {type(global_var).__name__}")
            
            # 检查enabled属性
            if hasattr(global_var, 'enabled'):
                if global_var.enabled:
                    print(f"   ✅ 状态: 已启用")
                    self.results['global_var'] = 'enabled'
                else:
                    print(f"   ⚠️  状态: 已初始化但未启用")
                    self.results['global_var'] = 'disabled'
                    return False
            else:
                self.results['global_var'] = 'ok'
            
            self.global_var = global_var
            return True
            
        except Exception as e:
            print(f"   ❌ {self.global_var_name}: 检查失败")
            print(f"   错误: {e}")
            self.results['global_var'] = f'failed: {e}'
            return False
    
    def check_functionality(self, test_func: Optional[Callable] = None) -> bool:
        """
        检查功能是否正常
        
        Args:
            test_func: 功能测试函数，接收global_var作为参数
            
        Returns:
            是否正常
        """
        print(f"\n[4/4] 检查功能...")
        
        if not hasattr(self, 'global_var'):
            print(f"   ⏭️  跳过（全局变量未初始化）")
            return False
        
        if test_func is None:
            print(f"   ⏭️  跳过（未提供测试函数）")
            return True
        
        try:
            test_func(self.global_var)
            print(f"   ✅ 功能测试: 通过")
            self.results['functionality'] = 'ok'
            return True
        except Exception as e:
            print(f"   ❌ 功能测试: 失败")
            print(f"   错误: {e}")
            self.results['functionality'] = f'failed: {e}'
            return False
    
    def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        if not hasattr(self, 'global_var'):
            return None
        
        if hasattr(self.global_var, 'get_stats'):
            try:
                return self.global_var.get_stats()
            except Exception as e:
                print(f"   ⚠️  获取统计信息失败: {e}")
                return None
        
        return None
    
    def run(
        self,
        service_check: Optional[Callable] = None,
        functionality_test: Optional[Callable] = None
    ) -> bool:
        """
        运行完整诊断
        
        Args:
            service_check: 服务检查函数
            functionality_test: 功能测试函数
            
        Returns:
            是否全部通过
        """
        print("=" * 80)
        print(f" 模块诊断: {self.module_name}.{self.global_var_name}")
        print("=" * 80)
        
        all_passed = True
        
        # 1. 检查服务
        if service_check:
            if not self.check_service(service_check):
                all_passed = False
        
        # 2. 检查模块导入
        if not self.check_module_import():
            all_passed = False
            self.print_summary()
            return False
        
        # 3. 检查全局变量
        if not self.check_global_var():
            all_passed = False
        
        # 4. 检查功能
        if functionality_test:
            if not self.check_functionality(functionality_test):
                all_passed = False
        
        # 5. 显示统计信息
        stats = self.get_stats()
        if stats:
            print(f"\n📊 统计信息:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
        
        # 6. 打印总结
        self.print_summary()
        
        return all_passed
    
    def print_summary(self):
        """打印诊断总结"""
        print("\n" + "=" * 80)
        print(" 诊断总结")
        print("=" * 80)
        
        all_ok = all(
            v in ['ok', 'enabled'] 
            for v in self.results.values()
        )
        
        if all_ok:
            print("✅ 所有检查通过，模块正常工作")
        else:
            print("⚠️  发现以下问题:")
            for check, result in self.results.items():
                if result not in ['ok', 'enabled']:
                    print(f"   - {check}: {result}")
        
        print("=" * 80 + "\n")


# =============================================================================
# 使用示例
# =============================================================================

def example_redis_diagnostic():
    """Redis缓存管理器诊断示例"""
    
    # 创建诊断工具
    diagnostic = ModuleDiagnostic(
        module_name='redis_cache_manager',
        global_var_name='REDIS_CACHE_MANAGER'
    )
    
    # 定义服务检查函数
    def check_redis_service():
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
    
    # 定义功能测试函数
    def test_redis_functionality(cache_manager):
        # 测试设置缓存
        result = cache_manager.set('test_key', 'test_value', ttl=60)
        if not result:
            raise Exception("设置缓存失败")
        
        # 测试获取缓存
        value = cache_manager.get('test_key')
        if value != 'test_value':
            raise Exception(f"获取缓存失败，期望'test_value'，实际'{value}'")
        
        # 清理测试数据
        cache_manager.delete('test_key')
    
    # 运行诊断
    success = diagnostic.run(
        service_check=check_redis_service,
        functionality_test=test_redis_functionality
    )
    
    return success


def example_database_diagnostic():
    """数据库连接诊断示例"""
    
    diagnostic = ModuleDiagnostic(
        module_name='database.connection',
        global_var_name='engine'
    )
    
    def check_database_service():
        from sqlalchemy import create_engine, text
        engine = create_engine('postgresql+pg8000://postgres:postgres@localhost:5432/o2o_dashboard')
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    
    def test_database_functionality(engine):
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM orders"))
            count = result.scalar()
            if count is None:
                raise Exception("查询失败")
    
    success = diagnostic.run(
        service_check=check_database_service,
        functionality_test=test_database_functionality
    )
    
    return success


# =============================================================================
# 命令行接口
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='通用模块诊断工具')
    parser.add_argument('--module', '-m', help='模块名', default='redis_cache_manager')
    parser.add_argument('--var', '-v', help='全局变量名', default='REDIS_CACHE_MANAGER')
    parser.add_argument('--example', '-e', help='运行示例', choices=['redis', 'database'])
    
    args = parser.parse_args()
    
    if args.example == 'redis':
        print("运行Redis缓存管理器诊断示例...\n")
        success = example_redis_diagnostic()
        sys.exit(0 if success else 1)
    
    elif args.example == 'database':
        print("运行数据库连接诊断示例...\n")
        success = example_database_diagnostic()
        sys.exit(0 if success else 1)
    
    else:
        # 基本诊断（不包含服务检查和功能测试）
        diagnostic = ModuleDiagnostic(
            module_name=args.module,
            global_var_name=args.var
        )
        success = diagnostic.run()
        sys.exit(0 if success else 1)
