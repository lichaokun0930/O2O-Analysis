# -*- coding: utf-8 -*-
"""
配置Redis为1GB内存（适合100家门店）
"""

import redis
import sys

print("=" * 70)
print(" 配置Redis内存限制为1GB")
print("=" * 70)
print()

try:
    # 连接Redis
    print("🔍 连接Redis...")
    client = redis.Redis(
        host='localhost',
        port=6379,
        decode_responses=True,
        socket_connect_timeout=5
    )
    
    # 测试连接
    client.ping()
    print("✅ Redis连接成功")
    print()
    
    # 获取当前配置
    print("📊 当前配置:")
    current_maxmemory = client.config_get('maxmemory')['maxmemory']
    current_policy = client.config_get('maxmemory-policy')['maxmemory-policy']
    
    if current_maxmemory == '0':
        print("   内存限制: 无限制")
    else:
        current_mb = int(current_maxmemory) / 1024 / 1024
        print(f"   内存限制: {current_mb:.0f}MB")
    print(f"   淘汰策略: {current_policy}")
    print()
    
    # 设置新配置
    print("🔧 设置新配置...")
    
    # 设置内存限制为1GB
    client.config_set('maxmemory', '1gb')
    print("   ✅ 内存限制已设置为1GB")
    
    # 设置淘汰策略
    client.config_set('maxmemory-policy', 'allkeys-lru')
    print("   ✅ 淘汰策略已设置为allkeys-lru")
    print()
    
    # 验证新配置
    print("✔️ 验证新配置:")
    new_maxmemory = client.config_get('maxmemory')['maxmemory']
    new_policy = client.config_get('maxmemory-policy')['maxmemory-policy']
    
    new_mb = int(new_maxmemory) / 1024 / 1024
    print(f"   内存限制: {new_mb:.0f}MB")
    print(f"   淘汰策略: {new_policy}")
    print()
    
    # 尝试持久化配置
    print("💾 尝试持久化配置...")
    try:
        client.config_rewrite()
        print("   ✅ 配置已保存到配置文件")
        print("   （重启Redis后配置仍然有效）")
    except redis.ResponseError as e:
        print(f"   ⚠️ 无法保存到配置文件: {e}")
        print("   （配置仅在当前会话有效，重启后需重新配置）")
    
    print()
    print("=" * 70)
    print(" ✅ Redis配置完成")
    print("=" * 70)
    print()
    print("📋 配置摘要:")
    print("   - 内存限制: 1GB")
    print("   - 淘汰策略: allkeys-lru（自动淘汰最少使用的键）")
    print("   - 适用场景: 100家门店，300万行数据")
    print("   - 预期使用率: 40%（健康范围）")
    print()
    print("💡 下一步:")
    print("   1. 运行测试: python 测试V8.4分层缓存.py")
    print("   2. 启动看板: .\\启动看板-调试模式.ps1")
    print("   3. 监控内存: python -c \"import redis; r=redis.Redis(); print(r.info('memory'))\"")
    print()
    
except redis.ConnectionError:
    print("❌ 无法连接到Redis")
    print()
    print("💡 解决方法:")
    print("   1. 检查Redis是否运行: Get-Service Memurai")
    print("   2. 启动Redis: .\\启动Redis.ps1")
    print("   3. 或启动看板（会自动启动Redis）: .\\启动看板-调试模式.ps1")
    print()
    sys.exit(1)
    
except Exception as e:
    print(f"❌ 配置失败: {e}")
    print()
    print("💡 手动配置方法:")
    print("   1. 安装redis-py: pip install redis")
    print("   2. 或使用redis-cli（如果可用）")
    print()
    sys.exit(1)
