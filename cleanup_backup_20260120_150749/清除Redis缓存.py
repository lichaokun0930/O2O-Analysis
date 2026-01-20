"""
清除Redis缓存

用于部署新版本后清除旧缓存
"""

import redis

try:
    # 连接Redis
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # 测试连接
    r.ping()
    print("✅ Redis连接成功")
    
    # 清除所有缓存
    r.flushdb()
    print("✅ Redis缓存已清除")
    
    # 显示统计
    info = r.info('stats')
    print(f"\n📊 Redis统计:")
    print(f"   总连接数: {info.get('total_connections_received', 0)}")
    print(f"   总命令数: {info.get('total_commands_processed', 0)}")
    
except redis.ConnectionError:
    print("❌ 无法连接到Redis，请确保Redis服务正在运行")
except Exception as e:
    print(f"❌ 错误: {e}")
