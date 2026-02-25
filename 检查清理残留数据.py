# -*- coding: utf-8 -*-
"""
检查和清理残留数据

检查内容：
1. Redis 缓存中的门店数据
2. 预聚合表中已删除门店的残留数据
3. 对比 orders 表和预聚合表的门店列表

使用方式：
    python 检查清理残留数据.py          # 仅检查
    python 检查清理残留数据.py --clean   # 检查并清理
"""

import sys
import argparse
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from database.connection import SessionLocal

# 预聚合表列表
AGGREGATION_TABLES = [
    "store_daily_summary",
    "store_hourly_summary",
    "category_daily_summary",
    "delivery_summary",
    "product_daily_summary"
]


def get_orders_stores():
    """获取 orders 表中的门店列表"""
    session = SessionLocal()
    try:
        result = session.execute(text("""
            SELECT DISTINCT store_name FROM orders WHERE store_name IS NOT NULL
        """))
        stores = [row[0] for row in result.fetchall()]
        return set(stores)
    finally:
        session.close()


def get_aggregation_stores(table_name):
    """获取预聚合表中的门店列表"""
    session = SessionLocal()
    try:
        result = session.execute(text(f"""
            SELECT DISTINCT store_name FROM {table_name} WHERE store_name IS NOT NULL
        """))
        stores = [row[0] for row in result.fetchall()]
        return set(stores)
    except Exception as e:
        print(f"   ⚠️ 表 {table_name} 不存在或查询失败: {e}")
        return set()
    finally:
        session.close()


def check_redis_cache():
    """检查 Redis 缓存"""
    print("\n" + "="*60)
    print("📦 检查 Redis 缓存")
    print("="*60)
    
    try:
        from redis_cache_manager import RedisCacheManager
        cache = RedisCacheManager()
        
        if not cache.enabled:
            print("⚠️ Redis 未启用或未连接")
            return None, []
        
        # 获取所有键
        redis_client = cache.redis_client
        all_keys = []
        
        # 扫描所有键
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match="*", count=1000)
            all_keys.extend([k.decode() if isinstance(k, bytes) else k for k in keys])
            if cursor == 0:
                break
        
        print(f"📊 Redis 中共有 {len(all_keys)} 个键")
        
        # 分类统计
        store_keys = [k for k in all_keys if 'store' in k.lower() or 'order' in k.lower()]
        other_keys = [k for k in all_keys if k not in store_keys]
        
        print(f"   • 门店/订单相关: {len(store_keys)} 个")
        print(f"   • 其他: {len(other_keys)} 个")
        
        # 显示门店相关的键
        if store_keys:
            print(f"\n门店/订单相关的缓存键:")
            for key in store_keys[:20]:  # 最多显示20个
                try:
                    ttl = redis_client.ttl(key)
                    print(f"   • {key} (TTL: {ttl}s)")
                except:
                    print(f"   • {key}")
            if len(store_keys) > 20:
                print(f"   ... 还有 {len(store_keys) - 20} 个")
        
        return cache, store_keys
        
    except ImportError:
        print("⚠️ redis_cache_manager 模块未找到")
        return None, []
    except Exception as e:
        print(f"❌ Redis 检查失败: {e}")
        return None, []


def check_aggregation_tables():
    """检查预聚合表中的残留数据"""
    print("\n" + "="*60)
    print("📊 检查预聚合表残留数据")
    print("="*60)
    
    # 获取 orders 表中的有效门店
    orders_stores = get_orders_stores()
    print(f"\n📦 orders 表中的门店: {len(orders_stores)} 个")
    for store in sorted(orders_stores):
        print(f"   • {store}")
    
    # 检查每个预聚合表
    orphan_data = {}
    
    for table in AGGREGATION_TABLES:
        print(f"\n🔍 检查 {table}...")
        agg_stores = get_aggregation_stores(table)
        
        if not agg_stores:
            print(f"   ✅ 表为空或不存在")
            continue
        
        # 找出孤儿数据（在预聚合表中但不在 orders 表中的门店）
        orphan_stores = agg_stores - orders_stores
        
        if orphan_stores:
            print(f"   ⚠️ 发现 {len(orphan_stores)} 个已删除门店的残留数据:")
            orphan_data[table] = orphan_stores
            for store in sorted(orphan_stores):
                # 统计残留数据量
                session = SessionLocal()
                try:
                    count = session.execute(text(f"""
                        SELECT COUNT(*) FROM {table} WHERE store_name = :store_name
                    """), {"store_name": store}).scalar()
                    print(f"      • {store}: {count} 条")
                finally:
                    session.close()
        else:
            print(f"   ✅ 无残留数据")
    
    return orphan_data


def clean_redis_cache(cache, store_keys):
    """清理 Redis 缓存"""
    print("\n" + "="*60)
    print("🧹 清理 Redis 缓存")
    print("="*60)
    
    if not cache or not cache.enabled:
        print("⚠️ Redis 不可用，跳过")
        return
    
    if not store_keys:
        print("✅ 没有需要清理的缓存")
        return
    
    redis_client = cache.redis_client
    deleted = 0
    
    for key in store_keys:
        try:
            redis_client.delete(key)
            deleted += 1
        except Exception as e:
            print(f"   ⚠️ 删除 {key} 失败: {e}")
    
    print(f"✅ 已清理 {deleted} 个缓存键")


def clean_aggregation_tables(orphan_data):
    """清理预聚合表中的残留数据"""
    print("\n" + "="*60)
    print("🧹 清理预聚合表残留数据")
    print("="*60)
    
    if not orphan_data:
        print("✅ 没有需要清理的残留数据")
        return
    
    session = SessionLocal()
    total_deleted = 0
    
    try:
        for table, stores in orphan_data.items():
            print(f"\n清理 {table}...")
            for store in stores:
                try:
                    result = session.execute(text(f"""
                        DELETE FROM {table} WHERE store_name = :store_name
                    """), {"store_name": store})
                    count = result.rowcount
                    total_deleted += count
                    print(f"   🗑️ {store}: {count} 条")
                except Exception as e:
                    print(f"   ❌ {store}: {e}")
            
            session.commit()
        
        print(f"\n✅ 共清理 {total_deleted} 条残留数据")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 清理失败: {e}")
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description='检查和清理残留数据')
    parser.add_argument('--clean', action='store_true', help='执行清理操作')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🔍 残留数据检查工具")
    print("="*60)
    
    # 1. 检查 Redis 缓存
    cache, store_keys = check_redis_cache()
    
    # 2. 检查预聚合表
    orphan_data = check_aggregation_tables()
    
    # 3. 汇总
    print("\n" + "="*60)
    print("📋 检查结果汇总")
    print("="*60)
    
    has_issues = False
    
    if store_keys:
        print(f"⚠️ Redis 缓存: {len(store_keys)} 个门店/订单相关的键")
        has_issues = True
    else:
        print("✅ Redis 缓存: 无问题")
    
    if orphan_data:
        total_orphan = sum(len(stores) for stores in orphan_data.values())
        print(f"⚠️ 预聚合表: {total_orphan} 个已删除门店的残留数据")
        has_issues = True
    else:
        print("✅ 预聚合表: 无残留数据")
    
    # 4. 清理（如果指定了 --clean）
    if args.clean and has_issues:
        print("\n" + "="*60)
        print("🧹 开始清理...")
        print("="*60)
        
        confirm = input("\n确认清理所有残留数据？(yes/no): ")
        if confirm.lower() == 'yes':
            clean_redis_cache(cache, store_keys)
            clean_aggregation_tables(orphan_data)
            print("\n✅ 清理完成！")
        else:
            print("已取消清理")
    elif has_issues and not args.clean:
        print("\n💡 提示: 使用 --clean 参数执行清理")
        print("   python 检查清理残留数据.py --clean")


if __name__ == "__main__":
    main()
