# -*- coding: utf-8 -*-
"""
测试V8.4分层缓存系统

测试内容:
1. 分层缓存管理器初始化
2. Level 1-3缓存读写
3. 压缩效果测试
4. 热点分析测试
5. 性能对比测试

作者: AI Assistant
版本: V8.4
日期: 2025-12-11
"""

import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

print("=" * 80)
print(" V8.4 分层缓存系统测试")
print("=" * 80)

# ========== 测试1: 初始化 ==========
print("\n[测试1] 初始化分层缓存管理器...")
from hierarchical_cache_manager import HierarchicalCacheManager

cache = HierarchicalCacheManager(
    host='localhost',
    port=6379,
    max_memory_mb=512,
    enable_compression=True
)

if not cache.enabled:
    print("❌ Redis未启用，无法继续测试")
    exit(1)

print("✅ 初始化成功")

# ========== 测试2: Level 1 - 原始数据缓存 ==========
print("\n[测试2] Level 1 - 原始数据缓存...")

# 创建测试数据（模拟10万条订单）
test_data = pd.DataFrame({
    '订单ID': [f'ORDER_{i:06d}' for i in range(100000)],
    '门店名称': np.random.choice(['门店A', '门店B', '门店C'], 100000),
    '商品名称': np.random.choice([f'商品{i}' for i in range(100)], 100000),
    '销售额': np.random.uniform(10, 500, 100000),
    '利润额': np.random.uniform(1, 100, 100000),
    '日期': pd.date_range('2025-12-01', periods=100000, freq='1min')
})

print(f"测试数据: {len(test_data):,}行, {test_data.memory_usage(deep=True).sum() / 1024 / 1024:.2f}MB")

# 缓存原始数据
start_time = time.time()
success = cache.cache_raw_data(
    store_id='store_001',
    date_range=('2025-12-01', '2025-12-11'),
    data=test_data,
    ttl=3600
)
cache_time = time.time() - start_time

if success:
    print(f"✅ 缓存成功，耗时: {cache_time:.3f}秒")
    
    # 读取缓存
    start_time = time.time()
    cached_data = cache.get_raw_data(
        store_id='store_001',
        date_range=('2025-12-01', '2025-12-11')
    )
    read_time = time.time() - start_time
    
    if cached_data is not None:
        print(f"✅ 读取成功，耗时: {read_time:.3f}秒")
        print(f"   数据完整性: {len(cached_data) == len(test_data)}")
        print(f"   加速比: {cache_time / read_time:.1f}x")
    else:
        print("❌ 读取失败")
else:
    print("❌ 缓存失败")

# ========== 测试3: Level 2 - 聚合指标缓存 ==========
print("\n[测试3] Level 2 - 聚合指标缓存...")

test_metrics = {
    '销售额': 12345.67,
    '订单数': 100,
    '利润额': 2345.67,
    '平均客单价': 123.46,
    '商品数': 50
}

success = cache.cache_metrics(
    store_id='store_001',
    date='2025-12-11',
    metrics=test_metrics,
    ttl=3600
)

if success:
    print("✅ 指标缓存成功")
    
    # 读取指标
    cached_metrics = cache.get_metrics(
        store_id='store_001',
        date='2025-12-11'
    )
    
    if cached_metrics:
        print(f"✅ 指标读取成功: {cached_metrics}")
    else:
        print("❌ 指标读取失败")
else:
    print("❌ 指标缓存失败")

# ========== 测试4: Level 3 - 诊断结果缓存 ==========
print("\n[测试4] Level 3 - 诊断结果缓存...")

test_diagnosis = {
    'date': '2025-12-11',
    'urgent': {
        'overflow': {'count': 5, 'loss': 123.45},
        'delivery': {'count': 3, 'extra_cost': 67.89},
        'stockout': {'count': 2, 'loss': 45.67}
    },
    'watch': {
        'traffic_drop': {'count': 10},
        'new_slow': {'count': 8, 'cost': 234.56}
    },
    'highlights': {
        'hot_products': {'count': 5, 'total_sales': 1234.56}
    }
}

success = cache.cache_diagnosis(
    store_ids=['store_001', 'store_002'],
    date_range=('2025-12-01', '2025-12-11'),
    diagnosis=test_diagnosis,
    ttl=3600
)

if success:
    print("✅ 诊断结果缓存成功")
    
    # 读取诊断结果
    cached_diagnosis = cache.get_diagnosis(
        store_ids=['store_001', 'store_002'],
        date_range=('2025-12-01', '2025-12-11')
    )
    
    if cached_diagnosis:
        print(f"✅ 诊断结果读取成功")
        print(f"   紧急问题: {cached_diagnosis['urgent']['overflow']['count']}个穿底订单")
    else:
        print("❌ 诊断结果读取失败")
else:
    print("❌ 诊断结果缓存失败")

# ========== 测试5: 压缩效果测试 ==========
print("\n[测试5] 压缩效果测试...")

# 创建大数据集
large_data = pd.DataFrame({
    'col1': np.random.randint(0, 100, 50000),
    'col2': np.random.uniform(0, 1000, 50000),
    'col3': ['text_' + str(i % 100) for i in range(50000)]
})

original_size = large_data.memory_usage(deep=True).sum()
print(f"原始数据大小: {original_size / 1024 / 1024:.2f}MB")

# 测试压缩缓存
cache_compressed = HierarchicalCacheManager(
    host='localhost',
    port=6379,
    enable_compression=True
)

cache_compressed.cache_raw_data(
    store_id='test_compressed',
    date_range=('2025-12-01', '2025-12-11'),
    data=large_data
)

# 测试不压缩
cache_uncompressed = HierarchicalCacheManager(
    host='localhost',
    port=6379,
    enable_compression=False
)

cache_uncompressed.cache_raw_data(
    store_id='test_uncompressed',
    date_range=('2025-12-01', '2025-12-11'),
    data=large_data
)

print("✅ 压缩测试完成（查看日志中的压缩率）")

# ========== 测试6: 热点分析测试 ==========
print("\n[测试6] 热点分析测试...")

# 模拟访问日志
for i in range(100):
    store_id = np.random.choice(['store_001', 'store_002', 'store_003'], p=[0.6, 0.3, 0.1])
    cache.get_diagnosis(
        store_ids=[store_id],
        date_range=('2025-12-01', '2025-12-11')
    )

# 分析热点
hot_stores = cache.analyze_hot_stores(top_n=2)
print(f"✅ 热点门店: {hot_stores}")

# ========== 测试7: 性能对比测试 ==========
print("\n[测试7] 性能对比测试...")

# 模拟计算密集型操作
def heavy_computation(df):
    """模拟耗时计算"""
    time.sleep(0.1)  # 模拟100ms计算
    return {
        'sum': df['销售额'].sum(),
        'mean': df['销售额'].mean(),
        'count': len(df)
    }

test_df = test_data.head(10000)

# 不使用缓存
print("\n不使用缓存（3次计算）:")
times_no_cache = []
for i in range(3):
    start = time.time()
    result = heavy_computation(test_df)
    elapsed = time.time() - start
    times_no_cache.append(elapsed)
    print(f"  第{i+1}次: {elapsed:.3f}秒")

avg_no_cache = sum(times_no_cache) / len(times_no_cache)
print(f"平均耗时: {avg_no_cache:.3f}秒")

# 使用缓存
print("\n使用缓存（3次读取）:")
times_with_cache = []

# 首次计算并缓存
start = time.time()
result = heavy_computation(test_df)
cache.cache_diagnosis(
    store_ids=['test_perf'],
    date_range=('2025-12-01', '2025-12-11'),
    diagnosis=result
)
first_time = time.time() - start
print(f"  首次（计算+缓存）: {first_time:.3f}秒")

# 后续从缓存读取
for i in range(3):
    start = time.time()
    cached_result = cache.get_diagnosis(
        store_ids=['test_perf'],
        date_range=('2025-12-01', '2025-12-11')
    )
    elapsed = time.time() - start
    times_with_cache.append(elapsed)
    print(f"  第{i+1}次（缓存）: {elapsed:.3f}秒")

avg_with_cache = sum(times_with_cache) / len(times_with_cache)
print(f"平均耗时: {avg_with_cache:.3f}秒")
print(f"加速比: {avg_no_cache / avg_with_cache:.1f}x")

# ========== 测试8: 缓存统计 ==========
print("\n[测试8] 缓存统计信息...")
stats = cache.get_stats()

print(f"✅ 缓存统计:")
print(f"   总键数: {stats.get('total_keys', 0)}")
print(f"   内存使用: {stats.get('used_memory_mb', 0):.2f}MB / {stats.get('max_memory_mb', 0):.2f}MB")
print(f"   内存使用率: {stats.get('memory_usage_pct', 0):.1f}%")
print(f"   缓存命中率: {stats.get('hit_rate', 0):.1f}%")
print(f"   Level 1键数: {stats.get('level_1', 0)}")
print(f"   Level 2键数: {stats.get('level_2', 0)}")
print(f"   Level 3键数: {stats.get('level_3', 0)}")

# ========== 清理测试数据 ==========
print("\n[清理] 清理测试数据...")
cache.clear_all()
print("✅ 清理完成")

print("\n" + "=" * 80)
print(" 测试完成")
print("=" * 80)
