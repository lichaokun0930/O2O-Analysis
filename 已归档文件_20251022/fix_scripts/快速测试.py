# -*- coding: utf-8 -*-
"""
智能门店经营看板系统 - 快速测试
检查系统基本功能是否正常
"""

import os
import sys
import pandas as pd

print("🚀 智能门店经营看板系统 - 快速测试")
print("=" * 50)

# 1. 检查数据文件
print("\n📁 1. 检查数据文件...")
data_file = "实际数据/测试数据-近30天数据.xlsx"

if os.path.exists(data_file):
    print("✅ 数据文件存在")
    try:
        excel_file = pd.ExcelFile(data_file)
        print(f"📊 包含sheets: {excel_file.sheet_names}")
        
        # 检查每个sheet的数据量
        for sheet in excel_file.sheet_names:
            df = pd.read_excel(data_file, sheet_name=sheet)
            print(f"  - {sheet}: {len(df):,}条记录")
        
    except Exception as e:
        print(f"❌ 数据文件读取失败: {e}")
else:
    print(f"❌ 数据文件不存在: {data_file}")

# 2. 检查核心模块
print("\n🔧 2. 检查核心模块...")

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from 核心业务逻辑 import process_order_data
    print("✅ 核心业务逻辑模块导入成功")
    
    # 测试数据处理
    if os.path.exists(data_file):
        order_data = pd.read_excel(data_file, sheet_name='门店订单数据')
        cleaned_data, order_summary, business_metrics = process_order_data(order_data)
        print(f"✅ 数据处理测试成功:")
        print(f"  - 原始数据: {len(order_data):,}条")
        print(f"  - 清洗后: {len(cleaned_data):,}条")
        print(f"  - 订单数: {len(order_summary):,}个")
        
        # 显示关键指标
        cost_structure = business_metrics.get('cost_structure', {})
        print(f"  - 真实成本率: {cost_structure.get('平均真实成本率', 0):.1%}")
        
except Exception as e:
    print(f"❌ 核心业务逻辑测试失败: {e}")

# 3. 检查智能看板系统
print("\n🧠 3. 检查智能看板系统...")

try:
    from 智能门店经营看板系统 import SmartStoreDashboard
    print("✅ 智能看板系统导入成功")
    
    # 初始化系统
    dashboard = SmartStoreDashboard()
    print("✅ 系统初始化成功")
    
    # 检查五大模型
    models = [
        ('假设验证模型', hasattr(dashboard, 'hypothesis_engine')),
        ('预测分析模型', hasattr(dashboard, 'prediction_engine')),
        ('决策建议模型', hasattr(dashboard, 'decision_engine')),
        ('风险评估模型', hasattr(dashboard, 'risk_engine')),
        ('数据经营模型', hasattr(dashboard, 'operation_engine'))
    ]
    
    print("🔍 五大核心模型检查:")
    for model_name, available in models:
        status = "✅" if available else "❌"
        print(f"  {status} {model_name}")
    
except Exception as e:
    print(f"❌ 智能看板系统测试失败: {e}")

# 4. 检查竞对分析
print("\n🕵️ 4. 检查竞对分析模块...")

try:
    from 竞对商业情报倒推分析器 import CompetitorIntelligenceAnalyzer
    print("✅ 竞对分析模块导入成功")
    
    if os.path.exists(data_file):
        analyzer = CompetitorIntelligenceAnalyzer()
        if analyzer.load_data(data_file):
            print("✅ 竞对数据加载成功")
        else:
            print("❌ 竞对数据加载失败")
    
except Exception as e:
    print(f"❌ 竞对分析测试失败: {e}")

# 5. 检查可视化界面
print("\n🎨 5. 检查可视化界面...")

visual_file = "智能门店经营看板_可视化.py"
if os.path.exists(visual_file):
    print("✅ 可视化界面文件存在")
    
    try:
        import streamlit
        import plotly
        print("✅ 可视化依赖包可用")
        print("💡 启动命令: streamlit run 智能门店经营看板_可视化.py")
    except ImportError as e:
        print(f"⚠️ 可视化依赖缺失: {e}")
        print("💡 安装命令: pip install streamlit plotly")
else:
    print(f"❌ 可视化文件不存在: {visual_file}")

print("\n" + "=" * 50)
print("🎯 快速测试完成")
print("💡 如果所有模块都显示 ✅，系统就可以正常使用了！")
print("🚀 启动可视化界面: streamlit run 智能门店经营看板_可视化.py")
print("=" * 50)