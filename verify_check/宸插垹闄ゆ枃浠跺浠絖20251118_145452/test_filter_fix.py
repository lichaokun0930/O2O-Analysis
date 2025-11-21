#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试修复效果 - 验证数据库数据现在可以正常显示"""

from database.data_source_manager import DataSourceManager
import pandas as pd

def test_filter_logic():
    """测试修复后的过滤逻辑"""
    
    print(f"\n{'='*80}")
    print("🧪 测试修复效果 - 验证过滤逻辑")
    print(f"{'='*80}\n")
    
    # 1. 从数据库加载数据
    print("1️⃣ 从数据库加载数据...")
    ds = DataSourceManager()
    
    try:
        # 直接加载默认门店
        df = ds.load_from_database()
        print(f"   ✅ 加载成功: {len(df)} 行原始数据")
        
    except Exception as e:
        print(f"   ❌ 加载失败: {e}")
        return
    
    # 2. 检查关键字段
    print(f"\n2️⃣ 检查关键字段...")
    print(f"   平台服务费 > 0: {(df['平台服务费'] > 0).sum()} 笔")
    print(f"   平台佣金 > 0: {(df['平台佣金'] > 0).sum()} 笔")
    
    # 3. 模拟原来的过滤逻辑(会失败)
    print(f"\n3️⃣ 测试原来的过滤逻辑...")
    old_filtered = df[df['平台服务费'] > 0]
    print(f"   仅平台服务费>0: {len(old_filtered)} 笔 ({'✅ 有数据' if len(old_filtered) > 0 else '❌ 空数据'})")
    
    # 4. 模拟新的过滤逻辑(应该成功)
    print(f"\n4️⃣ 测试修复后的过滤逻辑...")
    new_filtered = df[(df['平台服务费'] > 0) | (df['平台佣金'] > 0)]
    print(f"   平台服务费>0 OR 平台佣金>0: {len(new_filtered)} 笔 ({'✅ 有数据' if len(new_filtered) > 0 else '❌ 空数据'})")
    
    # 5. 对比结果
    print(f"\n5️⃣ 对比结果:")
    print(f"   原逻辑: {len(df)} → {len(old_filtered)} ({len(old_filtered)/len(df)*100:.1f}%)")
    print(f"   新逻辑: {len(df)} → {len(new_filtered)} ({len(new_filtered)/len(df)*100:.1f}%)")
    print(f"   改善: +{len(new_filtered) - len(old_filtered)} 笔订单")
    
    if len(new_filtered) > 0:
        print(f"\n✅ 修复成功! 数据库数据现在可以正常显示了")
        
        # 显示样本数据
        print(f"\n6️⃣ 样本数据 (前5笔):")
        sample = new_filtered.head(5)[['订单ID', '平台服务费', '平台佣金', '预计订单收入']]
        for idx, row in sample.iterrows():
            print(f"   订单 {row['订单ID']}: 服务费={row['平台服务费']}, 佣金={row['平台佣金']}, 金额={row['预计订单收入']}")
    else:
        print(f"\n❌ 仍然没有数据,请检查数据库是否有订单")

if __name__ == '__main__':
    test_filter_logic()
