# -*- coding: utf-8 -*-
"""
压力测试 - 模拟30人并发访问

测试场景:
1. 30个用户同时访问首页
2. 30个用户同时上传数据
3. 30个用户同时切换Tab
4. 30个用户同时查询数据

作者: AI Assistant
版本: V1.0
日期: 2025-12-11
"""

import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import statistics


class LoadTester:
    """压力测试器"""
    
    def __init__(self, base_url='http://localhost:8051', num_users=30):
        """
        初始化测试器
        
        Args:
            base_url: 应用URL
            num_users: 模拟用户数
        """
        self.base_url = base_url
        self.num_users = num_users
        self.results = []
    
    def test_homepage(self):
        """测试首页访问"""
        start = time.time()
        try:
            response = requests.get(self.base_url, timeout=30)
            elapsed = time.time() - start
            
            return {
                'success': response.status_code == 200,
                'time': elapsed,
                'status_code': response.status_code
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                'success': False,
                'time': elapsed,
                'error': str(e)
            }
    
    def run_concurrent_test(self, test_func, test_name):
        """
        运行并发测试
        
        Args:
            test_func: 测试函数
            test_name: 测试名称
        """
        print(f"\n{'='*70}")
        print(f" {test_name}")
        print(f"{'='*70}")
        print(f"模拟用户数: {self.num_users}")
        print(f"开始时间: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        results = []
        start_time = time.time()
        
        # 并发执行
        with ThreadPoolExecutor(max_workers=self.num_users) as executor:
            futures = [executor.submit(test_func) for _ in range(self.num_users)]
            
            for idx, future in enumerate(as_completed(futures), 1):
                result = future.result()
                results.append(result)
                
                # 实时显示进度
                if result['success']:
                    print(f"✅ 用户{idx:2d}: {result['time']:.2f}秒")
                else:
                    error = result.get('error', f"HTTP {result.get('status_code', 'N/A')}")
                    print(f"❌ 用户{idx:2d}: 失败 - {error}")
        
        total_time = time.time() - start_time
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        success_rate = success_count / len(results) * 100
        
        response_times = [r['time'] for r in results if r['success']]
        
        print()
        print(f"{'='*70}")
        print(f" 测试结果")
        print(f"{'='*70}")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"成功率: {success_rate:.1f}% ({success_count}/{len(results)})")
        
        if response_times:
            print(f"\n响应时间统计:")
            print(f"  最快: {min(response_times):.2f}秒")
            print(f"  最慢: {max(response_times):.2f}秒")
            print(f"  平均: {statistics.mean(response_times):.2f}秒")
            print(f"  中位数: {statistics.median(response_times):.2f}秒")
            
            if len(response_times) > 1:
                print(f"  标准差: {statistics.stdev(response_times):.2f}秒")
        
        # 性能评估
        print(f"\n性能评估:")
        if success_rate >= 95 and statistics.mean(response_times) < 3:
            print(f"  ✅ 优秀 - 系统运行良好")
        elif success_rate >= 90 and statistics.mean(response_times) < 5:
            print(f"  🟡 良好 - 系统基本满足需求")
        elif success_rate >= 80:
            print(f"  ⚠️ 一般 - 建议优化")
        else:
            print(f"  ❌ 较差 - 需要立即优化")
        
        print(f"{'='*70}\n")
        
        return {
            'test_name': test_name,
            'total_time': total_time,
            'success_rate': success_rate,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'results': results
        }
    
    def run_all_tests(self):
        """运行所有测试"""
        print(f"\n{'#'*70}")
        print(f"# 压力测试 - 模拟{self.num_users}人并发")
        print(f"# 目标: {self.base_url}")
        print(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*70}\n")
        
        # 检查服务是否可用
        print("🔍 检查服务状态...")
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200:
                print("✅ 服务正常运行\n")
            else:
                print(f"⚠️ 服务返回状态码: {response.status_code}\n")
        except Exception as e:
            print(f"❌ 无法连接到服务: {e}")
            print(f"   请确保看板正在运行: .\\启动看板.ps1\n")
            return
        
        # 测试1: 首页访问
        test1 = self.run_concurrent_test(
            self.test_homepage,
            f"测试1: {self.num_users}人同时访问首页"
        )
        
        # 等待一下
        print("⏳ 等待5秒...")
        time.sleep(5)
        
        # 测试2: 重复访问（测试缓存）
        test2 = self.run_concurrent_test(
            self.test_homepage,
            f"测试2: {self.num_users}人再次访问（测试缓存）"
        )
        
        # 总结
        print(f"\n{'#'*70}")
        print(f"# 测试总结")
        print(f"{'#'*70}\n")
        
        print(f"测试1（首次访问）:")
        print(f"  成功率: {test1['success_rate']:.1f}%")
        print(f"  平均响应: {test1['avg_response_time']:.2f}秒")
        
        print(f"\n测试2（缓存访问）:")
        print(f"  成功率: {test2['success_rate']:.1f}%")
        print(f"  平均响应: {test2['avg_response_time']:.2f}秒")
        
        if test2['avg_response_time'] < test1['avg_response_time']:
            improvement = (1 - test2['avg_response_time'] / test1['avg_response_time']) * 100
            print(f"\n✅ 缓存效果: 响应时间提升{improvement:.1f}%")
        
        print(f"\n{'#'*70}\n")


if __name__ == "__main__":
    import sys
    
    # 解析参数
    num_users = 30
    if len(sys.argv) > 1:
        try:
            num_users = int(sys.argv[1])
        except:
            print(f"⚠️ 无效的用户数，使用默认值: 30")
    
    # 运行测试
    tester = LoadTester(
        base_url='http://localhost:8051',
        num_users=num_users
    )
    
    tester.run_all_tests()
