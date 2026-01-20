"""
测试客户流失分析缓存优化

测试内容:
1. 首次调用 - 验证缓存未命中，正常计算
2. 二次调用 - 验证缓存命中，快速返回
3. 性能对比 - 对比缓存前后的性能提升

作者: Kiro AI
创建日期: 2025-12-11
"""

import pandas as pd
import time
from datetime import datetime, timedelta
from components.today_must_do.customer_churn_analyzer import (
    identify_churn_customers,
    analyze_churn_reasons
)

def create_test_data(num_rows=1000):
    """创建测试数据"""
    print(f"\n📊 创建测试数据（{num_rows}行）...")
    
    # 生成测试订单数据
    dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
    
    data = []
    for i in range(num_rows):
        data.append({
            '订单ID': f'ORDER_{i:06d}',
            '下单时间': dates[i % len(dates)],
            '收货地址': f'北京市朝阳区测试路{i % 100}号{i % 10}单元{i % 20}01',
            '商品名称': f'测试商品{i % 50}',
            '商品实售价': 10 + (i % 100) * 0.5,
            '门店名称': '测试门店A',
            '预计订单收入': 10 + (i % 100) * 0.5
        })
    
    df = pd.DataFrame(data)
    print(f"✅ 测试数据创建完成: {len(df)}行")
    return df

def create_test_products():
    """创建测试商品数据"""
    products = []
    for i in range(50):
        products.append({
            'product_name': f'测试商品{i}',
            'stock': 100 if i % 3 != 0 else 0,  # 1/3的商品缺货
            'price': 10 + i * 0.5
        })
    
    return pd.DataFrame(products)

def test_identify_churn_customers():
    """测试客户流失识别缓存"""
    print("\n" + "="*60)
    print("测试1: identify_churn_customers 缓存")
    print("="*60)
    
    # 创建测试数据
    df = create_test_data(num_rows=5000)
    
    # 首次调用（缓存未命中）
    print("\n🔍 首次调用（预期：缓存未命中）...")
    start_time = time.time()
    result1 = identify_churn_customers(df, lookback_days=30, min_orders=2, no_order_days=7)
    time1 = time.time() - start_time
    print(f"⏱️ 首次调用耗时: {time1:.2f}秒")
    print(f"📊 识别到 {len(result1)} 个流失客户")
    
    # 二次调用（缓存命中）
    print("\n🔍 二次调用（预期：缓存命中）...")
    start_time = time.time()
    result2 = identify_churn_customers(df, lookback_days=30, min_orders=2, no_order_days=7)
    time2 = time.time() - start_time
    print(f"⏱️ 二次调用耗时: {time2:.2f}秒")
    print(f"📊 识别到 {len(result2)} 个流失客户")
    
    # 性能对比
    print("\n📈 性能对比:")
    print(f"   首次调用: {time1:.2f}秒")
    print(f"   二次调用: {time2:.2f}秒")
    if time1 > 0:
        speedup = time1 / time2
        improvement = (1 - time2/time1) * 100
        print(f"   加速比: {speedup:.1f}x")
        print(f"   性能提升: {improvement:.1f}%")
    
    # 验证结果一致性
    print("\n🔍 验证结果一致性:")
    if len(result1) == len(result2):
        print(f"   ✅ 流失客户数量一致: {len(result1)}")
    else:
        print(f"   ❌ 流失客户数量不一致: {len(result1)} vs {len(result2)}")
    
    # 验证数据内容
    if not result1.empty and not result2.empty:
        # 比较第一个客户的数据
        customer1 = result1.iloc[0]
        customer2 = result2.iloc[0]
        
        if customer1['customer_id'] == customer2['customer_id']:
            print(f"   ✅ 客户ID一致: {customer1['customer_id'][:30]}...")
        else:
            print(f"   ❌ 客户ID不一致")
        
        if abs(customer1['ltv'] - customer2['ltv']) < 0.01:
            print(f"   ✅ LTV一致: {customer1['ltv']:.2f}")
        else:
            print(f"   ❌ LTV不一致: {customer1['ltv']:.2f} vs {customer2['ltv']:.2f}")
    
    return time1, time2

def test_analyze_churn_reasons():
    """测试客户流失原因分析缓存"""
    print("\n" + "="*60)
    print("测试2: analyze_churn_reasons 缓存")
    print("="*60)
    
    # 创建测试数据
    df = create_test_data(num_rows=5000)
    products_df = create_test_products()
    
    # 先识别流失客户
    print("\n🔍 识别流失客户...")
    churn_customers = identify_churn_customers(df, lookback_days=30, min_orders=2, no_order_days=7)
    print(f"📊 识别到 {len(churn_customers)} 个流失客户")
    
    if churn_customers.empty:
        print("⚠️ 没有流失客户，跳过原因分析测试")
        return 0, 0
    
    # 首次调用（缓存未命中）
    print("\n🔍 首次分析流失原因（预期：缓存未命中）...")
    start_time = time.time()
    result1 = analyze_churn_reasons(df, products_df, churn_customers)
    time1 = time.time() - start_time
    print(f"⏱️ 首次调用耗时: {time1:.2f}秒")
    print(f"📊 分析结果:")
    print(f"   总流失人数: {result1['summary']['total_churn']}")
    print(f"   缺货影响: {result1['summary']['out_of_stock']}")
    print(f"   涨价影响: {result1['summary']['price_increased']}")
    print(f"   下架影响: {result1['summary']['delisted']}")
    print(f"   其他原因: {result1['summary']['unknown']}")
    
    # 二次调用（缓存命中）
    print("\n🔍 二次分析流失原因（预期：缓存命中）...")
    start_time = time.time()
    result2 = analyze_churn_reasons(df, products_df, churn_customers)
    time2 = time.time() - start_time
    print(f"⏱️ 二次调用耗时: {time2:.2f}秒")
    print(f"📊 分析结果:")
    print(f"   总流失人数: {result2['summary']['total_churn']}")
    print(f"   缺货影响: {result2['summary']['out_of_stock']}")
    print(f"   涨价影响: {result2['summary']['price_increased']}")
    print(f"   下架影响: {result2['summary']['delisted']}")
    print(f"   其他原因: {result2['summary']['unknown']}")
    
    # 性能对比
    print("\n📈 性能对比:")
    print(f"   首次调用: {time1:.2f}秒")
    print(f"   二次调用: {time2:.2f}秒")
    if time1 > 0:
        speedup = time1 / time2
        improvement = (1 - time2/time1) * 100
        print(f"   加速比: {speedup:.1f}x")
        print(f"   性能提升: {improvement:.1f}%")
    
    # 验证结果一致性
    print("\n🔍 验证结果一致性:")
    if result1['summary'] == result2['summary']:
        print(f"   ✅ 统计结果一致")
    else:
        print(f"   ❌ 统计结果不一致")
    
    return time1, time2

def test_cache_invalidation():
    """测试缓存失效机制"""
    print("\n" + "="*60)
    print("测试3: 缓存失效机制")
    print("="*60)
    
    # 创建测试数据
    df1 = create_test_data(num_rows=1000)
    
    # 首次调用
    print("\n🔍 首次调用（数据集1，1000行）...")
    start_time = time.time()
    result1 = identify_churn_customers(df1)
    time1 = time.time() - start_time
    print(f"⏱️ 耗时: {time1:.2f}秒")
    print(f"📊 流失客户: {len(result1)}")
    
    # 二次调用（相同数据，应该缓存命中）
    print("\n🔍 二次调用（相同数据，预期：缓存命中）...")
    start_time = time.time()
    result2 = identify_churn_customers(df1)
    time2 = time.time() - start_time
    print(f"⏱️ 耗时: {time2:.2f}秒")
    print(f"📊 流失客户: {len(result2)}")
    
    # 三次调用（不同数据量，应该缓存未命中）
    df2 = create_test_data(num_rows=2000)
    print("\n🔍 三次调用（数据集2，2000行，预期：缓存未命中）...")
    start_time = time.time()
    result3 = identify_churn_customers(df2)
    time3 = time.time() - start_time
    print(f"⏱️ 耗时: {time3:.2f}秒")
    print(f"📊 流失客户: {len(result3)}")
    
    # 验证缓存失效
    print("\n🔍 验证缓存失效:")
    if time2 < time1 * 0.5:
        print(f"   ✅ 相同数据缓存命中（{time2:.2f}秒 < {time1*0.5:.2f}秒）")
    else:
        print(f"   ⚠️ 相同数据可能未命中缓存（{time2:.2f}秒 >= {time1*0.5:.2f}秒）")
    
    if time3 > time2 * 2:
        print(f"   ✅ 不同数据缓存失效（{time3:.2f}秒 > {time2*2:.2f}秒）")
    else:
        print(f"   ⚠️ 不同数据可能命中了缓存（{time3:.2f}秒 <= {time2*2:.2f}秒）")

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🧪 客户流失分析缓存优化测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 测试1: identify_churn_customers
        time1_1, time1_2 = test_identify_churn_customers()
        
        # 测试2: analyze_churn_reasons
        time2_1, time2_2 = test_analyze_churn_reasons()
        
        # 测试3: 缓存失效机制
        test_cache_invalidation()
        
        # 总结
        print("\n" + "="*60)
        print("📊 测试总结")
        print("="*60)
        
        print("\n✅ 所有测试完成！")
        print("\n性能提升汇总:")
        if time1_1 > 0 and time1_2 > 0:
            improvement1 = (1 - time1_2/time1_1) * 100
            print(f"   identify_churn_customers: {improvement1:.1f}% 提升")
        if time2_1 > 0 and time2_2 > 0:
            improvement2 = (1 - time2_2/time2_1) * 100
            print(f"   analyze_churn_reasons: {improvement2:.1f}% 提升")
        
        print("\n💡 建议:")
        print("   1. 在调试模式下启动看板，观察实际缓存效果")
        print("   2. 查看日志中的'缓存命中'/'缓存未命中'信息")
        print("   3. 监控经营诊断的加载时间变化")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
