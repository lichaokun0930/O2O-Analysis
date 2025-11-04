"""
问题诊断引擎 - 快速测试脚本

用于验证问题诊断引擎的各项功能是否正常
"""

import sys
from pathlib import Path

# 添加路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

print("=" * 60)
print("问题诊断引擎 - 功能测试")
print("=" * 60)

# 1. 测试模块导入
print("\n【步骤1】测试模块导入...")
try:
    from 问题诊断引擎 import ProblemDiagnosticEngine
    print("✅ 问题诊断引擎导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 2. 测试依赖库
print("\n【步骤2】测试依赖库...")
required_libs = {
    'pandas': 'pd',
    'numpy': 'np',
    'datetime': 'datetime'
}

for lib, alias in required_libs.items():
    try:
        exec(f"import {lib} as {alias}")
        print(f"  ✅ {lib} 可用")
    except ImportError:
        print(f"  ❌ {lib} 缺失")

# 3. 测试诊断引擎类
print("\n【步骤3】测试诊断引擎类...")
print("  可用方法:")
methods = [
    'diagnose_sales_decline',
    'diagnose_customer_price_decline',
    'diagnose_negative_margin_products',
    'diagnose_high_delivery_fee_orders',
    'diagnose_product_role_imbalance',
    'diagnose_abnormal_fluctuation',
    'generate_comprehensive_report'
]

for method in methods:
    if hasattr(ProblemDiagnosticEngine, method):
        print(f"    ✅ {method}()")
    else:
        print(f"    ❌ {method}() 缺失")

# 4. 创建模拟数据测试
print("\n【步骤4】创建模拟数据测试...")
try:
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # 生成模拟订单数据
    np.random.seed(42)
    n_orders = 500
    
    dates = [datetime.now() - timedelta(days=i) for i in range(30)]
    
    mock_data = pd.DataFrame({
        '订单ID': [f'ORD{i:05d}' for i in range(n_orders)],
        '三级分类名': np.random.choice(['商品A', '商品B', '商品C', '商品D', '商品E'], n_orders),
        '商品实售价': np.random.uniform(10, 100, n_orders),
        '商品采购成本': np.random.uniform(5, 80, n_orders),
        '日期': np.random.choice(dates, n_orders),
        '时段': np.random.choice(['上午(9-11点)', '下午(14-17点)', '晚间(21-24点)'], n_orders),
        '场景': np.random.choice(['早餐刚需', '日常补给', '正餐高峰', '休闲娱乐', '深夜应急'], n_orders),
        '商品角色': np.random.choice(['流量品', '利润品', '凑单品'], n_orders),
        '物流配送费': np.random.uniform(3, 15, n_orders),
        '平台佣金': np.random.uniform(1, 5, n_orders),
        '配送距离': np.random.uniform(0.5, 5.0, n_orders),
        '收货地址': np.random.choice(['地址A', '地址B', '地址C'], n_orders),
        '价格带': np.random.choice(['低价(0-20)', '中价(20-50)', '高价(50+)'], n_orders)
    })
    
    # 添加周列
    mock_data['周'] = mock_data['日期'].dt.isocalendar().week
    
    print(f"  ✅ 生成模拟数据: {len(mock_data)} 条订单")
    print(f"  📊 数据列: {', '.join(mock_data.columns.tolist())}")
    
except Exception as e:
    print(f"  ❌ 模拟数据生成失败: {e}")
    sys.exit(1)

# 5. 测试诊断引擎初始化
print("\n【步骤5】测试诊断引擎初始化...")
try:
    engine = ProblemDiagnosticEngine(mock_data)
    print("  ✅ 诊断引擎初始化成功")
except Exception as e:
    print(f"  ❌ 初始化失败: {e}")
    sys.exit(1)

# 6. 测试各项诊断功能
print("\n【步骤6】测试各项诊断功能...")

test_cases = [
    ('销量下滑诊断', lambda: engine.diagnose_sales_decline()),
    ('客单价归因分析', lambda: engine.diagnose_customer_price_decline()),
    ('负毛利预警', lambda: engine.diagnose_negative_margin_products()),
    ('高配送费诊断', lambda: engine.diagnose_high_delivery_fee_orders()),
    ('商品角色失衡', lambda: engine.diagnose_product_role_imbalance()),
    ('异常波动预警', lambda: engine.diagnose_abnormal_fluctuation())
]

for test_name, test_func in test_cases:
    try:
        result = test_func()
        if isinstance(result, pd.DataFrame):
            print(f"  ✅ {test_name}: 返回 {len(result)} 条结果")
        else:
            print(f"  ⚠️  {test_name}: 返回类型异常")
    except Exception as e:
        print(f"  ❌ {test_name}: {str(e)[:50]}...")

# 7. 测试综合报告生成
print("\n【步骤7】测试综合报告生成...")
try:
    report = engine.generate_comprehensive_report()
    print(f"  ✅ 综合报告生成成功")
    print(f"  📋 报告包含 {len(report)} 个诊断模块")
    
    if '诊断摘要' in report and len(report['诊断摘要']) > 0:
        print(f"\n  📊 诊断摘要:")
        print(report['诊断摘要'].to_string(index=False))
    
except Exception as e:
    print(f"  ❌ 报告生成失败: {e}")

# 测试完成
print("\n" + "=" * 60)
print("✅ 问题诊断引擎功能测试完成！")
print("=" * 60)
print("\n💡 下一步: 在 Streamlit 看板中测试实际数据")
print("   启动命令: streamlit run 智能门店经营看板_可视化.py --server.port 8502")
