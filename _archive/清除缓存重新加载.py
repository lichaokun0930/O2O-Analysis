"""清除Redis缓存,强制从数据库重新加载数据"""
import redis

try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
    
    # 删除所有门店数据缓存
    pattern = "store_data:*"
    keys = r.keys(pattern)
    if keys:
        deleted = r.delete(*keys)
        print(f"✅ 已删除 {deleted} 个缓存键: {pattern}")
    else:
        print(f"ℹ️ 未找到匹配的缓存键: {pattern}")
    
    # 删除完整数据缓存
    pattern = "store_full_data:*"
    keys = r.keys(pattern)
    if keys:
        deleted = r.delete(*keys)
        print(f"✅ 已删除 {deleted} 个完整数据缓存: {pattern}")
    else:
        print(f"ℹ️ 未找到匹配的缓存键: {pattern}")
    
    print("\n✅ 缓存清除完成! 请重新在看板中选择门店加载数据。")
    
except Exception as e:
    print(f"❌ 清除缓存失败: {e}")
