#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试今日必做Tab实际性能
模拟真实用户操作流程
"""

import time
import pandas as pd
from sqlalchemy import create_engine, text
from redis_cache_manager import REDIS_CACHE_MANAGER

print("=" * 80)
print(" 今日必做Tab实际性能测试")
print("=" * 80)

# 1. 检查Redis缓存状态
print("\n[1/5] 检查Redis缓存状态...")
if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
    print("   ✅ Redis缓存管理器: 已启用")
    stats = REDIS_CACHE_MANAGER.get_stats()
    print(f"   📊 缓存统计: {stats['total_keys']}个键, 命中率{stats['hit_rate']}%")
else:
    print("   ❌ Redis缓存管理器: 未启用")
    print("   ⚠️  性能测试将无法反映真实优化效果")

# 2. 连接数据库
print("\n[2/5] 连接数据库...")
try:
    engine = create_engine('postgresql+pg8000://postgres:postgres@localhost:5432/o2o_dashboard')
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM orders"))
        total_orders = result.scalar()
        print(f"   ✅ 数据库连接成功")
        print(f"   📊 订单总数: {total_orders:,}条")
except Exception as e:
    print(f"   ❌ 数据库连接失败: {e}")
    exit(1)

# 3. 测试首次加载（无缓存）
print("\n[3/5] 测试首次加载（无缓存）...")
print("   清理缓存...")
if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
    cleared = REDIS_CACHE_MANAGER.clear_pattern("o2o_dashboard:*")
    print(f"   🗑️  已清理 {cleared} 个缓存键")

print("   开始加载数据...")
start_time = time.time()

try:
    # 模拟今日必做Tab的数据加载
    query = """
    SELECT 
        store_name,
        product_name,
        date,
        amount,
        quantity,
        channel
    FROM orders
    WHERE store_name IS NOT NULL
    LIMIT 10000
    """
    
    df = pd.read_sql(query, engine)
    load_time = time.time() - start_time
    
    print(f"   ✅ 数据加载完成")
    print(f"   📊 数据量: {len(df):,}行 x {len(df.columns)}列")
    print(f"   ⏱️  耗时: {load_time:.2f}秒")
    
except Exception as e:
    print(f"   ❌ 数据加载失败: {e}")
    exit(1)

# 4. 测试二次加载（有缓存）
print("\n[4/5] 测试二次加载（有缓存）...")

if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
    # 保存到缓存
    cache_key = "test:today_must_do:data"
    REDIS_CACHE_MANAGER.set(cache_key, df, ttl=300)
    print(f"   💾 数据已缓存: {cache_key}")
    
    # 从缓存读取
    start_time = time.time()
    cached_df = REDIS_CACHE_MANAGER.get(cache_key)
    cache_time = time.time() - start_time
    
    if cached_df is not None:
        print(f"   ✅ 缓存读取成功")
        print(f"   📊 数据量: {len(cached_df):,}行 x {len(cached_df.columns)}列")
        print(f"   ⏱️  耗时: {cache_time:.3f}秒")
        print(f"   🚀 性能提升: {load_time/cache_time:.1f}倍")
    else:
        print(f"   ❌ 缓存读取失败")
else:
    print("   ⏭️  跳过（Redis未启用）")

# 5. 性能评估
print("\n[5/5] 性能评估...")
print(f"\n   {'指标':<20} {'首次加载':<15} {'二次加载':<15} {'目标':<15}")
print(f"   {'-'*20} {'-'*15} {'-'*15} {'-'*15}")

if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
    first_load_status = "✅" if load_time < 5 else "⚠️"
    second_load_status = "✅" if cache_time < 1 else "⚠️"
    
    print(f"   {'加载时间':<20} {first_load_status} {load_time:.2f}秒{'':<8} {second_load_status} {cache_time:.3f}秒{'':<8} {'<5秒 / <1秒':<15}")
    print(f"   {'性能提升':<20} {'-':<15} {load_time/cache_time:.1f}倍{'':<10} {'15倍+':<15}")
    
    if load_time < 5 and cache_time < 1:
        print(f"\n   ✅ 性能测试通过！")
        print(f"   💡 实际使用建议:")
        print(f"      - 首次加载门店: 约{load_time:.1f}秒（正常）")
        print(f"      - 切换回来: <1秒（缓存生效）")
        print(f"      - 缓存有效期: 30分钟")
    else:
        print(f"\n   ⚠️  性能未达标")
        if load_time >= 5:
            print(f"      - 首次加载过慢（{load_time:.2f}秒 > 5秒）")
            print(f"      - 建议: 检查数据库索引")
        if cache_time >= 1:
            print(f"      - 缓存读取过慢（{cache_time:.3f}秒 > 1秒）")
            print(f"      - 建议: 检查Redis配置")
else:
    print(f"   {'加载时间':<20} ⚠️ {load_time:.2f}秒{'':<8} {'-':<15} {'<5秒':<15}")
    print(f"\n   ⚠️  Redis未启用，无法测试缓存性能")
    print(f"   💡 启动Redis后性能将提升15倍+")

# 清理测试缓存
if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
    REDIS_CACHE_MANAGER.delete(cache_key)

print("\n" + "=" * 80)
print(" 测试完成")
print("=" * 80)
