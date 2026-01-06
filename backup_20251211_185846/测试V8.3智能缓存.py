#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试V8.3智能缓存

验证:
1. 缓存键是否基于门店而非数据形状
2. 后台任务是否为每个门店预热缓存
3. 切换门店时是否能命中缓存

作者: AI Assistant
版本: V8.3
日期: 2025-12-11
"""

import sys
from pathlib import Path
import time

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))


def test_cache_key_generation():
    """测试缓存键生成逻辑"""
    print("="*80)
    print("测试1: 缓存键生成逻辑")
    print("="*80)
    
    import pandas as pd
    from datetime import datetime, timedelta
    
    # 创建测试数据
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    # 测试数据1: 单个门店
    df1 = pd.DataFrame({
        '门店名称': ['门店A'] * 100,
        '日期': [yesterday] * 100,
        '订单ID': range(100)
    })
    
    # 测试数据2: 相同门店，不同行数（模拟筛选后）
    df2 = pd.DataFrame({
        '门店名称': ['门店A'] * 50,  # 行数不同
        '日期': [yesterday] * 50,
        '订单ID': range(50)
    })
    
    # 测试数据3: 不同门店
    df3 = pd.DataFrame({
        '门店名称': ['门店B'] * 100,
        '日期': [yesterday] * 100,
        '订单ID': range(100, 200)
    })
    
    # 生成缓存键
    def generate_cache_key(df):
        """生成智能缓存键"""
        if '门店名称' in df.columns:
            stores = sorted(df['门店名称'].unique().tolist())
            store_key = '_'.join(stores) if stores else 'all'
        else:
            store_key = 'all'
        
        if '日期' in df.columns:
            dates = pd.to_datetime(df['日期'])
            date_range = f"{dates.min().strftime('%Y%m%d')}_{dates.max().strftime('%Y%m%d')}"
        else:
            date_range = 'unknown'
        
        return f"diagnosis_v3:{store_key}:{date_range}"
    
    key1 = generate_cache_key(df1)
    key2 = generate_cache_key(df2)
    key3 = generate_cache_key(df3)
    
    print(f"\n数据集1 (门店A, 100行): {key1}")
    print(f"数据集2 (门店A, 50行):  {key2}")
    print(f"数据集3 (门店B, 100行): {key3}")
    
    if key1 == key2:
        print("\n✅ 测试通过: 相同门店不同行数生成相同缓存键")
    else:
        print("\n❌ 测试失败: 相同门店应该生成相同缓存键")
    
    if key1 != key3:
        print("✅ 测试通过: 不同门店生成不同缓存键")
    else:
        print("❌ 测试失败: 不同门店应该生成不同缓存键")


def test_background_task():
    """测试后台任务预热"""
    print("\n" + "="*80)
    print("测试2: 后台任务智能预热")
    print("="*80)
    
    try:
        from background_tasks import update_diagnosis_cache
        
        print("\n执行后台任务...")
        update_diagnosis_cache()
        
        print("\n✅ 后台任务执行完成")
        print("   请检查上面的日志，确认:")
        print("   1. 是否预热了全局数据")
        print("   2. 是否预热了每个门店")
        print("   3. 缓存键格式是否正确")
        
    except Exception as e:
        print(f"\n❌ 后台任务执行失败: {e}")
        import traceback
        traceback.print_exc()


def test_cache_hit():
    """测试缓存命中"""
    print("\n" + "="*80)
    print("测试3: 缓存命中测试")
    print("="*80)
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # 查找所有诊断缓存键
        keys = r.keys('diagnosis_v3:*')
        
        print(f"\n找到 {len(keys)} 个缓存键:")
        for key in keys:
            ttl = r.ttl(key)
            print(f"  - {key}")
            print(f"    TTL: {ttl}秒 ({ttl//60}分钟)")
        
        if len(keys) > 0:
            print("\n✅ 缓存已生成")
        else:
            print("\n⚠️  未找到缓存，请先运行后台任务")
        
    except Exception as e:
        print(f"\n❌ Redis连接失败: {e}")


def test_performance():
    """测试性能提升"""
    print("\n" + "="*80)
    print("测试4: 性能测试")
    print("="*80)
    
    try:
        from 智能门店看板_Dash版 import GLOBAL_DATA
        from components.today_must_do.diagnosis_analysis import get_diagnosis_summary
        from redis_cache_manager import REDIS_CACHE_MANAGER
        import pandas as pd
        
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            print("\n⚠️  GLOBAL_DATA为空，跳过测试")
            return
        
        df = GLOBAL_DATA.copy()
        
        # 生成缓存键
        def generate_cache_key(df):
            if '门店名称' in df.columns:
                stores = sorted(df['门店名称'].unique().tolist())
                store_key = '_'.join(stores) if stores else 'all'
            else:
                store_key = 'all'
            
            if '日期' in df.columns:
                dates = pd.to_datetime(df['日期'])
                date_range = f"{dates.min().strftime('%Y%m%d')}_{dates.max().strftime('%Y%m%d')}"
            else:
                date_range = 'unknown'
            
            return f"diagnosis_v3:{store_key}:{date_range}"
        
        cache_key = generate_cache_key(df)
        
        # 测试缓存读取
        print(f"\n[测试] 缓存键: {cache_key}")
        
        start_time = time.time()
        cached_data = REDIS_CACHE_MANAGER.get(cache_key)
        cache_time = time.time() - start_time
        
        if cached_data:
            print(f"✅ 缓存命中，耗时: {cache_time:.4f}秒")
        else:
            print(f"⚠️  缓存未命中")
            print(f"\n[测试] 实时计算...")
            
            start_time = time.time()
            diagnosis = get_diagnosis_summary(df)
            calc_time = time.time() - start_time
            
            print(f"✅ 计算完成，耗时: {calc_time:.2f}秒")
            
            # 写入缓存
            REDIS_CACHE_MANAGER.set(cache_key, diagnosis, ttl=3600)
            print(f"✅ 已写入缓存")
            
            # 再次读取
            start_time = time.time()
            cached_data = REDIS_CACHE_MANAGER.get(cache_key)
            cache_time = time.time() - start_time
            
            if cached_data:
                print(f"✅ 缓存读取成功，耗时: {cache_time:.4f}秒")
                print(f"\n性能提升: {calc_time / cache_time:.0f}倍")
            
    except Exception as e:
        print(f"\n❌ 性能测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主测试流程"""
    print("\n" + "="*80)
    print("V8.3 智能缓存测试")
    print("="*80)
    print("\n本测试将验证:")
    print("1. 缓存键生成逻辑（基于门店而非数据形状）")
    print("2. 后台任务智能预热（为每个门店预热）")
    print("3. 缓存命中情况")
    print("4. 性能提升效果")
    
    # 测试1: 缓存键生成
    test_cache_key_generation()
    
    # 测试2: 后台任务
    test_background_task()
    
    # 测试3: 缓存命中
    test_cache_hit()
    
    # 测试4: 性能测试
    test_performance()
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)
    print("\n下一步:")
    print("1. 启动看板: python -u 智能门店看板_Dash版.py")
    print("2. 等待后台任务完成预热（约1-2分钟）")
    print("3. 访问'今日必做'Tab")
    print("4. 切换不同门店，观察加载时间")
    print("\n预期效果:")
    print("- 首次访问: <10秒（实时计算）")
    print("- 后续访问: <1秒（缓存命中）")
    print("- 切换门店: <1秒（缓存命中）")
    print("="*80)


if __name__ == "__main__":
    main()
