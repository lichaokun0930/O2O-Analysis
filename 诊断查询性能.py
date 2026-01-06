#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断数据库查询性能
检查索引、数据量、查询速度
"""
import sys
import io
import time
from datetime import datetime, timedelta

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("="*70)
print("  数据库查询性能诊断")
print("="*70)
print()

# 1. 检查数据量
print("📊 [1/5] 检查数据量...")
try:
    from database.connection import get_db
    from database.models import Order
    from sqlalchemy import func, text
    
    db = next(get_db())
    
    # 总订单数
    total_count = db.query(Order).count()
    print(f"   ✅ 订单总数: {total_count:,} 条")
    
    # 按门店统计
    store_counts = db.query(
        Order.store_name, 
        func.count(Order.id).label('count')
    ).group_by(Order.store_name).all()
    
    print(f"   📍 门店数量: {len(store_counts)} 个")
    for store_name, count in store_counts[:5]:
        print(f"      • {store_name}: {count:,} 条")
    
    if len(store_counts) > 5:
        print(f"      ... 还有 {len(store_counts) - 5} 个门店")
    
except Exception as e:
    print(f"   ❌ 检查失败: {e}")

print()

# 2. 检查索引
print("🔍 [2/5] 检查索引...")
try:
    result = db.execute(text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'orders'
        ORDER BY indexname
    """))
    
    indexes = list(result)
    print(f"   ✅ 已创建索引: {len(indexes)} 个")
    
    # 检查关键索引
    key_indexes = ['idx_orders_store_date', 'idx_orders_store_name', 'idx_orders_date_desc']
    for key_idx in key_indexes:
        exists = any(idx[0] == key_idx for idx in indexes)
        status = "✅" if exists else "❌"
        print(f"   {status} {key_idx}: {'已创建' if exists else '未创建'}")
    
    if len(indexes) < 5:
        print(f"   ⚠️ 索引较少，建议运行: python database/create_indexes.py")
    
except Exception as e:
    print(f"   ❌ 检查失败: {e}")

print()

# 3. 测试查询速度
print("⏱️  [3/5] 测试查询速度...")
try:
    # 测试1: 简单查询
    start = time.time()
    result = db.query(Order).limit(1000).all()
    elapsed1 = time.time() - start
    print(f"   ✅ 查询 1000 条: {elapsed1:.2f} 秒")
    
    # 测试2: 带过滤的查询
    if store_counts:
        store_name = store_counts[0][0]
        start = time.time()
        result = db.query(Order).filter(Order.store_name == store_name).limit(1000).all()
        elapsed2 = time.time() - start
        print(f"   ✅ 门店过滤查询: {elapsed2:.2f} 秒")
    
    # 测试3: 日期范围查询
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    start = time.time()
    result = db.query(Order).filter(
        Order.date >= start_date,
        Order.date <= end_date
    ).limit(1000).all()
    elapsed3 = time.time() - start
    print(f"   ✅ 日期范围查询: {elapsed3:.2f} 秒")
    
    # 性能评估
    avg_time = (elapsed1 + elapsed2 + elapsed3) / 3
    if avg_time < 0.5:
        print(f"   🎉 性能优秀 (平均 {avg_time:.2f}秒)")
    elif avg_time < 2:
        print(f"   ✅ 性能良好 (平均 {avg_time:.2f}秒)")
    elif avg_time < 5:
        print(f"   ⚠️ 性能一般 (平均 {avg_time:.2f}秒)")
    else:
        print(f"   ❌ 性能较差 (平均 {avg_time:.2f}秒)")
        print(f"   💡 建议: 创建索引或优化查询")
    
except Exception as e:
    print(f"   ❌ 测试失败: {e}")

print()

# 4. 检查 Redis 缓存
print("💾 [4/5] 检查 Redis 缓存...")
try:
    from redis_cache_manager import REDIS_CACHE_MANAGER
    
    if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
        print(f"   ✅ Redis 缓存已启用")
        
        # 获取缓存统计
        stats = REDIS_CACHE_MANAGER.get_stats()
        if stats:
            print(f"   📊 缓存统计:")
            print(f"      • 命中次数: {stats.get('hits', 0)}")
            print(f"      • 未命中次数: {stats.get('misses', 0)}")
            hit_rate = stats.get('hit_rate', 0)
            print(f"      • 命中率: {hit_rate:.1f}%")
            
            if hit_rate > 50:
                print(f"   🎉 缓存效果优秀")
            elif hit_rate > 20:
                print(f"   ✅ 缓存效果良好")
            else:
                print(f"   ⚠️ 缓存命中率较低")
    else:
        print(f"   ❌ Redis 缓存未启用")
        print(f"   💡 建议: 启动 Redis 服务")
    
except Exception as e:
    print(f"   ⚠️ 检查失败: {e}")

print()

# 5. 模拟真实查询
print("🎯 [5/5] 模拟真实查询...")
try:
    if store_counts:
        store_name = store_counts[0][0]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"   查询条件:")
        print(f"      • 门店: {store_name}")
        print(f"      • 日期: {start_date.date()} ~ {end_date.date()}")
        
        start = time.time()
        
        # 模拟 data_source_manager 的查询
        from database.models import Product
        query = db.query(Order, Product.store_code).outerjoin(
            Product, Order.barcode == Product.barcode
        )
        query = query.filter(Order.store_name == store_name)
        query = query.filter(Order.date >= start_date)
        query = query.filter(Order.date <= end_date)
        
        # 先获取数量
        count = query.count()
        print(f"   📊 匹配记录: {count:,} 条")
        
        # 执行查询
        print(f"   ⏳ 执行查询...")
        results = query.all()
        
        elapsed = time.time() - start
        print(f"   ✅ 查询完成: {elapsed:.2f} 秒")
        
        # 性能评估
        if elapsed < 3:
            print(f"   🎉 查询速度优秀")
        elif elapsed < 10:
            print(f"   ✅ 查询速度良好")
        elif elapsed < 30:
            print(f"   ⚠️ 查询速度较慢")
        else:
            print(f"   ❌ 查询速度很慢")
            print(f"   💡 建议:")
            print(f"      1. 创建索引: python database/create_indexes.py")
            print(f"      2. 启用 Redis 缓存")
            print(f"      3. 限制查询范围")
    
except Exception as e:
    print(f"   ❌ 查询失败: {e}")

print()
print("="*70)
print("  诊断完成")
print("="*70)
