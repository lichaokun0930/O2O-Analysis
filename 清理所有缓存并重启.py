# -*- coding: utf-8 -*-
"""
清理所有缓存（Redis + 内存）

运行此脚本后重启后端，确保使用原始查询
"""

import redis
import sys

print("=" * 60)
print("🧹 清理所有缓存")
print("=" * 60)

# 清理 Redis 缓存
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping()
    
    # 获取所有订单相关的缓存键
    patterns = [
        "order_data_cache:*",
        "order_data_timestamp:*",
        "order_data_version:*",
        "store_comparison_all:*",
        "store_comparison_timestamp:*",
        "aggregation:*",
        "cache:*"
    ]
    
    total_deleted = 0
    for pattern in patterns:
        keys = r.keys(pattern)
        if keys:
            deleted = r.delete(*keys)
            total_deleted += deleted
            print(f"  ✅ 删除 {pattern}: {deleted} 个键")
    
    # 也删除不带通配符的键
    single_keys = [
        "order_data_cache",
        "order_data_timestamp", 
        "order_data_version"
    ]
    for key in single_keys:
        if r.exists(key):
            r.delete(key)
            total_deleted += 1
            print(f"  ✅ 删除 {key}")
    
    print(f"\n✅ Redis 缓存清理完成，共删除 {total_deleted} 个键")
    
except Exception as e:
    print(f"⚠️ Redis 清理失败（可能未运行）: {e}")

print("\n" + "=" * 60)
print("📋 下一步操作：")
print("=" * 60)
print("1. 重启后端服务")
print("2. 刷新前端页面")
print("3. 检查运营诊断中心的利润数据是否正确")
print("")
print("预期结果（兴化店全部日期）：")
print("  - 订单数：~6,091（过滤异常订单后）")
print("  - 销售额：¥173,026.80")
print("  - 利润：¥17,268.42（接近用户期望的¥17,341）")
print("=" * 60)
