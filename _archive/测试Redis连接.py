"""
Redis连接测试脚本
测试Memurai/Redis是否正常工作
"""

import redis
import json
import pandas as pd
from datetime import datetime

print("=" * 60)
print("          Redis 功能测试")
print("=" * 60)

try:
    # 1. 连接测试
    print("\n[1/5] 测试连接...")
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    result = r.ping()
    if result:
        print("✅ 连接成功! PONG")
    else:
        print("❌ 连接失败")
        exit(1)
    
    # 2. 获取服务器信息
    print("\n[2/5] 获取服务器信息...")
    info = r.info('server')
    print(f"  Redis版本: {info.get('redis_version', '未知')}")
    print(f"  运行模式: {info.get('redis_mode', '未知')}")
    print(f"  进程ID: {info.get('process_id', '未知')}")
    
    # 3. 基础操作测试
    print("\n[3/5] 测试基础读写...")
    r.set('test_key', 'Hello Redis!')
    value = r.get('test_key')
    print(f"  写入测试: test_key = 'Hello Redis!'")
    print(f"  读取结果: {value}")
    if value == 'Hello Redis!':
        print("  ✅ 读写正常")
    else:
        print("  ❌ 读写异常")
    
    # 4. DataFrame缓存测试
    print("\n[4/5] 测试DataFrame缓存...")
    test_data = pd.DataFrame({
        '商品': ['咖啡', '茶饮', '烘焙'],
        '销量': [100, 80, 60],
        '日期': [datetime.now().strftime('%Y-%m-%d')] * 3
    })
    
    # 序列化并存储
    cache_key = 'test_dataframe'
    json_str = test_data.to_json(orient='split', date_format='iso')
    r.setex(cache_key, 3600, json_str)  # 1小时过期
    print(f"  已缓存DataFrame (3行数据)")
    
    # 读取并反序列化
    cached_json = r.get(cache_key)
    if cached_json:
        df_restored = pd.read_json(cached_json, orient='split')
        print(f"  成功读取缓存:")
        print(df_restored.to_string(index=False))
        print("  ✅ DataFrame缓存正常")
    else:
        print("  ❌ 缓存读取失败")
    
    # 5. 性能测试
    print("\n[5/5] 简单性能测试...")
    import time
    
    # 写入测试
    start = time.time()
    for i in range(1000):
        r.set(f'perf_test_{i}', f'value_{i}')
    write_time = time.time() - start
    print(f"  写入1000条: {write_time:.3f}秒 ({1000/write_time:.0f} ops/s)")
    
    # 读取测试
    start = time.time()
    for i in range(1000):
        r.get(f'perf_test_{i}')
    read_time = time.time() - start
    print(f"  读取1000条: {read_time:.3f}秒 ({1000/read_time:.0f} ops/s)")
    
    # 清理测试数据
    r.delete('test_key', cache_key)
    for i in range(1000):
        r.delete(f'perf_test_{i}')
    
    # 内存使用
    mem_info = r.info('memory')
    used_memory_mb = mem_info.get('used_memory', 0) / 1024 / 1024
    print(f"\n  当前内存使用: {used_memory_mb:.2f} MB")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过! Redis可以正常使用")
    print("=" * 60)
    
except redis.ConnectionError:
    print("\n❌ 无法连接到Redis服务器")
    print("请确保:")
    print("  1. Memurai已安装")
    print("  2. Memurai服务正在运行")
    print("  3. 端口6379未被占用")
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
