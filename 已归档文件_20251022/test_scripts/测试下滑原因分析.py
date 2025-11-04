"""
测试下滑原因分析功能

验证:
1. 下滑原因分类逻辑是否准确
2. 显示格式是否清晰
3. 运营人员是否能根据原因采取行动
"""

import pandas as pd
from datetime import datetime, timedelta

# 导入问题诊断引擎
from 问题诊断引擎 import ProblemDiagnosisEngine

def test_declining_reason_analysis():
    """测试下滑原因分析"""
    print("=" * 80)
    print("【测试下滑原因分析功能】")
    print("=" * 80)
    
    # 创建测试数据
    base_date = datetime.now().date()
    
    # 构造测试数据：模拟不同下滑场景
    test_data = []
    
    # 场景1: 售罄（当前期销量=0）
    test_data.extend([
        {'日期': pd.Timestamp(base_date - timedelta(days=7)), '商品名称': '可口可乐', '商品实售价': 3.5, '数量': 100, '三级分类名': '饮料', '订单ID': f'O{i}'} 
        for i in range(100)
    ])
    # 当前期：无销量
    
    # 场景2: 涨价导致销量降（单价上涨>5% & 销量下降）
    test_data.extend([
        {'日期': pd.Timestamp(base_date - timedelta(days=7)), '商品名称': '雪碧', '商品实售价': 3.0, '数量': 80, '三级分类名': '饮料', '订单ID': f'O{100+i}'} 
        for i in range(80)
    ])
    test_data.extend([
        {'日期': pd.Timestamp(base_date), '商品名称': '雪碧', '商品实售价': 3.5, '数量': 50, '三级分类名': '饮料', '订单ID': f'O{200+i}'} 
        for i in range(50)
    ])
    
    # 场景3: 降价仍降量（单价下降>5% & 销量下降）
    test_data.extend([
        {'日期': pd.Timestamp(base_date - timedelta(days=7)), '商品名称': '芬达', '商品实售价': 4.0, '数量': 90, '三级分类名': '饮料', '订单ID': f'O{300+i}'} 
        for i in range(90)
    ])
    test_data.extend([
        {'日期': pd.Timestamp(base_date), '商品名称': '芬达', '商品实售价': 3.5, '数量': 60, '三级分类名': '饮料', '订单ID': f'O{400+i}'} 
        for i in range(60)
    ])
    
    # 场景4: 销量大幅下滑（销量下降>30%）
    test_data.extend([
        {'日期': pd.Timestamp(base_date - timedelta(days=7)), '商品名称': '百事可乐', '商品实售价': 3.5, '数量': 100, '三级分类名': '饮料', '订单ID': f'O{500+i}'} 
        for i in range(100)
    ])
    test_data.extend([
        {'日期': pd.Timestamp(base_date), '商品名称': '百事可乐', '商品实售价': 3.5, '数量': 50, '三级分类名': '饮料', '订单ID': f'O{600+i}'} 
        for i in range(50)
    ])
    
    # 场景5: 销量小幅下滑（销量下降<30%）
    test_data.extend([
        {'日期': pd.Timestamp(base_date - timedelta(days=7)), '商品名称': '红牛', '商品实售价': 6.0, '数量': 80, '三级分类名': '饮料', '订单ID': f'O{700+i}'} 
        for i in range(80)
    ])
    test_data.extend([
        {'日期': pd.Timestamp(base_date), '商品名称': '红牛', '商品实售价': 6.0, '数量': 60, '三级分类名': '饮料', '订单ID': f'O{800+i}'} 
        for i in range(60)
    ])
    
    # 转换为DataFrame
    df = pd.DataFrame(test_data)
    df['日期'] = pd.to_datetime(df['日期'])
    
    print(f"\n测试数据概览:")
    print(f"  总记录数: {len(df)}条")
    print(f"  日期范围: {df['日期'].min()} ~ {df['日期'].max()}")
    print(f"  商品数量: {df['商品名称'].nunique()}个")
    print(f"  商品列表: {df['商品名称'].unique().tolist()}")
    
    # 创建诊断引擎
    engine = ProblemDiagnosisEngine(df)
    
    # 分割两个周期的数据
    compare_date = base_date - timedelta(days=7)
    current_data = df[df['日期'].dt.date == base_date]
    compare_data = df[df['日期'].dt.date == compare_date]
    
    print(f"\n数据分割:")
    print(f"  当前期 ({base_date}): {len(current_data)}条")
    print(f"  对比期 ({compare_date}): {len(compare_data)}条")
    
    # 调用下滑原因分析方法
    print(f"\n调用下滑原因分析方法...")
    top_products = engine._get_top_declining_products_with_reason(
        current_data=current_data,
        compare_data=compare_data,
        top_n=5
    )
    
    print(f"\n下滑TOP商品分析结果:")
    print("=" * 80)
    if len(top_products) > 0:
        for i, product in enumerate(top_products, 1):
            print(f"  TOP{i}: {product}")
    else:
        print("  ❌ 无下滑商品")
    print("=" * 80)
    
    # 验证期望结果
    print(f"\n期望结果验证:")
    expected_reasons = {
        '可口可乐': '🔴售罄',
        '雪碧': '💰涨价导致销量降',
        '芬达': '💸降价仍降量',
        '百事可乐': '📉销量大幅下滑',
        '红牛': '📉销量小幅下滑'
    }
    
    for product_name, expected_reason in expected_reasons.items():
        matched = [p for p in top_products if product_name in p]
        if matched:
            product_str = matched[0]
            if expected_reason in product_str:
                print(f"  ✅ {product_name}: 原因判断正确 ({expected_reason})")
            else:
                print(f"  ❌ {product_name}: 原因判断错误")
                print(f"      期望: {expected_reason}")
                print(f"      实际: {product_str}")
        else:
            print(f"  ⚠️ {product_name}: 未出现在TOP列表中")
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)

if __name__ == "__main__":
    test_declining_reason_analysis()
