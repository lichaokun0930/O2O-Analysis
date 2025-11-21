"""
Redis缓存性能对比测试
测试看板中的真实查询场景
"""

import time
import redis
from redis_config import redis_cache

print("=" * 60)
print("          Redis 缓存性能对比测试")
print("=" * 60)

try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print("\n✅ Redis连接成功\n")
    
    # 模拟数据库查询场景
    def simulate_database_query():
        """模拟数据库查询延迟"""
        time.sleep(0.1)  # 模拟100ms查询
        return [
            {'label': '咖啡门店A', 'value': '咖啡门店A'},
            {'label': '咖啡门店B', 'value': '咖啡门店B'},
            {'label': '咖啡门店C', 'value': '咖啡门店C'},
        ]
    
    # 测试1: 无缓存查询
    print("[测试1] 无缓存 - 直接查询")
    start = time.time()
    for i in range(10):
        result = simulate_database_query()
    no_cache_time = time.time() - start
    print(f"  10次查询耗时: {no_cache_time:.3f}秒")
    print(f"  平均每次: {no_cache_time/10*1000:.1f}ms\n")
    
    # 测试2: Redis缓存查询
    print("[测试2] Redis缓存 - 第一次存储")
    start = time.time()
    redis_cache.set('test_store_list', simulate_database_query(), expire=300)
    first_write = time.time() - start
    print(f"  写入缓存耗时: {first_write*1000:.1f}ms\n")
    
    print("[测试3] Redis缓存 - 后续读取")
    start = time.time()
    for i in range(10):
        result = redis_cache.get('test_store_list')
    cache_time = time.time() - start
    print(f"  10次读取耗时: {cache_time:.3f}秒")
    print(f"  平均每次: {cache_time/10*1000:.1f}ms\n")
    
    # 性能提升对比
    speedup = no_cache_time / cache_time
    print("=" * 60)
    print("          性能提升对比")
    print("=" * 60)
    print(f"无缓存平均: {no_cache_time/10*1000:.1f}ms")
    print(f"Redis缓存: {cache_time/10*1000:.1f}ms")
    print(f"性能提升: {speedup:.1f}x 倍")
    print(f"节省时间: {(no_cache_time - cache_time)/10*1000:.1f}ms/次")
    print("=" * 60)
    
    # 清理测试数据
    redis_cache.delete('test_store_list')
    print("\n✅ 测试完成,缓存已清理")
    
except redis.ConnectionError:
    print("\n❌ Redis未运行,请先启动Memurai")
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
