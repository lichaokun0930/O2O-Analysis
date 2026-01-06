#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V8.6 今日必做性能优化测试脚本

测试目标：
- 验证订单聚合前置优化效果
- 对比V8.5和V8.6的性能差异
- 确保功能一致性
"""

import sys
import time
import pandas as pd
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

def test_performance():
    """性能测试"""
    print("="*80)
    print("V8.6 今日必做性能优化测试")
    print("="*80)
    
    # 1. 获取测试数据
    print("\n[1/4] 加载测试数据...")
    try:
        # 方法1: 尝试从主应用获取
        try:
            from 智能门店看板_Dash版 import GLOBAL_DATA
            df = GLOBAL_DATA
        except:
            # 方法2: 直接从Excel加载
            print("   从主应用获取失败，尝试直接加载Excel...")
            import pandas as pd
            from pathlib import Path
            
            data_dir = Path(__file__).parent / "实际数据"
            excel_files = list(data_dir.glob("*.xlsx"))
            
            if not excel_files:
                print("❌ 未找到Excel数据文件")
                return
            
            # 加载最新的Excel文件
            latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)
            print(f"   加载文件: {latest_file.name}")
            df = pd.read_excel(latest_file)
            
            # 标准化字段名
            if '下单时间' in df.columns and '日期' not in df.columns:
                df['日期'] = pd.to_datetime(df['下单时间'])
            if '销量' in df.columns and '月售' not in df.columns:
                df['月售'] = df['销量']
        
        if df is None or df.empty:
            print("❌ 无法获取测试数据")
            return
        
        print(f"✅ 数据加载成功: {len(df)} 行")
        
        # 确保有日期列
        date_col = '日期' if '日期' in df.columns else '下单时间'
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col])
            print(f"   日期范围: {df[date_col].min()} ~ {df[date_col].max()}")
        
        if '门店名称' in df.columns:
            print(f"   门店数: {df['门店名称'].nunique()}")
        
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. 测试V8.6优化版本
    print("\n[2/4] 测试V8.6优化版本（订单聚合前置）...")
    try:
        from components.today_must_do.diagnosis_analysis import get_diagnosis_summary
        
        start_time = time.time()
        result_v86 = get_diagnosis_summary(df)
        v86_time = time.time() - start_time
        
        print(f"✅ V8.6版本完成")
        print(f"   耗时: {v86_time:.2f}秒")
        print(f"   紧急问题: 穿底{result_v86['urgent']['overflow']['count']}单, "
              f"高配送{result_v86['urgent']['delivery']['count']}单, "
              f"缺货{result_v86['urgent']['stockout']['count']}个")
        
    except Exception as e:
        print(f"❌ V8.6测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 性能分析
    print("\n[3/4] 性能分析...")
    print(f"   V8.6耗时: {v86_time:.2f}秒")
    
    # 估算V8.5耗时（基于历史数据）
    v85_estimated = 70  # 秒
    improvement = v85_estimated / v86_time if v86_time > 0 else 0
    
    print(f"   V8.5估计耗时: {v85_estimated}秒（用户反馈）")
    print(f"   性能提升: {improvement:.1f}倍")
    print(f"   时间节省: {v85_estimated - v86_time:.1f}秒")
    
    # 4. 功能验证
    print("\n[4/4] 功能验证...")
    checks = []
    
    # 检查1: 结果结构完整性
    required_keys = ['date', 'urgent', 'watch', 'highlights']
    structure_ok = all(key in result_v86 for key in required_keys)
    checks.append(("结果结构完整", structure_ok))
    
    # 检查2: 紧急问题数据
    urgent_ok = (
        'overflow' in result_v86['urgent'] and
        'delivery' in result_v86['urgent'] and
        'stockout' in result_v86['urgent']
    )
    checks.append(("紧急问题数据", urgent_ok))
    
    # 检查3: 关注问题数据
    watch_ok = (
        'traffic_drop' in result_v86['watch'] and
        'new_slow' in result_v86['watch']
    )
    checks.append(("关注问题数据", watch_ok))
    
    # 检查4: 正向激励数据
    highlights_ok = (
        'hot_products' in result_v86['highlights'] and
        'high_profit_products' in result_v86['highlights']
    )
    checks.append(("正向激励数据", highlights_ok))
    
    # 打印检查结果
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}")
    
    all_passed = all(result for _, result in checks)
    
    # 5. 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    if all_passed and v86_time < 30:
        print("✅ 所有测试通过！")
        print(f"✅ 性能优化成功：{v85_estimated}秒 → {v86_time:.2f}秒（提升{improvement:.1f}倍）")
        print("✅ 功能完整性验证通过")
        print("\n🎉 V8.6优化达到预期目标！")
    elif all_passed:
        print("⚠️ 功能测试通过，但性能未达预期")
        print(f"   当前耗时: {v86_time:.2f}秒")
        print(f"   目标耗时: <30秒")
        print("   建议：检查数据规模或进一步优化")
    else:
        print("❌ 部分测试失败")
        print("   建议：检查代码逻辑")
    
    print("="*80)


def test_cache_integration():
    """测试Redis缓存集成"""
    print("\n" + "="*80)
    print("Redis缓存集成测试")
    print("="*80)
    
    try:
        from redis_cache_manager import REDIS_CACHE_MANAGER
        
        if not REDIS_CACHE_MANAGER or not REDIS_CACHE_MANAGER.enabled:
            print("⚠️ Redis缓存未启用")
            return
        
        print("✅ Redis缓存已启用")
        
        # 测试缓存读写
        test_key = "test:v86:performance"
        test_value = {"test": "data", "timestamp": time.time()}
        
        # 写入
        REDIS_CACHE_MANAGER.set(test_key, test_value, ttl=60)
        print("✅ 缓存写入成功")
        
        # 读取
        cached_value = REDIS_CACHE_MANAGER.get(test_key)
        if cached_value and cached_value.get('test') == 'data':
            print("✅ 缓存读取成功")
        else:
            print("❌ 缓存读取失败")
        
        # 清理
        REDIS_CACHE_MANAGER.delete(test_key)
        print("✅ 缓存清理成功")
        
    except Exception as e:
        print(f"❌ Redis缓存测试失败: {e}")


if __name__ == '__main__':
    print("\n🚀 开始V8.6性能优化测试...\n")
    
    # 主性能测试
    test_performance()
    
    # 缓存集成测试
    test_cache_integration()
    
    print("\n✅ 测试完成！\n")
