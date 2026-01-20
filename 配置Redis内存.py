# -*- coding: utf-8 -*-
"""
配置 Redis 内存限制
设置 maxmemory 为 4GB，淘汰策略为 allkeys-lru
"""
import redis

def configure_redis():
    """配置 Redis 内存"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # 获取当前配置
        print("📊 当前 Redis 配置:")
        current_maxmemory = r.config_get('maxmemory')
        current_policy = r.config_get('maxmemory-policy')
        print(f"   maxmemory: {current_maxmemory}")
        print(f"   maxmemory-policy: {current_policy}")
        
        # 获取内存使用情况
        info = r.info('memory')
        used_memory = info.get('used_memory_human', 'N/A')
        print(f"   当前内存使用: {used_memory}")
        
        # 设置新配置
        print("\n🔧 设置新配置...")
        r.config_set('maxmemory', '4gb')
        r.config_set('maxmemory-policy', 'allkeys-lru')
        
        # 验证配置
        print("\n✅ 配置完成，验证新配置:")
        new_maxmemory = r.config_get('maxmemory')
        new_policy = r.config_get('maxmemory-policy')
        print(f"   maxmemory: {new_maxmemory}")
        print(f"   maxmemory-policy: {new_policy}")
        
        # 清理旧缓存（可选）
        print("\n🧹 清理旧缓存...")
        r.flushdb()
        print("   缓存已清理")
        
        print("\n🎉 Redis 配置完成！")
        print("   - 最大内存: 4GB")
        print("   - 淘汰策略: allkeys-lru（内存满时自动淘汰最久未使用的key）")
        
    except redis.ConnectionError:
        print("❌ 无法连接到 Redis，请确保 Redis 服务正在运行")
    except Exception as e:
        print(f"❌ 配置失败: {e}")

if __name__ == "__main__":
    configure_redis()
