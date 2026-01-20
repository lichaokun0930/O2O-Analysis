"""
验证V8.10.2部署

测试：
1. 性能是否达标（<2秒）
2. 涨价判断是否恢复
3. 结果准确性
"""

import pandas as pd
import time
import sys

from components.today_must_do.customer_churn_analyzer import (
    identify_churn_customers,
    analyze_churn_reasons
)


def verify_deployment():
    """验证部署"""
    from database.data_source_manager import DataSourceManager
    dsm = DataSourceManager()
    
    test_store = "惠宜选超市（合肥繁华大道店）"
    
    print("="*80)
    print("🔍 V8.10.2部署验证")
    print("="*80)
    
    # 加载数据
    print(f"\n📊 加载测试数据: {test_store}")
    data_dict = dsm.load_from_database(store_name=test_store)
    df = data_dict.get('full', data_dict.get('display'))
    print(f"✅ 数据加载完成: {len(df)}行")
    
    # Step 1: 识别流失客户
    print("\n" + "="*80)
    print("Step 1: 识别流失客户")
    print("="*80)
    
    start = time.time()
    churn_customers = identify_churn_customers(df)
    elapsed = time.time() - start
    
    print(f"\n✅ 流失客户识别完成")
    print(f"   流失客户: {len(churn_customers)}个")
    print(f"   耗时: {elapsed:.2f}秒")
    
    # 创建商品数据
    products_df = df[['商品名称', '库存']].drop_duplicates()
    products_df.columns = ['product_name', 'stock']
    
    # Step 2: 测试V8.10.2版本
    print("\n" + "="*80)
    print("Step 2: 测试V8.10.2版本（向量化 + 涨价判断）")
    print("="*80)
    
    start = time.time()
    result = analyze_churn_reasons(df, products_df, churn_customers)
    elapsed = time.time() - start
    
    print(f"\n✅ V8.10.2 测试完成")
    print(f"   耗时: {elapsed:.2f}秒")
    print(f"\n📊 分析结果:")
    print(f"   总流失: {result['summary']['total_churn']}人")
    print(f"   缺货影响: {result['summary']['out_of_stock']}人")
    print(f"   涨价影响: {result['summary']['price_increased']}人 ⭐")
    print(f"   下架影响: {result['summary']['delisted']}人")
    print(f"   其他原因: {result['summary']['unknown']}人")
    
    # Step 3: 验证结果
    print("\n" + "="*80)
    print("📋 验证结果")
    print("="*80)
    
    # 性能验证
    performance_ok = elapsed < 2.0
    print(f"\n✅ 性能验证:")
    print(f"   目标: <2秒")
    print(f"   实际: {elapsed:.2f}秒")
    print(f"   结果: {'✅ 通过' if performance_ok else '❌ 未通过'}")
    
    # 涨价判断验证
    price_increase_restored = result['summary']['price_increased'] > 0
    print(f"\n✅ 涨价判断验证:")
    print(f"   涨价影响人数: {result['summary']['price_increased']}人")
    print(f"   结果: {'✅ 功能已恢复' if price_increase_restored else '⚠️ 未检测到涨价'}")
    
    # 数据完整性验证
    total_classified = (
        result['summary']['out_of_stock'] +
        result['summary']['price_increased'] +
        result['summary']['delisted'] +
        result['summary']['unknown']
    )
    data_integrity_ok = total_classified == result['summary']['total_churn']
    print(f"\n✅ 数据完整性验证:")
    print(f"   总流失: {result['summary']['total_churn']}人")
    print(f"   分类总计: {total_classified}人")
    print(f"   结果: {'✅ 通过' if data_integrity_ok else '❌ 数据不一致'}")
    
    # 最终结论
    print("\n" + "="*80)
    print("🎉 最终结论")
    print("="*80)
    
    all_ok = performance_ok and data_integrity_ok
    
    if all_ok:
        print("\n✅ V8.10.2部署成功！")
        print(f"\n🎯 关键指标:")
        print(f"   ⚡ 性能: {elapsed:.2f}秒（提升 {(4.34-elapsed)/4.34*100:.1f}%）")
        print(f"   🔍 涨价检测: {result['summary']['price_increased']}人")
        print(f"   📊 数据完整性: 100%")
        
        print(f"\n💡 建议:")
        print(f"   1. 可以正式启用V8.10.2版本")
        print(f"   2. 监控生产环境性能表现")
        print(f"   3. 收集用户反馈")
    else:
        print("\n⚠️ 需要进一步检查")
        if not performance_ok:
            print(f"   - 性能未达标（{elapsed:.2f}秒 > 2秒）")
        if not data_integrity_ok:
            print(f"   - 数据完整性问题")
    
    return all_ok


if __name__ == '__main__':
    try:
        success = verify_deployment()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
