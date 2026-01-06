#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试今日必做Tab完整流程
模拟真实的数据加载+计算流程
"""

import time
import sys
import pandas as pd
from sqlalchemy import create_engine, text

# 添加路径
sys.path.insert(0, 'components/today_must_do')

print("=" * 80)
print(" 今日必做Tab完整流程测试")
print("=" * 80)

# 1. 导入模块
print("\n[1/6] 导入模块...")
start_time = time.time()

try:
    from redis_cache_manager import REDIS_CACHE_MANAGER
    from diagnosis_analysis import calculate_order_aggregation
    print(f"   ✅ 模块导入完成 ({time.time() - start_time:.2f}秒)")
    
    if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
        print(f"   ✅ Redis缓存: 已启用")
    else:
        print(f"   ⚠️  Redis缓存: 未启用")
except Exception as e:
    print(f"   ❌ 模块导入失败: {e}")
    exit(1)

# 2. 连接数据库
print("\n[2/6] 连接数据库...")
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

# 3. 加载数据（模拟用户选择门店）
print("\n[3/6] 加载订单数据...")
start_time = time.time()

try:
    # 获取第一个门店
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DISTINCT store_name FROM orders WHERE store_name IS NOT NULL LIMIT 1"))
        store_name = result.scalar()
        print(f"   📍 测试门店: {store_name}")
    
    # 加载该门店的所有订单
    query = f"""
    SELECT *
    FROM orders
    WHERE store_name = '{store_name}'
    """
    
    df = pd.read_sql(query, engine)
    load_time = time.time() - start_time
    
    print(f"   ✅ 数据加载完成")
    print(f"   📊 数据量: {len(df):,}行 x {len(df.columns)}列")
    print(f"   ⏱️  耗时: {load_time:.2f}秒")
    
except Exception as e:
    print(f"   ❌ 数据加载失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 4. 测试V8.6订单聚合优化（首次计算）
print("\n[4/6] 测试V8.6订单聚合优化（首次计算）...")

# 清理缓存
if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
    cleared = REDIS_CACHE_MANAGER.clear_pattern("o2o_dashboard:*")
    print(f"   🗑️  已清理 {cleared} 个缓存键")

start_time = time.time()

try:
    # 调用V8.6优化的订单聚合函数
    aggregated_df = calculate_order_aggregation(df)
    calc_time = time.time() - start_time
    
    print(f"   ✅ 订单聚合完成")
    print(f"   📊 聚合后数据: {len(aggregated_df):,}行 x {len(aggregated_df.columns)}列")
    print(f"   ⏱️  耗时: {calc_time:.2f}秒")
    
    if calc_time > 5:
        print(f"   ⚠️  计算时间过长（>{calc_time:.2f}秒）")
    
except Exception as e:
    print(f"   ❌ 订单聚合失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 5. 测试二次计算（缓存命中）
print("\n[5/6] 测试二次计算（缓存命中）...")
start_time = time.time()

try:
    # 再次调用，应该命中缓存
    aggregated_df2 = calculate_order_aggregation(df)
    cache_time = time.time() - start_time
    
    print(f"   ✅ 订单聚合完成")
    print(f"   📊 聚合后数据: {len(aggregated_df2):,}行 x {len(aggregated_df2.columns)}列")
    print(f"   ⏱️  耗时: {cache_time:.2f}秒")
    
    if cache_time > 0 and cache_time < calc_time:
        print(f"   🚀 性能提升: {calc_time/cache_time:.1f}倍")
    elif cache_time == 0:
        print(f"   ⚠️  计算时间过短，无法测量性能提升")
    else:
        print(f"   ⚠️  缓存未生效")
    
except Exception as e:
    print(f"   ❌ 订单聚合失败: {e}")
    import traceback
    traceback.print_exc()
    cache_time = 0  # 设置默认值，避免后续除零错误

# 6. 性能评估
print("\n[6/6] 性能评估...")
print(f"\n   {'阶段':<25} {'耗时':<15} {'状态':<15}")
print(f"   {'-'*25} {'-'*15} {'-'*15}")
print(f"   {'数据加载':<25} {load_time:.2f}秒{'':<10} {'✅' if load_time < 2 else '⚠️'}")
print(f"   {'首次计算':<25} {calc_time:.2f}秒{'':<10} {'✅' if calc_time < 5 else '⚠️'}")
print(f"   {'二次计算（缓存）':<25} {cache_time:.2f}秒{'':<10} {'✅' if cache_time < 1 else '⚠️'}")
print(f"   {'总耗时（首次）':<25} {load_time + calc_time:.2f}秒{'':<10} {'✅' if load_time + calc_time < 10 else '⚠️'}")
print(f"   {'总耗时（二次）':<25} {load_time + cache_time:.2f}秒{'':<10} {'✅' if load_time + cache_time < 3 else '⚠️'}")

total_first = load_time + calc_time
total_second = load_time + cache_time

if total_first < 10 and total_second < 3:
    print(f"\n   ✅ 性能测试通过！")
    print(f"   💡 实际使用体验:")
    print(f"      - 首次加载门店: 约{total_first:.1f}秒")
    print(f"      - 切换回来: 约{total_second:.1f}秒")
    print(f"      - 性能提升: {total_first/total_second:.1f}倍")
else:
    print(f"\n   ⚠️  性能未达标")
    if total_first >= 10:
        print(f"      - 首次加载过慢（{total_first:.2f}秒 > 10秒）")
        if load_time > 2:
            print(f"        → 数据加载慢: {load_time:.2f}秒（建议检查数据库索引）")
        if calc_time > 5:
            print(f"        → 计算过慢: {calc_time:.2f}秒（建议优化算法）")
    if total_second >= 3:
        print(f"      - 二次加载过慢（{total_second:.2f}秒 > 3秒）")
        print(f"        → 缓存未生效或缓存读取慢")

print("\n" + "=" * 80)
print(" 测试完成")
print("=" * 80)

# 清理测试缓存
if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
    REDIS_CACHE_MANAGER.clear_pattern("o2o_dashboard:*")
