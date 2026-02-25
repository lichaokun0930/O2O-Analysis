# -*- coding: utf-8 -*-
"""
彻底清理所有缓存（Redis + 内存）

运行此脚本后重启后端，确保两个TAB使用相同的计算逻辑
"""

import redis

print("=" * 60)
print("🧹 彻底清理所有缓存")
print("=" * 60)

try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping()
    
    # 获取所有键
    all_keys = r.keys("*")
    print(f"当前Redis中共有 {len(all_keys)} 个键")
    
    if all_keys:
        # 显示所有键
        print("\n所有键:")
        for key in sorted(all_keys):
            print(f"  - {key}")
        
        # 删除所有键
        r.flushdb()
        print(f"\n✅ 已删除所有 {len(all_keys)} 个键")
    else:
        print("Redis中没有缓存数据")
    
except Exception as e:
    print(f"⚠️ Redis操作失败: {e}")

print("\n" + "=" * 60)
print("📋 下一步操作：")
print("=" * 60)
print("1. 重启后端服务")
print("2. 刷新前端页面")
print("3. 对比两个TAB的利润数据")
print("=" * 60)
