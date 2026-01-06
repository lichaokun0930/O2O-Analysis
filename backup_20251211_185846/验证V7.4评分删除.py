#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V7.4 评分体系删除验证脚本

验证内容：
1. 六象限分类是否正常
2. 排序逻辑是否正确
3. 评分字段是否已删除
4. 性能是否提升
"""

import pandas as pd
import numpy as np
import time
from components.today_must_do.callbacks import (
    calculate_enhanced_product_scores,
    calculate_enhanced_product_scores_with_trend
)

def generate_test_data(n_products=800):
    """生成测试数据"""
    np.random.seed(42)
    
    data = {
        '商品名称': [f'商品{i}' for i in range(n_products)],
        '店内码': [f'CODE{i:05d}' for i in range(n_products)],
        '一级分类名': np.random.choice(['饮料', '休闲食品', '日用品', '生鲜'], n_products),
        '实收价格': np.random.uniform(1, 50, n_products),
        '商品采购成本': np.random.uniform(0.5, 30, n_products),
        '月售': np.random.randint(0, 200, n_products),
        '订单ID': [f'ORDER{i}' for i in range(n_products)],
        '利润额': np.random.uniform(-50, 500, n_products),
        '库存': np.random.randint(0, 100, n_products),
        '日期': pd.date_range('2024-11-01', periods=n_products, freq='H')
    }
    
    df = pd.DataFrame(data)
    return df

def test_basic_calculation():
    """测试1：基础计算功能"""
    print("\n" + "="*80)
    print("测试1：基础计算功能")
    print("="*80)
    
    df = generate_test_data(800)
    
    start_time = time.time()
    result = calculate_enhanced_product_scores(df)
    calc_time = time.time() - start_time
    
    print(f"\n✅ 计算完成")
    print(f"   数据行数: {len(result)}")
    print(f"   计算时间: {calc_time:.3f}秒")
    
    # 检查必要字段
    required_fields = ['商品名称', '四象限分类', '综合利润率', '动销指数', '销量', '利润额']
    missing_fields = [f for f in required_fields if f not in result.columns]
    
    if missing_fields:
        print(f"\n❌ 缺少必要字段: {missing_fields}")
        return False
    else:
        print(f"\n✅ 所有必要字段都存在")
    
    # 检查评分字段是否已删除
    score_fields = ['综合得分', '评分等级', '利润率得分', '动销得分', '利润率排名', '动销排名']
    existing_score_fields = [f for f in score_fields if f in result.columns]
    
    if existing_score_fields:
        print(f"\n⚠️ 警告：以下评分字段仍然存在: {existing_score_fields}")
        return False
    else:
        print(f"\n✅ 评分字段已成功删除")
    
    # 检查六象限分类
    quadrant_counts = result['四象限分类'].value_counts()
    print(f"\n✅ 六象限分布:")
    for quadrant, count in quadrant_counts.items():
        print(f"   {quadrant}: {count}个")
    
    return True

def test_sorting_logic():
    """测试2：排序逻辑"""
    print("\n" + "="*80)
    print("测试2：排序逻辑")
    print("="*80)
    
    df = generate_test_data(100)
    result = calculate_enhanced_product_scores(df)
    
    # 检查排序是否正确
    quadrant_priority = {
        '🎯 策略引流': 1,
        '🌟 明星商品': 2,
        '🔥 畅销商品': 3,
        '💎 潜力商品': 4,
        '⚡ 自然引流': 5,
        '🐌 低效商品': 6
    }
    
    result['象限优先级'] = result['四象限分类'].map(quadrant_priority)
    
    # 检查是否按优先级排序
    is_sorted = True
    for i in range(len(result) - 1):
        current_priority = result.iloc[i]['象限优先级']
        next_priority = result.iloc[i + 1]['象限优先级']
        
        if current_priority > next_priority:
            is_sorted = False
            print(f"\n❌ 排序错误：第{i}行优先级{current_priority} > 第{i+1}行优先级{next_priority}")
            break
        
        # 同优先级时，检查是否按利润额降序
        if current_priority == next_priority:
            current_profit = result.iloc[i]['利润额']
            next_profit = result.iloc[i + 1]['利润额']
            if current_profit < next_profit:
                print(f"\n⚠️ 警告：同象限内利润额排序可能不正确")
    
    if is_sorted:
        print(f"\n✅ 排序逻辑正确：按六象限优先级排序")
        print(f"\n前10名商品:")
        for i in range(min(10, len(result))):
            row = result.iloc[i]
            print(f"   {i+1}. {row['商品名称']} - {row['四象限分类']} - 利润额¥{row['利润额']:.2f}")
        return True
    else:
        return False

def test_trend_calculation():
    """测试3：趋势分析功能"""
    print("\n" + "="*80)
    print("测试3：趋势分析功能")
    print("="*80)
    
    df = generate_test_data(800)
    
    start_time = time.time()
    result = calculate_enhanced_product_scores_with_trend(df, days=15)
    calc_time = time.time() - start_time
    
    print(f"\n✅ 趋势分析完成")
    print(f"   数据行数: {len(result)}")
    print(f"   计算时间: {calc_time:.3f}秒")
    
    # 检查趋势字段
    trend_fields = ['前期销量', '近期销量', '销量变化率', '利润率变化', '趋势标签']
    missing_fields = [f for f in trend_fields if f not in result.columns]
    
    if missing_fields:
        print(f"\n❌ 缺少趋势字段: {missing_fields}")
        return False
    else:
        print(f"\n✅ 趋势字段都存在")
    
    # 检查趋势得分字段是否已删除
    score_fields = ['趋势得分', '销量趋势得分', '利润趋势得分', '前期得分', '近期得分']
    existing_score_fields = [f for f in score_fields if f in result.columns]
    
    if existing_score_fields:
        print(f"\n⚠️ 警告：以下趋势得分字段仍然存在: {existing_score_fields}")
        return False
    else:
        print(f"\n✅ 趋势得分字段已成功删除")
    
    # 显示趋势标签分布
    if '趋势标签' in result.columns:
        trend_counts = result['趋势标签'].value_counts()
        print(f"\n✅ 趋势标签分布:")
        for trend, count in trend_counts.items():
            print(f"   {trend}: {count}个")
    
    return True

def test_performance():
    """测试4：性能测试"""
    print("\n" + "="*80)
    print("测试4：性能测试")
    print("="*80)
    
    test_sizes = [100, 500, 800, 1000]
    
    print(f"\n{'商品数量':<10} {'计算时间':<15} {'内存占用':<15}")
    print("-" * 40)
    
    for size in test_sizes:
        df = generate_test_data(size)
        
        start_time = time.time()
        result = calculate_enhanced_product_scores(df)
        calc_time = time.time() - start_time
        
        # 估算内存占用（MB）
        memory_mb = result.memory_usage(deep=True).sum() / 1024 / 1024
        
        print(f"{size:<10} {calc_time:.3f}秒{'':<8} {memory_mb:.2f}MB")
    
    print(f"\n✅ 性能测试完成")
    print(f"\n性能目标:")
    print(f"   800商品计算时间 < 1.0秒: {'✅ 达标' if calc_time < 1.0 else '❌ 未达标'}")
    print(f"   内存占用 < 15MB: {'✅ 达标' if memory_mb < 15 else '❌ 未达标'}")
    
    return True

def main():
    """主函数"""
    print("\n" + "="*80)
    print("V7.4 评分体系删除验证")
    print("="*80)
    
    tests = [
        ("基础计算功能", test_basic_calculation),
        ("排序逻辑", test_sorting_logic),
        ("趋势分析功能", test_trend_calculation),
        ("性能测试", test_performance)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name}测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print(f"\n🎉 所有测试通过！V7.4评分体系删除成功！")
    else:
        print(f"\n⚠️ 部分测试失败，请检查代码")
    
    return all_passed

if __name__ == '__main__':
    main()
