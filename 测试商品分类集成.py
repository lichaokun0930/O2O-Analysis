"""
快速测试商品分类分析模块集成
"""

print("=" * 60)
print("📦 测试商品分类分析模块集成")
print("=" * 60)
print()

# 测试1: 导入主看板模块
print("✅ 测试1: 导入主看板模块...")
try:
    import 多商品订单引导分析看板
    print("   ✓ 主看板模块导入成功")
except Exception as e:
    print(f"   ✗ 主看板模块导入失败: {e}")
    exit(1)

# 测试2: 导入商品分类分析模块
print("✅ 测试2: 导入商品分类分析模块...")
try:
    import 商品分类结构分析
    print("   ✓ 商品分类分析模块导入成功")
except Exception as e:
    print(f"   ✗ 商品分类分析模块导入失败: {e}")
    exit(1)

# 测试3: 检查函数存在
print("✅ 测试3: 检查核心函数...")
try:
    assert hasattr(商品分类结构分析, 'render_category_analysis')
    print("   ✓ render_category_analysis 函数存在")
    
    assert hasattr(商品分类结构分析, 'analyze_category_structure')
    print("   ✓ analyze_category_structure 函数存在")
    
    assert hasattr(商品分类结构分析, 'get_category_insights')
    print("   ✓ get_category_insights 函数存在")
    
except AssertionError as e:
    print(f"   ✗ 函数检查失败: {e}")
    exit(1)

# 测试4: 创建测试数据
print("✅ 测试4: 创建测试数据...")
try:
    import pandas as pd
    import numpy as np
    
    # 创建模拟数据
    test_data = {
        '订单ID': ['ORD001', 'ORD001', 'ORD002', 'ORD002', 'ORD003', 'ORD003', 'ORD004'],
        '商品名称': ['可乐', '薯片', '牛奶', '面包', '洗发水', '沐浴露', '苹果'],
        '商品实售价': [3.5, 5.8, 12.0, 4.5, 25.0, 18.0, 8.5],
        '一级分类': ['饮料', '零食', '乳制品', '面包', '个护', '个护', '水果'],
        '三级分类': ['碳酸饮料', '膨化食品', '鲜奶', '吐司', '洗发', '沐浴', '新鲜水果'],
        '商品成本': [2.0, 3.0, 8.0, 2.5, 15.0, 12.0, 5.0]
    }
    
    df_test = pd.DataFrame(test_data)
    print(f"   ✓ 测试数据创建成功（{len(df_test)}行）")
    
except Exception as e:
    print(f"   ✗ 测试数据创建失败: {e}")
    exit(1)

# 测试5: 运行分析函数
print("✅ 测试5: 运行分析函数...")
try:
    results = 商品分类结构分析.analyze_category_structure(df_test)
    
    assert 'level1' in results
    print(f"   ✓ 一级分类分析成功（{len(results['level1'])}个品类）")
    
    if 'hhi' in results:
        print(f"   ✓ HHI指数计算成功: {results['hhi']:.3f}")
    
    if 'contribution_matrix' in results:
        print(f"   ✓ 贡献度矩阵生成成功")
    
    if 'cross_category' in results:
        print(f"   ✓ 跨品类分析成功（{len(results['cross_category'])}个组合）")
    
except Exception as e:
    print(f"   ✗ 分析函数运行失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 测试6: 运行智能洞察
print("✅ 测试6: 生成智能洞察...")
try:
    insights = 商品分类结构分析.get_category_insights(results)
    
    assert len(insights) > 0
    print(f"   ✓ 智能洞察生成成功（{len(insights)}条）")
    
    for i, insight in enumerate(insights[:3], 1):
        print(f"      {i}. {insight}")
    
except Exception as e:
    print(f"   ✗ 智能洞察生成失败: {e}")
    exit(1)

print()
print("=" * 60)
print("🎉 所有测试通过！商品分类分析模块集成成功！")
print("=" * 60)
print()
print("📋 下一步:")
print("1. 运行看板: .\\启动多商品分析看板.ps1")
print("2. 上传数据文件（需包含'一级分类'字段）")
print("3. 在'商品分类结构竞争力'Tab查看分析结果")
print()
print("📚 详细文档: 商品分类分析功能说明.md")
print()
