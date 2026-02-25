# -*- coding: utf-8 -*-
"""
彻底清理所有缓存和预聚合表数据

清理内容：
1. 预聚合表 - 清空所有数据
2. Redis 缓存 - 清空所有键
3. 内存缓存 - 重置

用于重新上传数据前的完全清理
"""

import sys
from pathlib import Path

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


def clear_aggregation_tables():
    """清空所有预聚合表"""
    print("\n" + "="*60)
    print("🗑️ 清空预聚合表")
    print("="*60)
    
    session = SessionLocal()
    total_deleted = 0
    
    try:
        for table in AGGREGATION_TABLES:
            try:
                # 先统计数量
                count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                
                if count > 0:
                    # 清空表
                    session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY"))
                    print(f"   ✅ {table}: 清空 {count:,} 条")
                    total_deleted += count
                else:
                    print(f"   ✅ {table}: 已为空")
                    
            except Exception as e:
                print(f"   ⚠️ {table}: {e}")
        
        session.commit()
        print(f"\n📊 预聚合表共清空: {total_deleted:,} 条")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 清空失败: {e}")
    finally:
        session.close()
    
    return total_deleted


def clear_redis_cache():
    """清空 Redis 缓存"""
    print("\n" + "="*60)
    print("🗑️ 清空 Redis 缓存")
    print("="*60)
    
    try:
        import redis
        
        # 直接连接 Redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # 测试连接
        r.ping()
        
        # 获取所有键的数量
        keys_count = r.dbsize()
        print(f"   📊 当前键数量: {keys_count}")
        
        if keys_count > 0:
            # 清空数据库
            r.flushdb()
            print(f"   ✅ 已清空 {keys_count} 个键")
        else:
            print(f"   ✅ Redis 已为空")
        
        # 同时清空 DB 1（订单看板使用的）
        r1 = redis.Redis(host='localhost', port=6379, db=1)
        keys_count_1 = r1.dbsize()
        if keys_count_1 > 0:
            r1.flushdb()
            print(f"   ✅ DB1 已清空 {keys_count_1} 个键")
        
        return keys_count + keys_count_1
        
    except redis.ConnectionError:
        print("   ⚠️ Redis 未运行或无法连接")
        return 0
    except ImportError:
        print("   ⚠️ redis 模块未安装")
        return 0
    except Exception as e:
        print(f"   ❌ 清空失败: {e}")
        return 0


def clear_memory_cache():
    """清空内存缓存"""
    print("\n" + "="*60)
    print("🗑️ 清空内存缓存")
    print("="*60)
    
    try:
        # 尝试清理 dependencies.py 中的内存缓存
        from backend.app.dependencies import _memory_cache
        
        if _memory_cache:
            _memory_cache.clear()
            print("   ✅ 后端内存缓存已清空")
    except:
        print("   ⚠️ 后端内存缓存不可访问（可能后端未运行）")
    
    try:
        # 尝试清理 hierarchical_cache_manager
        from hierarchical_cache_manager import HierarchicalCacheManager
        cache = HierarchicalCacheManager()
        cache.clear_all()
        print("   ✅ 层级缓存已清空")
    except:
        print("   ⚠️ 层级缓存不可访问")
    
    print("   💡 提示: 重启后端服务可彻底清空内存缓存")


def vacuum_database():
    """优化数据库空间"""
    print("\n" + "="*60)
    print("🔧 优化数据库空间")
    print("="*60)
    
    session = SessionLocal()
    try:
        # 获取原始连接
        connection = session.connection().connection
        old_isolation_level = connection.isolation_level
        connection.set_isolation_level(0)  # 自动提交模式
        cursor = connection.cursor()
        
        # VACUUM ANALYZE
        print("   执行 VACUUM ANALYZE...")
        cursor.execute("VACUUM ANALYZE")
        
        cursor.close()
        connection.set_isolation_level(old_isolation_level)
        
        print("   ✅ 数据库空间优化完成")
        
    except Exception as e:
        print(f"   ⚠️ VACUUM 失败: {e}")
    finally:
        session.close()


def main():
    print("\n" + "="*60)
    print("🧹 彻底清理所有缓存和预聚合数据")
    print("="*60)
    print("\n⚠️ 警告: 此操作将清空以下内容:")
    print("   • 所有预聚合表数据")
    print("   • 所有 Redis 缓存")
    print("   • 内存缓存")
    print("\n这是为重新上传数据做准备。")
    
    # 1. 清空预聚合表
    agg_deleted = clear_aggregation_tables()
    
    # 2. 清空 Redis 缓存
    redis_deleted = clear_redis_cache()
    
    # 3. 清空内存缓存
    clear_memory_cache()
    
    # 4. 优化数据库空间
    vacuum_database()
    
    # 汇总
    print("\n" + "="*60)
    print("✅ 清理完成!")
    print("="*60)
    print(f"   • 预聚合表: 清空 {agg_deleted:,} 条")
    print(f"   • Redis 缓存: 清空 {redis_deleted} 个键")
    print(f"   • 内存缓存: 已重置")
    print(f"   • 数据库: 已优化")
    
    print("\n📋 下一步操作:")
    print("   1. 重启后端服务（彻底清空内存缓存）")
    print("   2. 使用 一键批量导入数据.ps1 上传新数据")
    print("   3. 运行 python 全看板性能优化实施.py 重建预聚合表")


if __name__ == "__main__":
    main()
