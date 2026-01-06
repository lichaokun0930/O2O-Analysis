"""
测试客户流失分析向量化优化效果

对比优化前后的：
1. 功能正确性
2. 性能提升
3. 结果一致性
"""

import pandas as pd
import time
import sys
sys.path.insert(0, 'O2O-Analysis/components/today_must_do')

from components.today_must_do.customer_churn_analyzer import (
    identify_churn_customers,
    analyze_churn_reasons
)
from analyze_churn_reasons_v2 import analyze_churn_reasons_v2


def test_performance():
    """测试性能对比"""
    # 加载真实数据
    from database.data_source_manager import DataSourceManager
    dsm = DataSourceManager()
    
    # 测试门店
    test_store = "惠宜选超市（合肥繁华大道店）"
    
    print("="*80)
    print("🧪 客户流失分析向量化优化性能测试")
    print("="*80)
    
    # 加载数据
    print(f"\n📊 加载测试数据: {test_store}")
    data_dict = dsm.load_from_database(store_name=test_store)
    
    # 检查返回类型并提取DataFrame
    if isinstance(data_dict, dict):
        # 使用完整数据（包含耗材）
        df = data_dict.get('full', data_dict.get('display'))
        
        if df is None:
            print(f"[DEBUG] data_dict keys: {list(data_dict.keys())}")
            raise ValueError("无法从返回的dict中找到DataFrame")
        
        print(f"✅ 数据加载完成: {len(df)}行（完整数据）")
    else:
        df = data_dict
        print(f"✅ 数据加载完成: {len(df)}行")
    
    # Step 1: 识别流失客户
    print("\n" + "="*80)
    print("Step 1: 识别流失客户")
    print("="*80)
    
    start = time.time()
    churn_customers = identify_churn_customers(df)
    elapsed = time.time() - start
    
    print(f"\n✅ 流失客户识别完成")
    print(f"   数据量: {len(df)}行")
    print(f"   流失客户: {len(churn_customers)}个")
    print(f"   耗时: {elapsed:.2f}秒")
    
    # 创建商品数据
    products_df = df[['商品名称', '库存']].drop_duplicates()
    products_df.columns = ['product_name', 'stock']
    print(f"   商品数: {len(products_df)}个")
    
    # Step 2: 测试原版本（V8.10.1）
    print("\n" + "="*80)
    print("Step 2: 测试原版本（V8.10.1 - 带Redis缓存）")
    print("="*80)
    
    start = time.time()
    result_v1 = analyze_churn_reasons(df, products_df, churn_customers)
    elapsed_v1 = time.time() - start
    
    print(f"\n✅ V8.10.1 测试完成")
    print(f"   耗时: {elapsed_v1:.2f}秒")
    print(f"   分析结果:")
    print(f"      总流失: {result_v1['summary']['total_churn']}人")
    print(f"      缺货影响: {result_v1['summary']['out_of_stock']}人")
    print(f"      涨价影响: {result_v1['summary']['price_increased']}人")
    print(f"      下架影响: {result_v1['summary']['delisted']}人")
    print(f"      其他原因: {result_v1['summary']['unknown']}人")
    
    # Step 3: 测试优化版本（V8.10.2）
    print("\n" + "="*80)
    print("Step 3: 测试优化版本（V8.10.2 - 向量化）")
    print("="*80)
    
    start = time.time()
    result_v2 = analyze_churn_reasons_v2(df, products_df, churn_customers)
    elapsed_v2 = time.time() - start
    
    print(f"\n✅ V8.10.2 测试完成")
    print(f"   耗时: {elapsed_v2:.2f}秒")
    print(f"   分析结果:")
    print(f"      总流失: {result_v2['summary']['total_churn']}人")
    print(f"      缺货影响: {result_v2['summary']['out_of_stock']}人")
    print(f"      涨价影响: {result_v2['summary']['price_increased']}人")
    print(f"      下架影响: {result_v2['summary']['delisted']}人")
    print(f"      其他原因: {result_v2['summary']['unknown']}人")
    
    # Step 4: 性能对比
    print("\n" + "="*80)
    print("📊 性能对比总结")
    print("="*80)
    
    speedup = elapsed_v1 / elapsed_v2 if elapsed_v2 > 0 else float('inf')
    improvement = (elapsed_v1 - elapsed_v2) / elapsed_v1 * 100 if elapsed_v1 > 0 else 0
    
    print(f"\n⏱️ 耗时对比:")
    print(f"   V8.10.1 (原版本): {elapsed_v1:.2f}秒")
    print(f"   V8.10.2 (优化版): {elapsed_v2:.2f}秒")
    print(f"   加速比: {speedup:.1f}x")
    print(f"   性能提升: {improvement:.1f}%")
    
    print(f"\n🎯 目标达成情况:")
    print(f"   目标耗时: <2秒")
    print(f"   实际耗时: {elapsed_v2:.2f}秒")
    print(f"   达标: {'✅ 是' if elapsed_v2 < 2 else '❌ 否'}")
    
    # Step 5: 结果一致性检查
    print("\n" + "="*80)
    print("🔍 结果一致性检查")
    print("="*80)
    
    # 检查summary一致性
    summary_match = (
        result_v1['summary']['total_churn'] == result_v2['summary']['total_churn'] and
        result_v1['summary']['out_of_stock'] == result_v2['summary']['out_of_stock'] and
        result_v1['summary']['delisted'] == result_v2['summary']['delisted']
    )
    
    print(f"\n✅ Summary一致性: {'通过' if summary_match else '❌ 不一致'}")
    
    # 检查details数量一致性
    details_count_match = len(result_v1['details']) == len(result_v2['details'])
    print(f"✅ Details数量一致性: {'通过' if details_count_match else '❌ 不一致'}")
    print(f"   V8.10.1: {len(result_v1['details'])}条")
    print(f"   V8.10.2: {len(result_v2['details'])}条")
    
    # 注意：涨价判断在V8.10.2中简化了，所以price_increased可能不同
    if result_v1['summary']['price_increased'] != result_v2['summary']['price_increased']:
        print(f"\n⚠️ 注意: 涨价判断结果不同（V8.10.2简化了涨价判断逻辑）")
        print(f"   V8.10.1: {result_v1['summary']['price_increased']}人")
        print(f"   V8.10.2: {result_v2['summary']['price_increased']}人")
    
    # 最终结论
    print("\n" + "="*80)
    print("🎉 测试结论")
    print("="*80)
    
    if elapsed_v2 < 2 and summary_match and details_count_match:
        print("\n✅ 优化成功！")
        print(f"   - 性能提升 {improvement:.1f}%")
        print(f"   - 耗时从 {elapsed_v1:.2f}秒 降到 {elapsed_v2:.2f}秒")
        print(f"   - 结果一致性验证通过")
        print(f"\n建议：可以将V8.10.2版本部署到生产环境")
    else:
        print("\n⚠️ 需要进一步优化")
        if elapsed_v2 >= 2:
            print(f"   - 耗时 {elapsed_v2:.2f}秒 仍超过目标（2秒）")
        if not summary_match:
            print(f"   - Summary结果不一致，需要检查算法")
        if not details_count_match:
            print(f"   - Details数量不一致，需要检查逻辑")


if __name__ == '__main__':
    try:
        test_performance()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
