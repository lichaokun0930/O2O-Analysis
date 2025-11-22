"""
清理Redis缓存脚本
解决看板显示旧数据的问题
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import redis
    
    # 直接连接Redis
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        decode_responses=True,
        socket_connect_timeout=2
    )
    
    # 测试连接
    redis_client.ping()
    print("Redis连接成功")
    
    # 获取所有key
    keys = redis_client.keys('*')
    print(f"\n发现 {len(keys)} 个缓存key")
    
    if keys:
        # 显示部分key
        print("\n前10个key:")
        for i, key in enumerate(keys[:10], 1):
            print(f"  {i}. {key}")
        
        # 删除所有key
        deleted = redis_client.delete(*keys)
        print(f"\n已删除 {deleted} 个缓存key")
        
        # 验证
        remaining = redis_client.keys('*')
        print(f"剩余 {len(remaining)} 个key")
        
        print("\n" + "="*60)
        print("Redis缓存已清空!")
        print("="*60)
        print("\n下一步: 重启看板")
        print("  .\\启动看板.ps1")
    else:
        print("Redis中没有缓存数据")
        
except redis.ConnectionError:
    print("无法连接Redis,请确保Redis服务已启动")
    print("启动Redis: .\\启动Redis.ps1")
except Exception as e:
    print(f"清理缓存失败: {e}")
    import traceback
    traceback.print_exc()
