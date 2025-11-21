# -*- coding: utf-8 -*-
"""测试缓存逻辑"""

# 模拟场景1: 缓存完全为空
print("场景1: 首次加载(缓存为空)")
cached_agg = None
cached_comparison = None
cache_version = "v1"
trigger = "v1"

cache_valid = (
    cached_agg is not None 
    and cached_comparison is not None 
    and cache_version == trigger
)
print(f"  cache_valid = {cache_valid}")
print(f"  结论: {'会计算环比' if not cache_valid else '不会计算环比'}")

# 模拟场景2: 缓存存在但环比为空
print("\n场景2: 缓存存在但环比为空")
cached_agg = [{"订单ID": "001"}]  # 有数据
cached_comparison = {'comparison_metrics': {}, 'channel_comparison': {}}  # 空环比
cache_version = "v1"
trigger = "v1"

cache_valid = (
    cached_agg is not None 
    and cached_comparison is not None 
    and cache_version == trigger
)
print(f"  初始 cache_valid = {cache_valid}")

if cache_valid:
    comparison_metrics = cached_comparison.get('comparison_metrics', {})
    channel_comparison = cached_comparison.get('channel_comparison', {})
    print(f"  comparison_metrics = {comparison_metrics}")
    print(f"  channel_comparison = {channel_comparison}")
    
    # 检查环比是否为空
    if not comparison_metrics or not channel_comparison:
        print(f"  检测到环比为空,设置 cache_valid = False")
        cache_valid = False
        comparison_metrics = None
        channel_comparison = None

print(f"  最终 cache_valid = {cache_valid}")
print(f"  结论: {'会计算环比' if not cache_valid else '不会计算环比'}")

# 模拟场景3: 缓存有效且环比有数据
print("\n场景3: 缓存有效且环比有数据")
cached_agg = [{"订单ID": "001"}]
cached_comparison = {
    'comparison_metrics': {'订单数': {'current': 100, 'previous': 90, 'change_rate': 11.1}},
    'channel_comparison': {'饿了么': {'订单数': {'current': 50, 'previous': 45}}}
}
cache_version = "v1"
trigger = "v1"

cache_valid = (
    cached_agg is not None 
    and cached_comparison is not None 
    and cache_version == trigger
)
print(f"  初始 cache_valid = {cache_valid}")

if cache_valid:
    comparison_metrics = cached_comparison.get('comparison_metrics', {})
    channel_comparison = cached_comparison.get('channel_comparison', {})
    print(f"  comparison_metrics = {list(comparison_metrics.keys())}")
    print(f"  channel_comparison = {list(channel_comparison.keys())}")
    
    if not comparison_metrics or not channel_comparison:
        print(f"  检测到环比为空,设置 cache_valid = False")
        cache_valid = False

print(f"  最终 cache_valid = {cache_valid}")
print(f"  结论: {'会计算环比' if not cache_valid else '使用缓存环比'}")

print("\n✅ 测试完成")
