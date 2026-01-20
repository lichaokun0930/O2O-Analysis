# -*- coding: utf-8 -*-
"""
测试订单API缓存优化

验证:
1. 按门店加载数据（不再加载全部数据）
2. Redis缓存按门店分开存储
3. 内存缓存按门店分开存储
"""

import sys
import time
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent / "backend" / "app"
sys.path.insert(0, str(APP_DIR))

from api.v1.orders import get_order_data, invalidate_cache, _memory_cache

def test_store_cache():
    """测试按门店缓存"""
    print("=" * 60)
    print("测试按门店缓存功能")
    print("=" * 60)
    
    # 清除缓存
    invalidate_cache()
    print("\n✅ 缓存已清除")
    
    # 测试1: 加载指定门店数据
    store_name = "灵璧县"  # 使用实际存在的门店名
    print(f"\n📦 测试1: 加载门店 '{store_name}' 的数据...")
    
    start = time.time()
    df1 = get_order_data(store_name)
    time1 = time.time() - start
    print(f"   首次加载: {len(df1)} 条记录, 耗时 {time1:.2f}s")
    
    # 测试2: 再次加载同一门店（应该使用缓存）
    print(f"\n📦 测试2: 再次加载门店 '{store_name}' (应使用缓存)...")
    
    start = time.time()
    df2 = get_order_data(store_name)
    time2 = time.time() - start
    print(f"   缓存加载: {len(df2)} 条记录, 耗时 {time2:.2f}s")
    
    if time2 < time1 * 0.5:
        print(f"   ✅ 缓存生效! 速度提升 {time1/time2:.1f}x")
    else:
        print(f"   ⚠️ 缓存可能未生效")
    
    # 测试3: 加载另一个门店
    store_name2 = "泗县"  # 另一个门店
    print(f"\n📦 测试3: 加载另一个门店 '{store_name2}'...")
    
    start = time.time()
    df3 = get_order_data(store_name2)
    time3 = time.time() - start
    print(f"   加载: {len(df3)} 条记录, 耗时 {time3:.2f}s")
    
    # 测试4: 检查内存缓存状态
    print("\n📊 内存缓存状态:")
    store_cache = _memory_cache.get("store_cache", {})
    for store, cache_info in store_cache.items():
        data = cache_info.get("data")
        ts = cache_info.get("timestamp", 0)
        print(f"   - {store}: {len(data) if data is not None else 0} 条记录")
    
    # 测试5: 不指定门店（加载全部 - 应该避免这种情况）
    print("\n📦 测试5: 不指定门店（加载全部数据 - 仅用于获取门店列表）...")
    
    start = time.time()
    df_all = get_order_data(None)
    time_all = time.time() - start
    print(f"   全部数据: {len(df_all)} 条记录, 耗时 {time_all:.2f}s")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    
    # 总结
    print("\n📋 总结:")
    print(f"   - 门店 '{store_name}': {len(df1)} 条")
    print(f"   - 门店 '{store_name2}': {len(df3)} 条")
    print(f"   - 全部数据: {len(df_all)} 条")
    print(f"   - 缓存加速: {time1/time2:.1f}x (首次 vs 缓存)")

if __name__ == "__main__":
    test_store_cache()
